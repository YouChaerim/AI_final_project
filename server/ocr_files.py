# server/ocr_files.py
# 사용법:
#  - POST   /ocr-files/{user_id}            : PDF 업로드(+요약 저장)
#  - GET    /ocr-files/{user_id}            : 사용자별 목록
#  - GET    /ocr-files/detail/{doc_id}      : 단건 상세
#  - GET    /ocr-files/download/{doc_id}    : 파일 다운로드
#  - DELETE /ocr-files/{doc_id}             : 삭제(문서+파일)
#  - GET    /ocr-files/debug/where          : 어떤 컬렉션 쓰는지/카운트 확인

import os, re
from datetime import datetime
import pytz
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import FileResponse
from bson import ObjectId

from .server_db import db

router = APIRouter(prefix="/ocr-files", tags=["Writing OCR"])
KST = pytz.timezone("Asia/Seoul")

# ─────────────────────────────────────────────────────────────
# 환경/경로 설정
# ─────────────────────────────────────────────────────────────
OCR_COLL = os.getenv("OCR_COLL", "writin_ocr")  # ← 기본값을 스키마 이름에 맞춤
UPLOAD_ROOT = os.getenv("UPLOAD_ROOT", "uploads")
OCR_DIR = os.path.join(UPLOAD_ROOT, "ocr")
os.makedirs(OCR_DIR, exist_ok=True)


def _col():
    return db[OCR_COLL]
_ocr_coll = _col

def _ensure_indexes():
    _col().create_index([("user_id", 1), ("regist_at", -1)])
    _col().create_index([("pdf_url", 1)])
_ensure_indexes()

def _oid(x: str) -> ObjectId:
    if not ObjectId.is_valid(x):
        raise HTTPException(400, "invalid ObjectId")
    return ObjectId(x)

def _slug_filename(name: str) -> str:
    """
    파일명 안전화: 한글/영문/숫자/.-_만 허용, 나머지 제거
    """
    base = os.path.basename(name or "file.pdf")
    # 확장자 보존
    root, ext = os.path.splitext(base)
    if not ext:
        ext = ".pdf"
    root = re.sub(r"[^0-9A-Za-z가-힣._-]+", "_", root)
    return root[:120] + ext  # 과도한 길이 방지


def _to_dict(doc):
    if not doc:
        return None
    d = dict(doc)
    d["_id"] = str(d["_id"])
    if "user_id" in d and isinstance(d["user_id"], ObjectId):
        d["user_id"] = str(d["user_id"])
    return d


# ─────────────────────────────────────────────────────────────
# 업로드
# ─────────────────────────────────────────────────────────────
@router.post("/{user_id}")
async def upload_pdf(
    user_id: str,
    file: UploadFile = File(..., description="PDF 파일"),
    summary: str = Form("", description="요약 텍스트(선택)"),
):
    """
    Streamlit에서 보내는 멀티파트 요청을 받아
    - 서버 로컬에 파일 저장
    - MongoDB에 문서 메타 기록
    - 저장 경로/문서 id 반환
    """
    uid = _oid(user_id)

    # 콘텐츠 타입/확장자 방어
    content_type = (file.content_type or "").lower()
    if not (content_type == "application/pdf" or file.filename.lower().endswith(".pdf")):
        raise HTTPException(400, "PDF만 업로드 가능합니다.")

    # 안전한 파일명 + 타임스탬프 프리픽스
    safe_name = _slug_filename(file.filename)
    ts = datetime.now(KST).strftime("%Y%m%d_%H%M%S")
    save_name = f"{user_id}_{ts}_{safe_name}"
    save_path = os.path.join(OCR_DIR, save_name)

    # 저장
    try:
        with open(save_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(500, f"파일 저장 실패: {e}")

    # DB 문서 작성
    doc = {
        "user_id": uid,
        "pdf_url": save_path,            # 로컬 경로(상대/절대) 저장
        "regist_at": datetime.now(KST),  # KST 기준
        "summary": summary or "",
    }
    ins = _col().insert_one(doc)

    return {
        "saved": True,
        "inserted_id": str(ins.inserted_id),
        "pdf_url": save_path,           # 프론트가 바로 써야 하면 반환
    }


# ─────────────────────────────────────────────────────────────
# 목록/조회
# ─────────────────────────────────────────────────────────────
@router.get("/{user_id}")
def list_user_docs(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200)
):
    uid = _oid(user_id)
    cur = _col().find({"user_id": uid}).sort("regist_at", -1).skip(skip).limit(limit)
    return {"items": [_to_dict(d) for d in cur]}


