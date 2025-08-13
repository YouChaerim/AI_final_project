# server/app.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 메인 FastAPI 앱
app = FastAPI(title="ttalk API", version="0.1.0")

# CORS (Streamlit 로컬 접근 허용)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8501")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:8501", "http://127.0.0.1:8501", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- 라우터 결합 ----
# kakao_sign.py / local_sign.py 가
#  1) router = APIRouter(...) 를 노출하거나
#  2) app = FastAPI(...) 를 노출할 수 있으니 둘 다 지원
from server import kakao_sign, local_sign  # noqa: F401

# local
if hasattr(local_sign, "router"):
    app.include_router(local_sign.router)
elif hasattr(local_sign, "app"):
    app.include_router(local_sign.app.router)

# kakao
if hasattr(kakao_sign, "router"):
    app.include_router(kakao_sign.router)
elif hasattr(kakao_sign, "app"):
    app.include_router(kakao_sign.app.router)

# 헬스체크
@app.get("/health")
def health():
    return {"status": "ok"}
