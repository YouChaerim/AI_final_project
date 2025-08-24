# server/study_sessions.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from bson import ObjectId
from datetime import datetime
import pytz
from datetime import datetime, timedelta, timezone
from bson import ObjectId

from .server_db import db

router = APIRouter(prefix="/study", tags=["Study Sessions"])
KST = pytz.timezone("Asia/Seoul")


# ---------------------------
# Pydantic Models
# ---------------------------
class SessionStartResp(BaseModel):
    session_id: str

class SessionFinishBody(BaseModel):
    # 프론트에서 집계해서 주는 값 (없으면 None 허용)
    focus_score: Optional[float] = None         # 세션 평균 집중도
    yawn_count: Optional[int] = None            # 하품 횟수(=yawn_end 개수)
    avg_yawn: Optional[float] = None            # 하품 인식 가중치 평균
    sum_study_time: Optional[float] = None      # 누적 공부 시간(초)

class YawnEvent(BaseModel):
    type: Literal["start", "yawn_end"]
    timestamp: str                               # "YYYY-MM-DD HH:MM:SS" (로컬/KST)
    avg_yawn_duration: Optional[float] = None    # yawn_end일 때만
    attention_score: Optional[float] = None      # yawn_end일 때만

class SleepEvent(BaseModel):
    type: Literal["start", "drowys_end"]         # 타이포 포함 그대로 반영
    timestamp: str
    attention_score: Optional[float] = None      # end일 때만

class EventBatchBody(BaseModel):
    yawn_events: List[YawnEvent] = Field(default_factory=list)
    sleep_events: List[SleepEvent] = Field(default_factory=list)

class BreakStartBody(BaseModel):
    reason: Literal["focus_drop", "manual", "pomodoro"] = "manual"
    focus_score: Optional[float] = None

class BreakStartResp(BaseModel):
    break_id: str

class BreakEndBody(BaseModel):
    break_id: Optional[str] = None               # 없으면 "미종료인 최신 break" 자동 종료
    focus_score: Optional[float] = None          # 휴식 평균 집중도(있으면 업데이트)


# ---------------------------
# Helpers
# ---------------------------
def _oid(s: str) -> ObjectId:
    try:
        return ObjectId(s)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ObjectId")

def _parse_kst(ts_str: str) -> datetime:
    """
    "YYYY-MM-DD HH:MM:SS" 포맷 문자열을 KST aware datetime으로 변환
    """
    try:
        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        return KST.localize(dt)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid timestamp: {ts_str}")

def _ensure_indexes():
    db.sessions.create_index([("user_id", 1), ("study_date", 1)])
    db.breaks.create_index([("session_id", 1), ("start_time", 1)])
    db.session_events.create_index([("session_id", 1), ("timestamp", 1)])
    db.points.create_index([("user_id", 1), ("gain_date", 1)])
    try:
        db.points.create_index([("user_id", 1), ("reason", 1)], unique=True)
    except Exception:
        pass
_ensure_indexes()


# ---------------------------
# Session Start / Finish
# ---------------------------
@router.post("/sessions/start/{user_id}", response_model=SessionStartResp)
def start_session(user_id: str):
    """
    main.py 진입시 호출 → 세션 생성
    """
    user_obj = _oid(user_id)
    now = datetime.now(KST)

    open_sessions = list(db.sessions.find({"user_id": user_obj, "end_time": None}, {"_id": 1}))
    if open_sessions:
        open_ids = [s["_id"] for s in open_sessions]
        db.sessions.update_many({"_id": {"$in": open_ids}}, {"$set": {"end_time": now}})
        # 1-1) 해당 세션들의 미종료 휴식도 함께 종료
        db.breaks.update_many({"session_id": {"$in": open_ids}, "end_time": None}, {"$set": {"end_time": now}})

    doc = {
        "user_id": user_obj,
        "study_date": now,         # 시작 시간
        "end_time": None,          # 종료 시 업데이트
        "focus_score": None,       # 종료 시 집계
        "yawn_count": None,
        "avg_yawn": None,
        "sum_study_time": 0.0,
    }
    inserted = db.sessions.insert_one(doc)
    return {"session_id": str(inserted.inserted_id)}


