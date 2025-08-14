# server/app.py
# 실행:  python -m uvicorn server.app:app --reload --host 0.0.0.0 --port 8080
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server import kakao_sign, local_sign

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
