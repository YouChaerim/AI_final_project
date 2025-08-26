# server/shop.py
from fastapi import APIRouter, Query, Body, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from typing import Optional, Dict
from datetime import datetime, timedelta, timezone
import os
from pymongo import ReturnDocument

from .server_db import db

router = APIRouter(prefix="/shop", tags=["shop"])
KST = timezone(timedelta(hours=9))

Users = db[os.getenv("USER_COLL", "User")]
Shop  = db[os.getenv("SHOP_COLL", "shop")]

CHAR_PRICES = {
    "bear": 1000,
    "cat": 1000,
    "rabbit": 1000,
    "shiba": 1000,   # assets 파일명은 siba.png 이지만, 논리 ID는 shiba 로 통일
}

def _to_object_id(maybe_id: str) -> Optional[ObjectId]:
    try:
        return ObjectId(maybe_id) if maybe_id and len(maybe_id) == 24 else None
    except Exception:
        return None

def find_user(doc_id_or_userid: str) -> Dict:
    """_id(24hex) 또는 id/user_id 문자열을 받아 User 도큐먼트 조회."""
    oid = _to_object_id(doc_id_or_userid)
    if oid:
        u = Users.find_one({"_id": oid})
    else:
        u = Users.find_one({"$or": [{"id": doc_id_or_userid}, {"user_id": doc_id_or_userid}]})
    if not u:
        raise NotFound("사용자를 찾을 수 없습니다.")
    return u

def ensure_shop_doc(user_id: str) -> Dict:
    """Shop 컬렉션에 사용자 소유목록 문서를 보장."""
    doc = Shop.find_one({"user_id": user_id})
    if not doc:
        doc = {"user_id": user_id, "owned_chars": []}
        Shop.insert_one(doc)
        doc = Shop.find_one({"user_id": user_id})
    return doc

def get_state(user_id: str) -> Dict:
    u = find_user(user_id)
    shop = ensure_shop_doc(str(u.get("_id")))

    # coins/points 이름 정리 (DB에는 points로 저장한다고 가정)
    points = int(u.get("points", 0))
    active_char = u.get("active_char") or "ddalkkak"

    return {
        "user_id": str(u["_id"]),
        "nickname": u.get("nickname") or u.get("id") or "-",
        "points": points,
        "active_char": active_char,
        "owned_chars": shop.get("owned_chars", []),
    }

def buy_char(user_id: str, char_id: str) -> Dict:
    if char_id not in CHAR_PRICES:
        raise ValueError("존재하지 않는 캐릭터입니다.")
    price = CHAR_PRICES[char_id]

    uid = _to_object_id(get_state(user_id)["user_id"])
    # 1) 포인트 원자적 차감(충분할 때만)
    updated_user = Users.find_one_and_update(
        {"_id": uid, "points": {"$gte": price}},
        {"$inc": {"points": -price}},
        return_document=ReturnDocument.AFTER
    )
    if not updated_user:
        return {"ok": False, "message": "포인트가 부족합니다.", "state": get_state(user_id)}

    # 2) 소유 추가(이미 있으면 변화 없음)
    Shop.update_one(
        {"user_id": str(uid)},
        {"$addToSet": {"owned_chars": char_id}},
        upsert=True
    )
    return {"ok": True, "message": "구매 완료", "state": get_state(user_id)}

def select_char(user_id: str, char_id: str) -> Dict:
    state = get_state(user_id)
    if char_id not in state["owned_chars"]:
        return {"ok": False, "message": "보유하지 않은 캐릭터입니다.", "state": state}

    Users.update_one(
        {"_id": _to_object_id(state["user_id"])},
        {"$set": {"active_char": char_id}}
    )
    return {"ok": True, "message": "선택 완료", "state": get_state(user_id)}


class NotFound(Exception):
    pass

class BuyBody(BaseModel):
    user_id: str
    char_id: str

class SelectBody(BaseModel):
    user_id: str
    char_id: str

@router.get("/state")
def api_state(user_id: str = Query(..., description="User _id(24hex) 또는 id/user_id")):
    try:
        return {"ok": True, "state": get_state(user_id)}
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/buy")
def api_buy(body: BuyBody = Body(...)):
    try:
        result = buy_char(body.user_id, body.char_id)
        if not result["ok"]:
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/select")
def api_select(body: SelectBody = Body(...)):
    try:
        result = select_char(body.user_id, body.char_id)
        if not result["ok"]:
            raise HTTPException(status_code=400, detail=result["message"])
        return result
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))