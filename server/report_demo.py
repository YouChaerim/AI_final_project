try:
    # 패키지로 실행: python -m server.report_demo
    from .server_db import db
except Exception:
    # 스크립트로 실행: cd server && python report_demo.py
    from server_db import db

from pymongo import ReturnDocument

Users = db["User"]
Shop  = db["shop"]

def main():
    Users.update_many({"points": {"$exists": False}}, {"$set": {"points": 0}})
    Users.update_many({"active_char": {"$exists": False}}, {"$set": {"active_char": "ddalkkak"}})

    try:
        Shop.create_index("user_id", unique=True)
    except Exception:
        pass

    for u in Users.find({}, {"_id": 1}):
        uid = str(u["_id"])
        Shop.update_one(
            {"user_id": uid},
            {"$setOnInsert": {"owned_chars": []}},
            upsert=True
        )
    print("✅ Migration done.")

if __name__ == "__main__":
    main()