@router.post("/sessions/finish/{user_id}/{session_id}")
def finish_session(user_id: str, session_id: str, body: SessionFinishBody):
    """
    페이지 이탈 혹은 '스탑' 버튼 시 호출 → 세션 종료/집계 저장
    """
    user_obj = _oid(user_id)
    sess_obj = _oid(session_id)

    ses = db.sessions.find_one({"_id": sess_obj, "user_id": user_obj})
    if not ses:
        raise HTTPException(status_code=404, detail="Session not found")

    update = {
        "end_time": datetime.now(KST),
    }
    # 전달된 값만 반영 (None은 무시)
    for k in ["focus_score", "yawn_count", "avg_yawn", "sum_study_time"]:
        v = getattr(body, k)
        if v is not None:
            update[k] = v

    db.sessions.update_one({"_id": sess_obj}, {"$set": update})
    ses = db.sessions.find_one({"_id": sess_obj})
    added = award_all_points_on_finish(db, ses)

    return {"status": "success", "points_added": int(added)}


# ---------------------------
# Event Batch (yawn/sleep)
# ---------------------------
@router.post("/sessions/{session_id}/events/batch")
def save_event_batch(session_id: str, body: EventBatchBody):
    """
    현재 로컬 JSON에 쌓아둔 하품/졸음 이벤트들을 한꺼번에 DB에 적재
    """
    sess_obj = _oid(session_id)
    # 세션 존재 체크 (없으면 404)
    if not db.sessions.find_one({"_id": sess_obj}):
        raise HTTPException(status_code=404, detail="Session not found")

    docs = []
    # yawn events
    for ev in body.yawn_events:
        docs.append({
            "session_id": sess_obj,
            "timestamp": _parse_kst(ev.timestamp),
            "event_type": "yawn_start" if ev.type == "start" else "yawn_end",
            "attention": ev.attention_score if ev.type == "yawn_end" else None,
            "yawn_weight": ev.avg_yawn_duration if ev.type == "yawn_end" else None,
        })
    # sleep events
    for ev in body.sleep_events:
        docs.append({
            "session_id": sess_obj,
            "timestamp": _parse_kst(ev.timestamp),
            "event_type": "sleep_start" if ev.type == "start" else "sleep_end",  # drowys_end → sleep_end 맵핑
            "attention": ev.attention_score if ev.type != "start" else None,
            "yawn_weight": None,
        })

    if docs:
        db.session_events.insert_many(docs)

    return {"status": "success", "inserted": len(docs)}


# ---------------------------
# Breaks (start/end)
# ---------------------------
@router.post("/sessions/{session_id}/breaks/start", response_model=BreakStartResp)
def start_break(session_id: str, body: BreakStartBody):
    """
    휴식 시작. 미종료 break가 이미 있으면 409 반환.
    """
    sess_obj = _oid(session_id)

    # 미종료 break가 존재하는지 방어
    open_break = db.breaks.find_one({"session_id": sess_obj, "end_time": None})
    if open_break:
        return {"break_id": str(open_break["_id"])}

    doc = {
        "session_id": sess_obj,
        "start_time": datetime.now(KST),
        "end_time": None,
        "reason": body.reason,
        "focus_score": body.focus_score,
    }
    ins = db.breaks.insert_one(doc)
    return {"break_id": str(ins.inserted_id)}


@router.post("/sessions/{session_id}/breaks/end")
def end_break(session_id: str, body: BreakEndBody):
    """
    휴식 종료. break_id가 없으면 가장 최근 미종료 break를 찾아 종료한다.
    """
    sess_obj = _oid(session_id)

    if body.break_id:
        br_obj = _oid(body.break_id)
        q = {"_id": br_obj, "session_id": sess_obj, "end_time": None}
    else:
        q = {"session_id": sess_obj, "end_time": None}
    br = db.breaks.find_one(q)
    if not br:
        raise HTTPException(status_code=404, detail="Open break not found")

    update = {"end_time": datetime.now(KST)}
    if body.focus_score is not None:
        update["focus_score"] = body.focus_score

    db.breaks.update_one({"_id": br["_id"]}, {"$set": update})
    return {"status": "success"}

