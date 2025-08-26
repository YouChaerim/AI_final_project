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
            {"$match": {"user_id": uid, "start": {"$gte": t0, "$lt": t1}}},
            {"$project": {
                "day": {"$dateTrunc": {"date": "$start", "unit": "day", "timezone": "Asia/Seoul"}},
                "minutes": {"$ifNull": ["$minutes", {"$divide":[{"$subtract":["$end","$start"]}, 60000]}]}
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

    # 보조 규칙: 세션이 있거나 ATTENDANCE 포인트가 있으면 출석 1로 인정
    for k in set(list(ses_by_day.keys()) + list(pts_by_day.keys())):
        if k in pts_by_day and "ATTEND" in ",".join(pts_by_reason.keys()).upper():
            att_days.add(k)

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
