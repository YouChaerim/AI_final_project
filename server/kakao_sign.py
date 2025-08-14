# server/kakao_sign.py
from fastapi import APIRouter
from fastapi.responses import RedirectResponse, JSONResponse
from urllib.parse import quote_plus
from server.common_sign import db, now_kst, bump_streak_and_touch
from dotenv import load_dotenv
import os, requests

load_dotenv()

KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL")

router = APIRouter(prefix="/auth/kakao", tags=["kakao-auth"])

@router.get("/login")
def kakao_login():
    url = (
        "https://kauth.kakao.com/oauth/authorize"
        f"?client_id={KAKAO_CLIENT_ID}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=profile_nickname"
        f"&prompt=select_account"
    )
    return RedirectResponse(url, status_code=302)

@router.get("/callback")
def kakao_callback(code: str):
    token_res = requests.post(
        "https://kauth.kakao.com/oauth/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "client_id": KAKAO_CLIENT_ID,
            "client_secret": KAKAO_CLIENT_SECRET,
            "redirect_uri": KAKAO_REDIRECT_URI,
            "code": code,
        }, timeout=10
    )
    if not token_res.ok:
        return JSONResponse({"error": "token_request_failed", "detail": token_res.text}, status_code=400)
    access_token = token_res.json().get("access_token")
    if not access_token:
        return JSONResponse({"error": "no_access_token"}, status_code=400)

    profile_res = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10
    )
    if not profile_res.ok:
        return JSONResponse({"error": "profile_request_failed", "detail": profile_res.text}, status_code=400)
    p = profile_res.json()

    kakao_id = p.get("id")
    if kakao_id is None:
        return JSONResponse({"error": "no_kakao_id", "detail": p}, status_code=400)

    acc = (p.get("kakao_account") or {})
    prof = (acc.get("profile") or {})
    nickname = prof.get("nickname") or (p.get("properties", {}) or {}).get("nickname") or f"user_{kakao_id}"

    user = db.User.find_one({"provider": "kakao", "provider_id": int(kakao_id)})
    if not user:
        db.User.insert_one({
            "provider": "kakao",
            "provider_id": int(kakao_id),
            "local_user_id": None,
            "nickname": nickname,
            "passwd": None,
            "created_at": now_kst(),
            "points": 0,
            "continuous_count": 0,
            "last_login_log": now_kst(),
        })
    else:
        bump_streak_and_touch(user)
        db.User.update_one({"_id": user["_id"]}, {"$set": {"nickname": nickname}})

    n = quote_plus(nickname or "")
    return RedirectResponse(
        f"{FRONTEND_URL}/login_page?login=success&provider=kakao&uid={int(kakao_id)}&nickname={n}",
        status_code=302
    )
