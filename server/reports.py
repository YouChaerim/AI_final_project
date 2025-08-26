# server/reports.py
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta, timezone
from bson import ObjectId
from typing import Optional, List, Dict, Any
import os

from .server_db import db

router = APIRouter(prefix="/reports", tags=["Reports"])
KST = timezone(timedelta(hours=9))

def _users():   return db[os.getenv("USER_COLL", "User")]
def _points():  return db[os.getenv("POINTS_COLL", "points")]
def _sess():    return db[os.getenv("SESSIONS_COLL", "sessions")]
def _att():     return db[os.getenv("ATTENDANCE_COLL", "attendance")]
def _focus():   return db[os.getenv("FOCUS_COLL", "focus_events")]

def _oid(x: str) -> ObjectId:
    if not ObjectId.is_valid(x): raise HTTPException(400, "invalid ObjectId")
    return ObjectId(x)

def _resolve_uid(user_key: str) -> ObjectId:
    U = _users()
    if ObjectId.is_valid(user_key):
        f = U.find_one({"_id": ObjectId(user_key)}, {"_id": 1})
        if f: return f["_id"]
    ors = []
    for f in ["local_user_id","localUserId","localId","localid",
              "provider_id","providerId","provider",
              "id","user_id","userId","email","username"]:
        ors.append({f: user_key})
        try: ors.append({f: int(user_key)})    # 숫자형 id 대응
        except: pass
    f = U.find_one({"$or": ors}, {"_id": 1})
    if not f: raise HTTPException(404, "user not found")
    return f["_id"]

def _dt_kst(date_str: str, end=False) -> datetime:
    # 00:00(시작) 또는 다음날 00:00(끝 경계)
    d = datetime.strptime(date_str, "%Y-%m-%d")
    base = datetime(d.year, d.month, d.day, tzinfo=KST)
    return base + (timedelta(days=1) if end else timedelta(0))

