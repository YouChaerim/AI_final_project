from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
from zoneinfo import ZoneInfo
import bcrypt, os

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client["ttalk"]

KST = ZoneInfo("Asia/Seoul")

def now_kst():
    return datetime.now(KST)

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_pw(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def bump_streak_and_touch(user_doc: dict):
    """last_login_log 기준 연속출석 갱신 + 로그인 시각 업데이트"""
    today = now_kst().date()
    inc_ops = {}
    prev_dt = user_doc.get("last_login_log")
    if prev_dt:
        prev_day = prev_dt.astimezone(KST).date()
        delta = (today - prev_day).days
        if delta == 1:
            inc_ops["$inc"] = {"continuous_count": 1}
        elif delta > 1:
            inc_ops["$set"] = {**inc_ops.get("$set", {}), "continuous_count": 0}
    base_set = {"last_login_log": now_kst()}
    db.User.update_one({"_id": user_doc["_id"]},
                       {**({"$set": base_set}), **inc_ops} if inc_ops else {"$set": base_set})
