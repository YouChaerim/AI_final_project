# server/memos.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime, time
import pytz

from .server_db import db

router = APIRouter(prefix="/memos", tags=["Memos"])
KST = pytz.timezone('Asia/Seoul')

class MemoData(BaseModel):
    contents: str


def _today_range_kst():
    """KST 기준 오늘 00:00 ~ 23:59:59.999 범위를 반환."""
    today = datetime.now(KST).date()
    start_of_day = KST.localize(datetime.combine(today, time.min))
    end_of_day = KST.localize(datetime.combine(today, time.max))
    return start_of_day, end_of_day


@router.get("/{user_id}", response_model=MemoData)
def get_memo_by_user(user_id: str):
    # ✅ 오늘 메모만 가져온다 (없으면 빈 문자열)
    try:
        user_obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    start_of_day, end_of_day = _today_range_kst()
    memo = db.memo.find_one(
        {"user_id": user_obj_id, "created_at": {"$gte": start_of_day, "$lte": end_of_day}},
        sort=[("created_at", -1)],
    )
    if memo:
        return {"contents": memo.get("contents", "")}
    return {"contents": ""}


@router.post("/{user_id}")
def upsert_memo_for_today(user_id: str, data: MemoData):
    """
    ✅ 오늘(KST) 문서가 있으면 '수정', 없으면 '새 문서 생성'
    """
    try:
        user_obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    now = datetime.now(KST)
    start_of_day, end_of_day = _today_range_kst()

    existing = db.memo.find_one(
        {"user_id": user_obj_id, "created_at": {"$gte": start_of_day, "$lte": end_of_day}}
    )

    if existing:
        db.memo.update_one(
            {"_id": existing["_id"]},
            {"$set": {"contents": data.contents, "updated_at": now}},
        )
        return {"status": "success", "message": "Memo updated (today)"}
    else:
        db.memo.insert_one(
            {
                "user_id": user_obj_id,
                "contents": data.contents,
                "created_at": now,
                "updated_at": now,
            }
        )
        return {"status": "success", "message": "Memo created (new day)"}
