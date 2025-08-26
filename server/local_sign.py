# server/local_sign.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from server.common_sign import db, hash_pw, verify_pw, now_kst, bump_streak_and_touch

router = APIRouter(prefix="/auth/local", tags=["local-auth"])

class LocalSignupIn(BaseModel): user_id: str; password: str; nickname: Optional[str] = None
class LocalLoginIn(BaseModel): user_id: str; password: str

@router.get("/check-id/{user_id}")
def check_id_duplicate(user_id: str):
    if db.User.find_one({"provider": "local", "local_user_id": user_id}): return {"exists": True}
    return {"exists": False}

@router.get("/check-nickname/{nickname}")
def check_nickname_duplicate(nickname: str):
    if db.User.find_one({"nickname": nickname}): return {"exists": True}
    return {"exists": False}

@router.post("/signup")
def local_signup(body: LocalSignupIn):
    uid, pw = (body.user_id or "").strip(), (body.password or "")
    if not uid or not pw: return {"result": "error", "error": "invalid_input"}
    if db.User.find_one({"provider": "local", "local_user_id": uid}): return {"result": "error", "error": "user_exists"}
    nick = (body.nickname or uid).strip()
    if db.User.find_one({"nickname": nick}): return {"result": "error", "error": "nickname_exists"}
    doc = { "provider": "local", "provider_id": 0, "local_user_id": uid, "nickname": nick, "passwd": hash_pw(pw), "created_at": now_kst(), "points": 0, "continuous_count": 0, "last_login_log": now_kst() }
    db.User.insert_one(doc)
    return {"result": "ok", "user": {"provider": "local", "local_user_id": uid, "nickname": nick}}

@router.post("/login")
def local_login(body: LocalLoginIn):
    uid, pw = (body.user_id or "").strip(), (body.password or "")
    user = db.User.find_one({"provider": "local", "local_user_id": uid})
    if not user or not user.get("passwd"): return {"result": "error", "error": "not_found"}
    if not verify_pw(pw, user["passwd"]): return {"result": "error", "error": "wrong_password"}
    bump_streak_and_touch(user)
    fresh = db.User.find_one({"_id": user["_id"]})
    return {
        "result": "ok",
        "user": {
            "id": str(fresh["_id"]), # 👈 [수정] 로그인 성공 시 ObjectId 반환
            "provider": "local",
            "local_user_id": uid,
            "nickname": fresh.get("nickname", uid),
            "continuous_count": fresh.get("continuous_count", 0),
        },
    }