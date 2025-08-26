# server/seed_ranking.py

from datetime import datetime, timedelta, timezone
from bson import ObjectId
from pymongo import MongoClient, UpdateOne
import os, random
from pathlib import Path
from dotenv import load_dotenv

SERVER_ENV = Path(__file__).resolve().parent / ".env"
load_dotenv(SERVER_ENV, override=True)

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB  = os.getenv("MONGODB_DB", "ttalk")
KST = timezone(timedelta(hours=9))
rnd = random.Random(123)

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]
Users  = db["User"]
Points = db["points"]

print(f"Seeding to {MONGODB_URI} / DB={MONGODB_DB}")

# --- (A) 기존 잘못 들어간 demo 유저 수리: provider_id 비어있으면 _id 문자열로 채움 ---
fix_targets = list(Users.find(
    {"provider": "demo", "$or": [{"provider_id": None}, {"provider_id": {"$exists": False}}]},
    {"_id": 1}
))
for doc in fix_targets:
    Users.update_one({"_id": doc["_id"]}, {"$set": {"provider_id": str(doc["_id"])}})
if fix_targets:
    print(f"fixed demo users: {len(fix_targets)}")

NAMES = [
    "소지섭","유유유유유윤","상혁","똑깡아아야","민서","지우","다온","크림림","dbwngus",
    "차은상","채원","아라","준호","가온","별하","하린","주호","예린","수호"
]

# --- (B) demo 유저 생성 시 provider_id를 고유값으로 반드시 넣기 ---
def ensure_users(names):
    user_ids = []
    for name in names:
        # 닉네임이 이미 있으면 재사용
        u = Users.find_one({"nickname": name}, {"_id": 1})
        if u:
            user_ids.append(u["_id"])
            continue

        uid = ObjectId()
        Users.update_one(
            {"provider": "demo", "provider_id": str(uid)},   # 고유 쌍으로 upsert
            {"$setOnInsert": {
                "_id": uid,
                "provider": "demo",
                "provider_id": str(uid),
                "nickname": name,
                "points": 0,
                "created_at": datetime.now(KST),
            }},
            upsert=True
        )
        user_ids.append(uid)
    return user_ids

user_ids = ensure_users(NAMES)

# 이하 기존 로직 그대로 …
start = datetime(2025,4,24,tzinfo=KST)
end   = datetime(2025,8,25,tzinfo=KST)
days = (end - start).days

ops = []
balance_delta = {uid: 0 for uid in user_ids}
def kst(y,m,d,h=0,mi=0): return datetime(y,m,d,h,mi,tzinfo=KST)

for uid in user_ids:
    for i in range(days):
        cur = start + timedelta(days=i)
        y,m,d = cur.year, cur.month, cur.day
        iso = f"{y:04d}-{m:02d}-{d:02d}"

        present = rnd.random() < rnd.uniform(0.55, 0.75)
        if present:
            att_doc = {
                "user_id": uid,
                "gain_date": kst(y,m,d,8,5),
                "point": 10,
                "reason": f"ATTENDANCE#{iso}",
            }
            ops.append(UpdateOne(
                {"user_id": uid, "reason": att_doc["reason"]},
                {"$setOnInsert": att_doc}, upsert=True
            ))
            balance_delta[uid] += 10

            if rnd.random() < 0.65:
                gain = rnd.choice([15,20,30,40,50])
                base = rnd.choice(["QUIZ","BET_REWARD","FOCUS_BONUS"])
                rew = {
                    "user_id": uid,
                    "gain_date": kst(y,m,d,21,10),
                    "point": gain,
                    "reason": f"{base}#{iso}",
                }
                ops.append(UpdateOne(
                    {"user_id": uid, "reason": rew["reason"]},
                    {"$setOnInsert": rew}, upsert=True
                ))
                balance_delta[uid] += gain

        if rnd.random() < 0.12:
            stake = -rnd.choice([20,40,60])
            bet = {
                "user_id": uid,
                "gain_date": kst(y,m,d,19,55),
                "point": stake,
                "reason": f"BET_START#{iso}",
            }
            ops.append(UpdateOne(
                {"user_id": uid, "reason": bet["reason"]},
                {"$setOnInsert": bet}, upsert=True
            ))
            balance_delta[uid] += stake

if ops:
    Points.bulk_write(ops, ordered=False)

for uid, delta in balance_delta.items():
    if delta:
        Users.update_one({"_id": uid}, {"$inc": {"points": delta}})

print(f"✅ seeded users={len(user_ids)}, ops={len(ops)}")
