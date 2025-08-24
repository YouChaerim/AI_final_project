# server/todos.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from bson import ObjectId
from datetime import datetime, time
import pytz
from .server_db import db

router = APIRouter(prefix="/todos", tags=["Todos"])
KST = pytz.timezone('Asia/Seoul')

class TodoItem(BaseModel):
    id: str
    contents: str
    complete: bool

class TodoCreateItem(BaseModel):
    text: str

class TodoListCreate(BaseModel):
    todo_items: List[TodoCreateItem]

def serialize_todo(todo):
    return {"id": str(todo["_id"]), "contents": todo["contents"], "complete": todo["complete"]}

def _today_range():
    today_kst = datetime.now(KST).date()
    start = KST.localize(datetime.combine(today_kst, time.min))
    end = KST.localize(datetime.combine(today_kst, time.max))
    return start, end

@router.get("/{user_id}", response_model=List[TodoItem])
def get_todos_by_user(user_id: str):
    try:
        user_obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    start, end = _today_range()
    query = {"user_id": user_obj_id, "todo_date": {"$gte": start, "$lte": end}}
    return [serialize_todo(t) for t in db.todo.find(query).sort("_id", 1)]

@router.put("/toggle/{user_id}/{todo_id}")
def toggle_todo_status(user_id: str, todo_id: str):
    try:
        user_obj_id = ObjectId(user_id)
        todo_obj_id = ObjectId(todo_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    start, end = _today_range()
    todo = db.todo.find_one({
        "_id": todo_obj_id,
        "user_id": user_obj_id,
        "todo_date": {"$gte": start, "$lte": end},
    })
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    new_status = not todo.get("complete", False)
    db.todo.update_one({"_id": todo_obj_id}, {"$set": {"complete": new_status}})
    return {"status": "success"}

@router.post("/{user_id}")
def create_new_todos(user_id: str, data: TodoListCreate):
    """오늘 날짜에 '없는 텍스트'만 새로 생성 (기존은 유지)."""
    try:
        user_obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    start, end = _today_range()
    today_query = {"user_id": user_obj_id, "todo_date": {"$gte": start, "$lte": end}}
    existing = set(t["contents"] for t in db.todo.find(today_query))
    to_insert = []
    now = datetime.now(KST)

    for item in data.todo_items:
        text = (item.text or "").strip()
        if not text or text in existing:
            continue
        to_insert.append({
            "user_id": user_obj_id,
            "contents": text,
            "complete": False,
            "todo_date": now
        })

    if to_insert:
        db.todo.insert_many(to_insert)

    return {"status": "success", "created": len(to_insert)}

class TodoUpdateBody(BaseModel):
    text: str

@router.put("/update/{user_id}/{todo_id}")
def update_todo_text(user_id: str, todo_id: str, body: TodoUpdateBody):
    """오늘 항목의 텍스트만 수정 (완료상태/날짜는 유지)."""
    try:
        user_obj_id = ObjectId(user_id)
        todo_obj_id = ObjectId(todo_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    new_text = (body.text or "").strip()
    if not new_text:
        raise HTTPException(status_code=400, detail="Text is empty")

    start, end = _today_range()
    todo = db.todo.find_one({
        "_id": todo_obj_id,
        "user_id": user_obj_id,
        "todo_date": {"$gte": start, "$lte": end},
    })
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    # 중복 텍스트로 바꾸려면 허용/차단 중 선택. 여기선 허용(그대로 업데이트)
    db.todo.update_one({"_id": todo_obj_id}, {"$set": {"contents": new_text}})
    return {"status": "success"}