@router.get("/users/{user_id}/yawn-weight")
def get_user_yawn_weight(user_id: str):
    try:
        uid = ObjectId(user_id)
    except Exception:
        raise HTTPException(400, "Invalid user id")

    doc = db.sessions.find_one(
        {"user_id": uid, "avg_yawn": {"$gt": 0}},
        sort=[("end_time", -1)]  # 최근 종료 세션 우선
    )
    return {"avg_yawn": float(doc["avg_yawn"]) if doc and "avg_yawn" in doc else None}

ATTN_MINUTES_CUTOFF = 25     # 25분 이전 종료면 집중도 포인트 없음
ATTN_THRESHOLD = 60          # 평균 집중도 60점 이상
ATTN_POINTS = 2              # 집중도 포인트: 고정 2점
HOUR_POINTS = 5              # 시간 포인트: 1시간당 5점
ATTEND_DAILY_POINTS = 2     # 하루 출석 +2
ATTEND_WEEK_BONUS   = 2     # 7일 채우면 +2
ONE_HOUR_SECS       = 3600

def _kst_day_range(when: datetime):
    """KST 기준 당일 [00:00:00, 24:00:00) 범위"""
    if when.tzinfo is None:
        when = KST.localize(when)
    local = when.astimezone(KST)
    start = local.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end

def _session_net_seconds(db, ses) -> float:
    """
    세션의 실제 공부 시간(초).
    우선순위:
      1) 프론트가 준 sum_study_time (초)
      2) (end - start) - sum(break)
    """
    sst = ses.get("sum_study_time")
    if sst is not None:
        try:
            return float(sst)
        except Exception:
            pass
    start = ses.get("study_date"); end = ses.get("end_time")
    if not start or not end:
        return 0.0
    total = (end - start).total_seconds()
    br_secs = 0.0
    for br in db.breaks.find({"session_id": ses["_id"], "end_time": {"$ne": None}}, {"start_time":1,"end_time":1}):
        st = br.get("start_time"); ed = br.get("end_time")
        if st and ed:
            br_secs += max(0.0, (ed - st).total_seconds())
    return max(0.0, total - br_secs)

def _award_point(db, user_oid: ObjectId, value: int, reason: str, when: datetime) -> int:
    # 중복 방지(유니크 인덱스와 중복 체크 이중 방어)
    if db.points.find_one({"user_id": user_oid, "reason": reason}):
        return 0
    db.points.insert_one({
        "user_id": user_oid,
        "gain_date": when,
        "point": int(value),
        "reason": reason,
    })
    # 유저 보유 포인트도 함께 반영
    db.users.update_one({"_id": user_oid}, {"$inc": {"points": int(value)}})
    return int(value)

# --- 집중도 규칙: 25분 이전 종료면 0점, 그 외 평균 집중도 >= 60이면 +2점 ---
def _award_attention_points(db, session_doc) -> int:
    end = session_doc.get("end_time")
    if not end:
        return 0
    dur_min = _session_net_seconds(db, session_doc) / 60.0
    if dur_min < ATTN_MINUTES_CUTOFF:
        return 0
    avg = session_doc.get("focus_score") or 0
    if avg >= ATTN_THRESHOLD:
        sid = str(session_doc.get("_id"))
        day_str = end.astimezone(KST).strftime("%Y-%m-%d")
        reason = f"ATTN_{day_str}_session:{sid}"
        user_oid = session_doc["user_id"] if isinstance(session_doc["user_id"], ObjectId) else ObjectId(session_doc["user_id"])
        return _award_point(db, user_oid, ATTN_POINTS, reason, when=end)
    return 0

