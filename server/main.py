from fastapi import FastAPI
from fastapi.responses import RedirectResponse, JSONResponse
import os
from dotenv import load_dotenv
import requests

load_dotenv()  # .env 파일 읽기

KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")   # ← 시크릿키도 환경변수로!
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")

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

# 2. 카카오에서 인증코드 받아서 토큰/프로필 요청
@app.get("/auth/kakao/callback")
def kakao_callback(code: str):
    # 2-1. 토큰 발급
    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_CLIENT_ID,
        "client_secret": KAKAO_CLIENT_SECRET,  # ← 시크릿키 추가!
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": code,
    }
    token_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_res = requests.post(token_url, data=token_data, headers=token_headers)
    token_json = token_res.json()

    if "access_token" not in token_json:
        return JSONResponse(token_json, status_code=400)

    access_token = token_json["access_token"]

    # 2-2. 사용자 정보 요청
    profile_url = "https://kapi.kakao.com/v2/user/me"
    profile_headers = {"Authorization": f"Bearer {access_token}"}
    profile_res = requests.get(profile_url, headers=profile_headers)
    profile_json = profile_res.json()

    # ★ 데모: 유저 정보 JSON 그대로 반환 (실서비스에선 JWT/세션/리다이렉트 처리!)
    return JSONResponse(profile_json)
