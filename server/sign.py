from fastapi import FastAPI
from fastapi.responses import RedirectResponse, JSONResponse
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime
import requests

# .env에서 환경변수 로드
load_dotenv()

# 환경변수 불러오기
MONGODB_URI = os.getenv("MONGODB_URI")
KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")

# MongoDB 연결
client = MongoClient(MONGODB_URI)
db = client["ttalk"]         # 사용할 DB명

app = FastAPI()

# 1. 카카오 로그인 페이지로 리다이렉트
@app.get("/auth/kakao/login")
def kakao_login():
    kakao_auth_url = (
        "https://kauth.kakao.com/oauth/authorize"
        f"?client_id={KAKAO_CLIENT_ID}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}"
        f"&response_type=code"
    )
    return RedirectResponse(kakao_auth_url)

# 2. 카카오 콜백(인증코드 → 토큰, 프로필 → DB저장)
@app.get("/auth/kakao/callback")
def kakao_callback(code: str):
    # 2-1. 토큰 발급 요청
    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_CLIENT_ID,
        "client_secret": KAKAO_CLIENT_SECRET,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": code,
    }
    token_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_res = requests.post(token_url, data=token_data, headers=token_headers)
    token_json = token_res.json()

    # 토큰 발급 실패 시
    if "access_token" not in token_json:
        return JSONResponse(token_json, status_code=400)

    access_token = token_json["access_token"]

    # 2-2. 사용자 정보 요청
    profile_url = "https://kapi.kakao.com/v2/user/me"
    profile_headers = {"Authorization": f"Bearer {access_token}"}
    profile_res = requests.get(profile_url, headers=profile_headers)
    profile_json = profile_res.json()

    # 2-3. DB에 저장할 값 추출 (kakao id, nickname, email 등)
    kakao_id = profile_json["id"]   # (숫자)
    nickname = profile_json["kakao_account"]["profile"]["nickname"]
    email = profile_json["kakao_account"].get("email")   # 허용 안하면 None

    # 2-4. 이미 가입된 유저인지 확인 (provider, provider_id 조합으로)
    user = db.User.find_one({"provider": "kakao", "provider_id": str(kakao_id)})

    # 2-5. 유저가 없다면 새로 저장
    if not user:
        user_doc = {
            "provider": "kakao",
            "provider_id": str(kakao_id),
            "nickname": nickname,
            "email": email,
            "created_at": datetime.utcnow(),
            "points": 0,
            "continuous_count": 0
        }
        db.User.insert_one(user_doc)
        user = user_doc

    # (실서비스라면 여기서 JWT발급/세션생성/리다이렉트 등 처리)
    return JSONResponse({
        "result": "ok",
        "user": {
            "provider": user["provider"],
            "provider_id": user["provider_id"],
            "nickname": user["nickname"],
            "email": user.get("email")
        }
    })