# --- 시간 규칙: 당일 누적 공부시간 1시간마다 +5점(중복 방지) ---
def _award_hourly_points(db, user_id, when: datetime) -> int:
    user_oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
    day_start, day_end = _kst_day_range(when)

    total_secs = 0.0
    cur = db.sessions.find(
        {"user_id": user_oid, "study_date": {"$gte": day_start, "$lt": day_end}, "end_time": {"$ne": None}},
        {"_id": 1, "study_date": 1, "end_time": 1, "sum_study_time": 1}
    )
    for ses in cur:
        total_secs += _session_net_seconds(db, ses)
    total_hours = int(total_secs // 3600)

    day_str = day_start.strftime("%Y-%m-%d")
    given = db.points.count_documents({
        "user_id": user_oid,
        "gain_date": {"$gte": day_start, "$lt": day_end},
        "reason": {"$regex": f"^HOUR_{day_str}_"}
    })

    to_give = max(0, total_hours - given)
    gained = 0
    for k in range(given + 1, given + to_give + 1):
        reason = f"HOUR_{day_str}_{k}"
        gained += _award_point(db, user_oid, HOUR_POINTS, reason, when=day_end - timedelta(seconds=1))
    return gained

# --- 출석 규칙: 당일 누적 1시간 달성 시 +2, 연속 7일마다 추가 +2, streak 갱신 ---
def _award_attendance_for_day(db, user_oid: ObjectId, day_start: datetime, when: datetime) -> int:
    day_str = day_start.strftime("%Y-%m-%d")
    # 이미 일일 출석 지급했으면 종료
    if db.points.find_one({"user_id": user_oid, "reason": f"ATTEND_{day_str}"}):
        return 0

    # 당일 누적 공부시간 체크
    day_end = day_start + timedelta(days=1)
    total_secs = 0.0
    for ses in db.sessions.find(
        {"user_id": user_oid, "study_date": {"$gte": day_start, "$lt": day_end}, "end_time": {"$ne": None}},
        {"_id":1, "study_date":1, "end_time":1, "sum_study_time":1}
    ):
        total_secs += _session_net_seconds(db, ses)

    if total_secs < ONE_HOUR_SECS:
        return 0

    gained = 0
    # 1) 일일 출석 +2
    gained += _award_point(db, user_oid, ATTEND_DAILY_POINTS, f"ATTEND_{day_str}", when=when)

    # 2) 연속 출석일(streak) 갱신
    user = db.users.find_one({"_id": user_oid}, {"continuous_count":1}) or {}
    prev_cnt = int(user.get("continuous_count") or 0)
    yday_str = (day_start - timedelta(days=1)).strftime("%Y-%m-%d")
    had_yday = db.points.find_one({"user_id": user_oid, "reason": f"ATTEND_{yday_str}"}) is not None
    new_cnt = (prev_cnt + 1) if had_yday else 1
    db.users.update_one({"_id": user_oid}, {"$set": {"continuous_count": new_cnt}})

    # 3) 7일 보너스
    if new_cnt % 7 == 0:
        bonus_reason = f"ATTEND_WEEK_{day_str}"
        gained += _award_point(db, user_oid, ATTEND_WEEK_BONUS, bonus_reason, when=when)

    return gained

def award_all_points_on_finish(db, session_doc) -> int:
    """
    세션 종료 직후 호출:
      - 집중도 규칙 포인트
      - 당일 누적시간 규칙 포인트
      - 출석(1시간 달성) + 연속 7일 보너스
    """
    gained = 0
    # 1) 집중도 규칙
    gained += _award_attention_points(db, session_doc)
    # 2) 시간 누적 규칙
    end = session_doc.get("end_time") or datetime.now(KST)
    gained += _award_hourly_points(db, session_doc["user_id"], end)
    # 3) 출석/보너스
    day_start, _ = _kst_day_range(end)
    user_oid = session_doc["user_id"] if isinstance(session_doc["user_id"], ObjectId) else ObjectId(session_doc["user_id"])
    gained += _award_attendance_for_day(db, user_oid, day_start, when=end)
    return gained