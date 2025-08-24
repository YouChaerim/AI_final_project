# server/common_sign.py
from .server_db import db
from pymongo import MongoClient
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import bcrypt, os, pytz
from bson import ObjectId

load_dotenv()

server_env = Path(__file__).parent / ".env"
if server_env.exists():
    load_dotenv(server_env, override=True)

MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db = client["ttalk"]

KST = ZoneInfo("Asia/Seoul")
def now_kst(): return datetime.now(KST)

def hash_pw(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_pw(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def bump_streak_and_touch(user_doc: dict):
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
    db.User.update_one(
        {"_id": user_doc["_id"]},
        {**({"$set": base_set}), **inc_ops} if inc_ops else {"$set": base_set},
    )

def sync_streak_on_login(user_id):
    oid = ObjectId(user_id) if isinstance(user_id, str) else user_id
    today = datetime.now(KST).date()
    yesterday = today - timedelta(days=1)

    # 가장 최근 출석(ATTEND_YYYY-MM-DD) 찾기
    last = db.points.find_one(
        {"user_id": oid, "reason": {"$regex": r"^ATTEND_\d{4}-\d{2}-\d{2}$"}},
        sort=[("gain_date", -1)]
    )
    if not last:
        db.users.update_one({"_id": oid}, {"$set": {"continuous_count": 0}})
        return

    last_day = last["gain_date"].astimezone(KST).date()
    # 전날을 건너뛰었으면 streak 끊김
    if last_day < yesterday:
        db.users.update_one({"_id": oid}, {"$set": {"continuous_count": 0}})