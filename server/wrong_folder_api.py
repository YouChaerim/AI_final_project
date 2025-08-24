# server/wrong_folder_api.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from pymongo import MongoClient
import os

# === DB 연결 ===
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB  = os.getenv("MONGODB_DB", "ttalk")

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]

memo_coll  = db["memo_folder"]   # 메모 폴더 전용
wrong_coll = db["wrongbook"]     # 오답 폴더 전용

# 인덱스(최초 1회)
memo_coll.create_index([("user_id", 1), ("date", 1)])
wrong_coll.create_index([("user_id", 1), ("date", 1), ("created_at", 1)])

router = APIRouter()

KST = timezone(timedelta(hours=9))

# === 유틸 ===
def to_oid(s: str) -> ObjectId:
    try:
        return ObjectId(s)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid user_id or id")

def ser_memo(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc.get("_id")),
        "user_id": str(doc.get("user_id")),
        "date": doc.get("date"),            # 'YYYY-MM-DD'
        "title": doc.get("title", ""),
        "content": doc.get("content", ""),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }

def ser_wrong(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc.get("_id")),
        "user_id": str(doc.get("user_id")),
        "date": doc.get("date"),            # 'YYYY-MM-DD'
        "quiz_id": doc.get("quiz_id"),
        "question": doc.get("question", ""),
        "my_answer": doc.get("my_answer", ""),
        "correct_answer": doc.get("correct_answer", ""),
        "explanation": doc.get("explanation", ""),
        "image": doc.get("image"),
        "source": doc.get("source"),
        "page": doc.get("page"),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }

def now_kst_iso() -> str:
    return datetime.now(tz=KST).isoformat(timespec="seconds")

# === 스키마 ===
class MemoCU(BaseModel):
    user_id: str = Field(..., description="24-hex ObjectId 문자열")
    date: str    = Field(..., description="YYYY-MM-DD")
    title: str   = ""
    content: str = ""

class WrongCU(BaseModel):
    user_id: str
    date: str                      # YYYY-MM-DD
    question: str = ""
    my_answer: str = ""
    correct_answer: str = ""
    explanation: str = ""
    image: Optional[str] = None
    source: Optional[str] = None
    page: Optional[int] = None

# ---------------------------
# 메모 폴더
# ---------------------------

@router.get("/memo-folder/list")
def memo_list(user_id: str = Query(...), date: Optional[str] = Query(None)):
    uid = to_oid(user_id)
    q = {"user_id": uid}
    if date:
        q["date"] = date
    cur = memo_coll.find(q).sort([("date", -1), ("created_at", 1)])
    items = [ser_memo(d) for d in cur]
    return {"items": items}

@router.post("/memo-folder/add")
def memo_add(body: MemoCU):
    uid = to_oid(body.user_id)
    doc = {
        "user_id": uid,
        "date": body.date,
        "title": body.title or "",
        "content": body.content or "",
        "created_at": now_kst_iso(),
        "updated_at": now_kst_iso(),
    }
    _id = memo_coll.insert_one(doc).inserted_id
    doc["_id"] = _id
    return {"item": ser_memo(doc)}

@router.put("/memo-folder/update/{memo_id}")
def memo_update(memo_id: str, body: MemoCU):
    uid = to_oid(body.user_id)
    mid = to_oid(memo_id)
    upd = {
        "date": body.date,
        "title": body.title or "",
        "content": body.content or "",
        "updated_at": now_kst_iso(),
    }
    res = memo_coll.update_one({"_id": mid, "user_id": uid}, {"$set": upd})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="memo not found")
    doc = memo_coll.find_one({"_id": mid})
    return {"item": ser_memo(doc)}

@router.delete("/memo-folder/delete/{memo_id}")
def memo_delete(memo_id: str, user_id: str = Query(...)):
    uid = to_oid(user_id)
    mid = to_oid(memo_id)
    res = memo_coll.delete_one({"_id": mid, "user_id": uid})
    return {"ok": res.deleted_count == 1}

# ---------------------------
# 오답 폴더
# ---------------------------

@router.get("/wrong-folder/list")
def wrong_list(user_id: str = Query(...), date: Optional[str] = Query(None)):
    uid = to_oid(user_id)
    q = {"user_id": uid}
    if date:
        q["date"] = date
    cur = wrong_coll.find(q).sort([("date", -1), ("created_at", 1)])
    items = [ser_wrong(d) for d in cur]
    return {"items": items}

@router.post("/wrong-folder/add")
def wrong_add(body: WrongCU):
    uid = to_oid(body.user_id)
    doc = {
        "user_id": uid,
        "date": body.date,
        "quiz_id": f"OCR-{body.date}-{ObjectId()}",  # 프론트 요구에 맞춰 생성
        "question": body.question or "",
        "my_answer": body.my_answer or "",
        "correct_answer": body.correct_answer or "",
        "explanation": body.explanation or "",
        "image": body.image,
        "source": body.source,
        "page": body.page,
        "created_at": now_kst_iso(),
        "updated_at": now_kst_iso(),
    }
    _id = wrong_coll.insert_one(doc).inserted_id
    doc["_id"] = _id
    return {"item": ser_wrong(doc)}

@router.put("/wrong-folder/update/{wid}")
def wrong_update(wid: str, body: WrongCU):
    uid = to_oid(body.user_id)
    _id = to_oid(wid)
    upd = {
        "date": body.date,
        "question": body.question or "",
        "my_answer": body.my_answer or "",
        "correct_answer": body.correct_answer or "",
        "explanation": body.explanation or "",
        "image": body.image,
        "source": body.source,
        "page": body.page,
        "updated_at": now_kst_iso(),
    }
    res = wrong_coll.update_one({"_id": _id, "user_id": uid}, {"$set": upd})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="wrong item not found")
    doc = wrong_coll.find_one({"_id": _id})
    return {"item": ser_wrong(doc)}

@router.delete("/wrong-folder/delete/{wid}")
def wrong_delete(wid: str, user_id: str = Query(...)):
    uid = to_oid(user_id)
    _id = to_oid(wid)
    res = wrong_coll.delete_one({"_id": _id, "user_id": uid})
    return {"ok": res.deleted_count == 1}
