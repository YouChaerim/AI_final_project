# server/app.py
# 실행:  python -m uvicorn server.app:app --reload --host 0.0.0.0 --port 8080
import os
from fastapi import FastAPI
from .server_db import db
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from server import kakao_sign, local_sign, todos, memos, study_time, ocr_files, study_sessions, quizzes, reports, ranking, shop

app = FastAPI(title="ttalk API", version="0.1.0")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8501")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 👉 라우터 마운트(엔드포인트는 각 파일 내부에만 존재)
app.include_router(local_sign.router)
app.include_router(kakao_sign.router)
app.include_router(todos.router)
app.include_router(memos.router)
app.include_router(study_time.router)
app.include_router(ocr_files.router)
app.include_router(study_sessions.router)
app.include_router(quizzes.router)
app.include_router(reports.router)
app.include_router(ranking.router)
app.include_router(shop.router)

@app.get("/health")
def health():
    return {"status": "ok"}

# (선택) 환경변수 디버그
@app.get("/auth/kakao/debug")
def kakao_debug():
    cid = (os.getenv("KAKAO_CLIENT_ID") or "")[:6] + "..."
    return {
        "client_id": cid,
        "redirect_uri": os.getenv("KAKAO_REDIRECT_URI"),
        "frontend_url": FRONTEND_URL,
    }

BASE_DIR = os.path.dirname(__file__)
STATIC_ROOT = os.path.join(BASE_DIR, "uploads")
os.makedirs(STATIC_ROOT, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_ROOT), name="static")


@app.get("/debug/db")
def debug_db():
    import os, re
    uri = os.getenv("MONGODB_URI") or os.getenv("MONGO_URL") or ""
    uri_masked = re.sub(r"//([^:]+):([^@]+)@", r"//\1:****@", uri) if uri else ""
    return {
        "db": db.name,
        "collections": sorted(db.list_collection_names()),
        "uri": uri_masked,
    }