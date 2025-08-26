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
USER_ID   = ObjectId("68a57b61743df4d021f534d2")  # ← 너 DB의 _id
KST = timezone(timedelta(hours=9))
rnd = random.Random(42)

def kst(y,m,d,h=0,mi=0):
    return datetime(y, m, d, h, mi, tzinfo=KST)

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]
Users  = db["User"]
Points = db["points"]
Sess   = db["sessions"]
SEvt   = db["session_events"]
Breaks = db["breaks"]

start = datetime(2025, 4, 24, tzinfo=KST)
end   = datetime(2025, 8, 25, tzinfo=KST)  # end-exclusive

# 사용자 기본 포인트 필드 확보
Users.update_one({"_id": USER_ID}, {"$setOnInsert": {"points": 0}}, upsert=True)

points_to_upsert = []   # UpdateOne upsert 작업들
bulk_events = []
bulk_breaks = []

cur = start
total_delta = 0

while cur < end:
    y, m, d = cur.year, cur.month, cur.day
    iso_day = f"{y:04d}-{m:02d}-{d:02d}"

    # 60% 확률로 학습(=출석)한 날
    present = rnd.random() < 0.60
    if present:
        # 출석 포인트 +10  (reason에 날짜 suffix 추가)
        att_doc = {
            "user_id": USER_ID,
            "gain_date": kst(y, m, d, 8, 5),
            "point": 10,
            "reason": f"ATTENDANCE#{iso_day}",
        }
        points_to_upsert.append(
            UpdateOne(
                {"user_id": USER_ID, "reason": att_doc["reason"]},
                {"$setOnInsert": att_doc},
                upsert=True
            )
        )
        total_delta += 10

        # 세션 1~3개 생성 (각 25~55분)
        for _ in range(rnd.randint(1, 3)):
            hh = rnd.choice([9, 10, 14, 15, 20, 21])
            mm = rnd.choice([0, 15, 30, 45])
            minutes = rnd.randint(25, 55)
            s = kst(y, m, d, hh, mm)
            e = s + timedelta(minutes=minutes)

            focus_score = rnd.randint(65, 95)
            blink_cnt = rnd.randint(1, 6)
            yawn_cnt  = rnd.randint(0, 4)

            session_doc = {
                "user_id": USER_ID,
                "study_date": s,        # 시작
                "end_time":   e,        # 종료
                "focus_score": float(focus_score),
                "blink_count": int(blink_cnt),
                "yawn_count":  int(yawn_cnt),
                "avg_yawn":    float(max(0.0, yawn_cnt / max(1, minutes/25))),  # 대략값
                "sum_study_time": float(minutes),  # 분 단위 총 학습시간
            }
            sid = Sess.insert_one(session_doc).inserted_id

            # 쉬는 시간(0~1개) – breaks
            if rnd.random() < 0.40:
                b_len = rnd.randint(3, 10)
                # 쉬는 시작이 세션 길이를 넘지 않도록 clamp
                max_start_off = max(1, minutes - 5)
                b_start = s + timedelta(minutes=rnd.randint(10, max_start_off))
                b_end   = b_start + timedelta(minutes=b_len)
                bulk_breaks.append({
                    "session_id": sid,
                    "start_time": b_start,
                    "end_time":   b_end,
                    "reason": rnd.choice(["manual", "focus_drop"]),
                    "focus_score": float(rnd.randint(50, 85)),
                })

            # 세션 이벤트(0~3개) – session_events
            for _ in range(rnd.randint(0, 3)):
                et = rnd.choice(["blink", "yawn", "focus_drop"])
                ts = s + timedelta(minutes=rnd.randint(0, minutes))
                bulk_events.append({
                    "session_id": sid,
                    "timestamp": ts,
                    "event_type": et,
                    "attention": float(rnd.randint(40, 95)),
                    "yawn_weight": float(rnd.choice([0.0, 0.5, 1.0, 1.5])),
                })

        # 퀴즈/배팅/포커스 보상(+)  (reason에 날짜 suffix 추가)
        if rnd.random() < 0.70:
            gain = rnd.choice([15, 20, 30, 40, 50])
            base_reason = rnd.choice(["QUIZ", "BET_REWARD", "FOCUS_BONUS"])
            rew_doc = {
                "user_id": USER_ID,
                "gain_date": kst(y, m, d, 21, 10),
                "point": gain,
                "reason": f"{base_reason}#{iso_day}",
            }
            points_to_upsert.append(
                UpdateOne(
                    {"user_id": USER_ID, "reason": rew_doc["reason"]},
                    {"$setOnInsert": rew_doc},
                    upsert=True
                )
            )
            total_delta += gain

    # 배팅 시작(차감, −) — reason에 날짜 suffix 부여
    if rnd.random() < 0.15:
        stake = -rnd.choice([20, 40, 60])
        bet_doc = {
            "user_id": USER_ID,
            "gain_date": kst(y, m, d, 19, 55),
            "point": stake,
            "reason": f"BET_START#{iso_day}",
        }
        points_to_upsert.append(
            UpdateOne(
                {"user_id": USER_ID, "reason": bet_doc["reason"]},
                {"$setOnInsert": bet_doc},
                upsert=True
            )
        )
        total_delta += stake

    cur += timedelta(days=1)

# 벌크 쓰기
if bulk_breaks:
    Breaks.insert_many(bulk_breaks, ordered=False)
if bulk_events:
    SEvt.insert_many(bulk_events, ordered=False)
if points_to_upsert:
    Points.bulk_write(points_to_upsert, ordered=False)  # ← upsert로 중복 에러 회피

# 사용자 잔액 반영
Users.update_one({"_id": USER_ID}, {"$inc": {"points": total_delta}})
print(
    f"✅ Seeded points(upserts)={len(points_to_upsert)}, "
    f"sessions={Sess.count_documents({'user_id': USER_ID})}, "
    f"events={len(bulk_events)}, breaks={len(bulk_breaks)}, delta={total_delta}"
)
