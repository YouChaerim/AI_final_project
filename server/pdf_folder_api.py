# server/pdf_folder_api.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from pymongo import MongoClient
import os, shutil

# ---- 환경설정 ----
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB  = os.getenv("MONGODB_DB", "ttalk")
# 서버 로컬 저장 디렉토리 (없으면 생성)
PDF_STORAGE_DIR = os.getenv(
    "PDF_STORAGE_DIR",
    os.path.join(os.path.dirname(__file__), "data", "pdf_storage")
)
os.makedirs(PDF_STORAGE_DIR, exist_ok=True)

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]
PDFs = db["pdf_files"]
PDFs.create_index([("user_id", 1), ("date", 1), ("created_at", 1)])

KST = timezone(timedelta(hours=9))
router = APIRouter()


# ---- 유틸 ----
def _oid(s: str) -> ObjectId:
    try:
        return ObjectId(s)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid id")

def _now_kst() -> str:
    return datetime.now(tz=KST).isoformat(timespec="seconds")

def _ser(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "user_id": str(doc["user_id"]),
        "date": doc["date"],
        "title": doc.get("title") or os.path.splitext(doc.get("original_name", "PDF"))[0],
        "original_name": doc.get("original_name", "file.pdf"),
        "size": int(doc.get("size", 0)),
        "notes": doc.get("notes", ""),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


# ---- API: 목록 ----
@router.get("/pdf-folder/list")
def list_pdfs(user_id: str, date: Optional[str] = None):
    uid = _oid(user_id)
    q = {"user_id": uid}
    if date:
        q["date"] = date
    cur = PDFs.find(q).sort([("date", -1), ("updated_at", -1)])
    return {"items": [_ser(d) for d in cur]}


# ---- API: 업로드(단일 파일) ----
@router.post("/pdf-folder/upload")
async def upload_pdf(
    user_id: str = Form(...),
    date: str = Form(...),
    file: UploadFile = File(...)
):
    uid = _oid(user_id)
    original_name = os.path.basename(file.filename or "file.pdf")
    day_dir = os.path.join(PDF_STORAGE_DIR, date)
    os.makedirs(day_dir, exist_ok=True)

    # ObjectId 미리 생성해서 파일명으로 사용
    new_id = ObjectId()
    stored_path = os.path.join(day_dir, f"{new_id}.pdf")

    # 파일 저장
    with open(stored_path, "wb") as out:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)

    size = os.path.getsize(stored_path)
    doc = {
        "_id": new_id,
        "user_id": uid,
        "date": date,
        "title": os.path.splitext(original_name)[0],
        "original_name": original_name,
        "stored_path": stored_path,
        "size": int(size),
        "notes": "",
        "created_at": _now_kst(),
        "updated_at": _now_kst(),
    }
    PDFs.insert_one(doc)
    return {"item": _ser(doc)}


# ---- API: 수정 ----
class PdfUpdate(BaseModel):
    user_id: str
    date: Optional[str] = None
    title: Optional[str] = None
    notes: Optional[str] = None

@router.put("/pdf-folder/update/{pdf_id}")
def update_pdf(pdf_id: str, body: PdfUpdate):
    uid = _oid(body.user_id)
    _id = _oid(pdf_id)
    doc = PDFs.find_one({"_id": _id, "user_id": uid})
    if not doc:
        raise HTTPException(status_code=404, detail="pdf not found")

    upd: Dict[str, Any] = {}
    if body.title is not None:
        upd["title"] = body.title
    if body.notes is not None:
        upd["notes"] = body.notes
    # 날짜 변경 시 파일 폴더도 같이 이동
    if body.date and body.date != doc["date"]:
        new_dir = os.path.join(PDF_STORAGE_DIR, body.date)
        os.makedirs(new_dir, exist_ok=True)
        new_path = os.path.join(new_dir, f"{pdf_id}.pdf")
        try:
            shutil.move(doc["stored_path"], new_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"file move failed: {e}")
        upd["date"] = body.date
        upd["stored_path"] = new_path

    upd["updated_at"] = _now_kst()
    PDFs.update_one({"_id": _id}, {"$set": upd})
    return {"item": _ser(PDFs.find_one({"_id": _id}))}


# ---- API: 삭제 ----
@router.delete("/pdf-folder/delete/{pdf_id}")
def delete_pdf(pdf_id: str, user_id: str):
    uid = _oid(user_id)
    _id = _oid(pdf_id)
    doc = PDFs.find_one({"_id": _id, "user_id": uid})
    if not doc:
        return {"ok": False}
    try:
        if os.path.exists(doc.get("stored_path", "")):
            os.remove(doc["stored_path"])
    except Exception:
        pass
    PDFs.delete_one({"_id": _id, "user_id": uid})
    return {"ok": True}


# ---- API: 다운로드 ----
@router.get("/pdf-folder/download/{pdf_id}")
def download_pdf(pdf_id: str, user_id: str):
    uid = _oid(user_id)
    _id = _oid(pdf_id)
    doc = PDFs.find_one({"_id": _id, "user_id": uid})
    if not doc:
        raise HTTPException(status_code=404, detail="pdf not found")
    path = doc.get("stored_path")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="file missing")
    return FileResponse(path, media_type="application/pdf", filename=doc.get("original_name", "file.pdf"))
