# server/server_db.py
import os
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv
from urllib.parse import urlparse

# ✅ server 폴더(이 파일과 같은 폴더)에 있는 .env를 우선 로드
SERVER_ENV = Path(__file__).resolve().parent / ".env"
load_dotenv(SERVER_ENV, override=True)

# (선택) 루트 .env는 값이 비어있는 항목만 채우도록 보조 로드
ROOT_ENV = Path(__file__).resolve().parents[1] / ".env"
if ROOT_ENV.exists():
    load_dotenv(ROOT_ENV, override=False)

MONGODB_URI = os.getenv("MONGODB_URI") or None
MONGODB_DB  = os.getenv("MONGODB_DB", "ttalk")

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI가 비어 있습니다. server/.env를 확인하세요.")

# 연결 확인을 빨리 실패시키기
client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
client.admin.command("ping")  # 연결 실패 시 여기서 예외

db = client[MONGODB_DB]

try:
    host = urlparse(MONGODB_URI).hostname or "(unknown)"
except Exception:
    host = "(unknown)"
print(f"[DB] connected host={host} db={db.name}")