@router.get("/daily/{user_key}")
def daily_report(
    user_key: str,
    start: str = Query(..., description="YYYY-MM-DD"),
    end: str   = Query(..., description="YYYY-MM-DD")
):
    uid = _resolve_uid(user_key)
    t0 = _dt_kst(start, end=False)
    t1 = _dt_kst(end,   end=True)

    # ----- points(양수만) 일자 합계 + 사유별 합계 -----
    pos_match = {"user_id": uid, "gain_date": {"$gte": t0, "$lt": t1}, "point": {"$gt": 0}}
    pts_by_day = {
        d["_id"].date().isoformat(): int(d["sum"])
        for d in _points().aggregate([
            {"$match": pos_match},
            {"$group": {"_id": {"$dateTrunc": {"date": "$gain_date", "unit": "day", "timezone": "Asia/Seoul"}},
                        "sum": {"$sum": "$point"}}}
        ])
    }
    pts_by_reason = {
        d["_id"] or "UNKNOWN": int(d["sum"])
        for d in _points().aggregate([
            {"$match": pos_match},
            {"$group": {"_id": "$reason", "sum": {"$sum": "$point"}}}
        ])
    }

    # ----- study sessions 일자 합계(분) -----
    # minutes 필드가 있으면 사용, 없으면 end-start 계산
    ses_by_day = {
        d["_id"].date().isoformat(): float(d["min"])
        for d in _sess().aggregate([
            {"$match": {"user_id": uid,
                        "$or": [
                            {"start": {"$gte": t0, "$lt": t1}},
                            {"study_date": {"$gte": t0, "$lt": t1}}
                        ]}},
            {"$project": {
                # start/end 필드 혼재 대응
                "startX": {"$ifNull": ["$start", "$study_date"]},
                "endX":   {"$ifNull": ["$end", "$end_time"]},
                "minutes": {"$ifNull": [
                    "$minutes",
                    {"$divide": [{"$subtract": [
                        {"$ifNull": ["$end", "$end_time"]},
                        {"$ifNull": ["$start", "$study_date"]}
                    ]}, 60000]}
                ]}
            }},
            {"$project": {
                "day": {"$dateTrunc": {"date": "$startX", "unit": "day", "timezone": "Asia/Seoul"}},
                "minutes": {"$ifNull": ["$minutes", 0]}
            }},
            {"$group": {"_id": "$day", "min": {"$sum": "$minutes"}}}
        ])
    }

    # ----- attendance(출석) -----
    # attendance.date(자정 기준) 또는 checked_at로 존재하는 날을 1로
    att_days = set()
    for d in _att().aggregate([
        {"$match": {"user_id": uid,
                    "$or": [{"date": {"$gte": t0, "$lt": t1}},
                            {"checked_at": {"$gte": t0, "$lt": t1}}]}},
        {"$project": {"day": {"$ifNull": ["$date", {"$dateTrunc": {"date": "$checked_at", "unit":"day", "timezone": "Asia/Seoul"}}]}}},
        {"$group": {"_id": "$day"}}
    ]):
        att_days.add(d["_id"].date().isoformat())

    # 보조 규칙: 해당 '날짜'에 ATTEND 계열 포인트가 있으면 그 날을 출석으로 인정
    att_from_points_days = {
        d["_id"].date().isoformat()
        for d in _points().aggregate([
            {"$match": {**pos_match, "reason": {"$regex": "ATTEND", "$options": "i"}}},
            {"$group": {"_id": {
                "$dateTrunc": {"date": "$gain_date", "unit": "day", "timezone": "Asia/Seoul"}
            }}}
        ])
    }
    att_days |= att_from_points_days

    # ----- 날짜축 생성 & 병합 -----
    days = []
    cur = t0
    while cur < t1:
        iso = cur.date().isoformat()
        days.append({
            "date": iso,
            "study_minutes": int(round(ses_by_day.get(iso, 0.0))),
            "points": int(pts_by_day.get(iso, 0)),
            "attendance": 1 if iso in att_days else 0
        })
        cur += timedelta(days=1)

    return {
        "user_id": str(uid),
        "start": start, "end": end,
        "days": days,
        "points_by_reason": pts_by_reason
    }

@router.get("/focus/{user_key}")
def focus_of_day(user_key: str, day: str = Query(..., description="YYYY-MM-DD")):
    uid = _resolve_uid(user_key)
    d0 = _dt_kst(day, end=False)
    d1 = _dt_kst(day, end=True)
    items = list(_focus().find({"user_id": uid, "ts": {"$gte": d0, "$lt": d1}},
                               {"_id":0,"time":1,"blinks":1,"yawns":1}).sort("ts", 1))
    # 없으면 가벼운 샘플 제공
    if not items:
        items = [{"time":"09:00","blinks":2,"yawns":1},
                 {"time":"10:00","blinks":3,"yawns":1},
                 {"time":"14:30","blinks":4,"yawns":2}]
    return {"day": day, "events": items}

