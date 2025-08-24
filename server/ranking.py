# server/ranking.py
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta, timezone
from bson import ObjectId
import os

from .server_db import db

router = APIRouter(prefix="/ranking", tags=["Ranking"])
KST = timezone(timedelta(hours=9))

Users  = db[os.getenv("USER_COLL", "User")]
Points = db[os.getenv("POINTS_COLL", "points")]

def _window(period: str):
    now = datetime.now(KST)
    if period == "weekly":
        return now - timedelta(days=7), now
    if period == "monthly":
        return now - timedelta(days=30), now
    # all-time
    return datetime(1970,1,1,tzinfo=KST), now

@router.get("/top")
def ranking_top(
    period: str = Query("weekly", pattern="^(weekly|monthly|all)$"),
    limit: int = Query(50, ge=1, le=200),
):
    start, end = _window(period)

    pipeline = [
        {"$match": {"gain_date": {"$gte": start, "$lt": end}}},
        {"$group": {
            "_id": "$user_id",
            # ATTENDANCE#YYYY-MM-DD 건수를 출석으로 카운트
            "attempts": {"$sum": {
                "$cond": [{"$regexMatch": {"input": "$reason", "regex": r"^ATTENDANCE#"}}, 1, 0]
            }},
            # 포인트는 보상(+만) 합산. (BET_START 등 음수 차감 제외)
            "points": {"$sum": {"$cond": [{"$gt": ["$point", 0]}, "$point", 0]}},
        }},
        {"$sort": {"points": -1, "attempts": -1}},
        {"$limit": limit},
    ]
    rows = list(Points.aggregate(pipeline))

    # 유저 정보 합치기
    out = []
    for r in rows:
        uid = r["_id"]
        u = Users.find_one({"_id": uid}, {"nickname": 1, "points": 1})
        name = (u or {}).get("nickname") or f"user-{str(uid)[-6:]}"
        out.append({
            "user_id": str(uid),
            "name": name,
            "attempts": int(r.get("attempts", 0)),
            "points": int(r.get("points", 0)),     # 기간 내 획득한(+만) 포인트 합
            "balance": int((u or {}).get("points", 0)),  # 현재 보유 포인트(참고용)
        })

    return {
        "period": period,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "rows": out,
    }