@router.get("/detail/{doc_id}")
def get_detail(doc_id: str):
    _id = _oid(doc_id)
    doc = _col().find_one({"_id": _id})
    if not doc:
        raise HTTPException(404, "document not found")
    return _to_dict(doc)


# ─────────────────────────────────────────────────────────────
# 파일 다운로드 (개발 편의)
# ─────────────────────────────────────────────────────────────
@router.get("/download/{doc_id}")
def download_file(doc_id: str):
    _id = _oid(doc_id)
    doc = _col().find_one({"_id": _id})
    if not doc:
        raise HTTPException(404, "document not found")

    path = doc.get("pdf_url")
    if not path or not os.path.exists(path):
        raise HTTPException(404, "file not found on server")

    # 파일명은 저장된 경로에서 추출
    filename = os.path.basename(path)
    return FileResponse(path, media_type="application/pdf", filename=filename)


# ─────────────────────────────────────────────────────────────
# 삭제(문서+파일)
# ─────────────────────────────────────────────────────────────
@router.delete("/{doc_id}")
def delete_doc(doc_id: str):
    _id = _oid(doc_id)
    doc = _col().find_one({"_id": _id})
    if not doc:
        raise HTTPException(404, "document not found")

    path = doc.get("pdf_url")
    _col().delete_one({"_id": _id})

    # 파일도 삭제 (있을 때만)
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            # 파일 삭제 실패는 문서 삭제까지 롤백하지 않음
            pass

    return {"deleted": True, "doc_id": doc_id}


# ─────────────────────────────────────────────────────────────
# 디버그: 현재 사용하는 컬렉션/카운트
# ─────────────────────────────────────────────────────────────
@router.get("/debug/peek")
def peek_docs(n: int = Query(5, ge=1, le=50)):
    col = _col()
    docs = list(col.find({}, {"pdf_url":1, "summary":1, "regist_at":1})
                    .sort([("_id", -1)]).limit(n))
    # ObjectId → str
    for d in docs:
        d["_id"] = str(d["_id"])
    return {
        "db": db.name,
        "collection": OCR_COLL,
        "count": col.estimated_document_count(),
        "latest": docs,
    }

@router.post("/debug/seed")
def seed_one():
    col = _col()
    doc = {
        "user_id": ObjectId("000000000000000000000000"),
        "pdf_url": "debug://seed.pdf",
        "ocr_text": "seed",
        "summary": "seed",
        "regist_at": datetime.utcnow(),
    }
    rid = col.insert_one(doc).inserted_id
    found = col.find_one({"_id": rid}, {"_id":1})
    return {
        "inserted_id": str(rid),
        "found_after_insert": bool(found),
        "db": db.name,
        "collection": OCR_COLL,
        "total_now": col.estimated_document_count(),
    }

@router.get("/latest/{user_id}")
def get_latest_summary(user_id: str, only: str = Query("summary", enum=["summary","full"])):
    coll = _col()
    doc = coll.find_one({"user_id": _oid(user_id)}, sort=[("regist_at", -1)])
    if not doc:
        raise HTTPException(status_code=404, detail="no summary for user")
    if only == "summary":
        return {"_id": str(doc["_id"]), "summary": doc.get("summary", ""), "regist_at": doc.get("regist_at")}
    # full 문서는 ObjectId → str 변환
    doc["_id"] = str(doc["_id"])
    doc["user_id"] = str(doc["user_id"])
    return doc