@router.get("/summary/{user_key}")
def summary_all(user_key: str):
    uid = _resolve_uid(user_key)
    U = _users()
    P = _points()
    S = _sess()
    A = _att()

    u = U.find_one({"_id": uid}, {"created_at":1, "points":1})
    if not u:
        raise HTTPException(404, "user not found")
    created_at = u.get("created_at") or datetime(1970,1,1, tzinfo=KST)
    now = datetime.now(tz=KST)

    # 1) 총 학습일 = 출석한 일수(가입~현재)
    att_days = set()
    for d in A.aggregate([
        {"$match": {"user_id": uid,
                    "$or":[{"date":{"$gte":created_at, "$lt":now}},
                           {"checked_at":{"$gte":created_at, "$lt":now}}]}},
        {"$project":{"day":{"$ifNull":["$date", {"$dateTrunc":{"date":"$checked_at","unit":"day","timezone":"Asia/Seoul"}}]}}},
        {"$group":{"_id":"$day"}}
    ]):
        att_days.add(d["_id"].date())

    # 출석 기록이 없다면 세션이 있는 날을 보조로 포함
    for d in S.aggregate([
        {"$match": {"user_id": uid, "start": {"$gte": created_at, "$lt": now}}},
        {"$project": {"day": {"$dateTrunc":{"date":"$start","unit":"day","timezone":"Asia/Seoul"}}}},
        {"$group": {"_id":"$day"}}
    ]):
        att_days.add(d["_id"].date())

    total_learning_days = len(att_days)

    # 2) 연속 출석일(오늘부터 거꾸로, 하루 60분 이상 학습)
    #    minutes 필드가 없으면 end-start로 대체
    pipeline = [
        {"$match": {"user_id": uid, "start": {"$type": "date"}}},  # start 가 날짜인 문서만
        {"$project": {
            "day": {"$dateTrunc": {"date": "$start", "unit": "day", "timezone": "Asia/Seoul"}},
            # minutes 필드가 없으면 end-start, 그마저도 없으면 0
            "minutes": {
                "$ifNull": [
                    "$minutes",
                    {"$divide": [{"$subtract": ["$end", "$start"]}, 60000]}
                ]
            }
        }},
        {"$match": {"day": {"$ne": None}}},  # day 가 null 인 것 제거
        {"$group": {
            "_id": "$day",
            "min": {"$sum": {"$ifNull": ["$minutes", 0]}}
        }}
    ]

    minutes_by_day = {}
    for d in S.aggregate(pipeline):
        day = d.get("_id")
        if isinstance(day, datetime):  # 혹시 모를 None 방어
            minutes_by_day[day.date()] = float(d.get("min") or 0.0)
    streak = 0
    cur = datetime.now(tz=KST).date()
    while True:
        if minutes_by_day.get(cur, 0) >= 60:
            streak += 1
            cur -= timedelta(days=1)
        else:
            break

    # 3) 총 포인트(가입~현재): 유저 문서의 보유 포인트가 있으면 그 값을 사용
    total_points = int(u.get("points", 0))

    return {
        "total_learning_days": total_learning_days,
        "streak_days": streak,
        "total_points": total_points,
        "created_at": (created_at.astimezone(KST)).date().isoformat()
    }


# === NEW: 기간별 집중도 히스토그램(시간대 24칸) ===
@router.get("/focus_hist/{user_key}")
def focus_hist(user_key: str, start: str = Query(...), end: str = Query(...)):
    uid = _resolve_uid(user_key)
    t0 = _dt_kst(start, end=False)
    t1 = _dt_kst(end,   end=True)

    S = _sess()
    items = list(S.find(
        {"user_id": uid, "$or": [
            {"start": {"$lt": t1}, "end": {"$gt": t0}},
            {"study_date": {"$lt": t1}, "end_time": {"$gt": t0}}
        ]},
        {"start":1, "end":1, "study_date":1, "end_time":1, "focus_score":1, "minutes":1}
    ))

    def _as_kst(dt):
        if not dt: return None
        return dt.replace(tzinfo=KST) if dt.tzinfo is None else dt.astimezone(KST)

    wsum = [0.0]*24; wmin = [0.0]*24
    for it in items:
        s = _as_kst(it.get("start") or it.get("study_date"))
        e = _as_kst(it.get("end") or it.get("end_time") or s)
        fs = float(it.get("focus_score") or 0)
        if not s or not e: continue
        s = max(s, t0); e = min(e, t1)
        if e <= s: continue

        cur = s
        while cur < e:
            h_end = datetime(cur.year, cur.month, cur.day, cur.hour, tzinfo=KST) + timedelta(hours=1)
            seg_end = min(h_end, e)
            mins = (seg_end - cur).total_seconds()/60.0
            if mins > 0:
                idx = cur.hour
                wsum[idx] += fs * mins
                wmin[idx] += mins
            cur = seg_end

    hourly = [(wsum[h]/wmin[h] if wmin[h] > 0 else 0.0) for h in range(24)]
    return {"start": start, "end": end, "hourly": hourly}
