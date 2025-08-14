# server/local_sign.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from server.common_sign import db, hash_pw, verify_pw, now_kst, bump_streak_and_touch

router = APIRouter(prefix="/auth/local", tags=["local-auth"])

class LocalSignupIn(BaseModel):
    user_id: str
    password: str
    nickname: Optional[str] = None

class LocalLoginIn(BaseModel):
    user_id: str
    password: str

@router.post("/signup")
def local_signup(body: LocalSignupIn):
    uid = (body.user_id or "").strip()
    pw  = (body.password or "")
    if not uid or not pw:
        return {"result": "error", "error": "invalid_input"}

    if db.User.find_one({"provider": "local", "local_user_id": uid}):
        return {"result": "error", "error": "user_exists"}

    nick = (body.nickname or uid).strip()
    doc = {
        "provider": "local",
        "provider_id": 0,               # 로컬은 0으로 고정
        "local_user_id": uid,
        "nickname": nick,
        "passwd": hash_pw(pw),
        "created_at": now_kst(),
        "points": 0,
        "continuous_count": 0,
        "last_login_log": now_kst(),
    }
    db.User.insert_one(doc)
    return {"result": "ok", "user": {"provider": "local", "local_user_id": uid, "nickname": nick}}

@router.post("/login")
def local_login(body: LocalLoginIn):
    uid = (body.user_id or "").strip()
    pw  = (body.password or "")
    user = db.User.find_one({"provider": "local", "local_user_id": uid})
    if not user or not user.get("passwd"):
        return {"result": "error", "error": "not_found"}
    if not verify_pw(pw, user["passwd"]):
        return {"result": "error", "error": "wrong_password"}

    bump_streak_and_touch(user)
    fresh = db.User.find_one({"_id": user["_id"]})
    return {
        "result": "ok",
        "user": {
            "provider": "local",
            "local_user_id": uid,
            "nickname": fresh.get("nickname", uid),
            "continuous_count": fresh.get("continuous_count", 0),
        },
    }
