# server/memo_folder_api.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from pymongo import MongoClient, ASCENDING, DESCENDING
import os

# ---- 환경/DB ----
KST = timezone(timedelta(hours=9))
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB  = os.getenv("MONGODB_DB", "ttalk")

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]
MemoFolder = db["memo_folder"]   # ✅ 메인의 memos와 분리된 전용 컬렉션

# 인덱스
MemoFolder.create_index([("user_id", ASCENDING), ("date", ASCENDING), ("created_at", DESCENDING)])

router = APIRouter(prefix="/memo-folder", tags=["memo-folder"])

# ---- 모델 ----
class MemoIn(BaseModel):
    user_id: str = Field(..., description="사용자 ObjectId(hex)")
    date: str    = Field(..., description="YYYY-MM-DD")
    title: str   = ""
    content: str = ""

def _oid(x: str) -> ObjectId:
    try:
        return ObjectId(x)
    except Exception:
        raise HTTPException(400, detail="invalid ObjectId")

def _to_json(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "user_id": str(doc["user_id"]),
        "date": doc["date"],
        "title": doc.get("title", ""),
        "content": doc.get("content", ""),
        "created_at": doc.get("created_at", datetime.now(KST)).isoformat(),
        "updated_at": doc.get("updated_at", doc.get("created_at", datetime.now(KST))).isoformat(),
    }

# ---- API ----
@router.get("/list")
def list_memos(user_id: str, date: Optional[str] = Query(None, description="YYYY-MM-DD")):
    q = {"user_id": _oid(user_id)}
    if date:
        q["date"] = date
    cur = MemoFolder.find(q).sort([("date", ASCENDING), ("created_at", DESCENDING)])
    return {"items": [_to_json(x) for x in cur]}

@router.post("/add")
def add_memo(body: MemoIn):
    now = datetime.now(KST)
    doc = {
        "user_id": _oid(body.user_id),
        "date": body.date,
        "title": body.title or "",
        "content": body.content or "",
        "created_at": now,
        "updated_at": now,
    }
    ins = MemoFolder.insert_one(doc)
    doc["_id"] = ins.inserted_id
    return {"ok": True, "item": _to_json(doc)}

@router.put("/update/{memo_id}")
def update_memo(memo_id: str, body: MemoIn):
    upd = {
        "date": body.date,
        "title": body.title or "",
        "content": body.content or "",
        "updated_at": datetime.now(KST),
    }
    r = MemoFolder.update_one({"_id": _oid(memo_id), "user_id": _oid(body.user_id)}, {"$set": upd})
    if r.matched_count == 0:
        raise HTTPException(404, "memo not found")
    d = MemoFolder.find_one({"_id": _oid(memo_id)})
    return {"ok": True, "item": _to_json(d)}

@router.delete("/delete/{memo_id}")
def delete_memo(memo_id: str, user_id: str):
    r = MemoFolder.delete_one({"_id": _oid(memo_id), "user_id": _oid(user_id)})
    return {"ok": r.deleted_count == 1}
