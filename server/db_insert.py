from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

uri = os.getenv("MONGODB_URI")
client = MongoClient(uri)
db = client["ttalk"]

# # 2. 사용자(user) 샘플 insert
# user_id = db.User.insert_one({
#     "provider": "local",
#     "provider_id": None,        # 로컬 가입이므로 None
#     "local_user_id": "test1@email.com",
#     "nickname": "테스터",
#     "passwd": "bcrypt_hash",
#     "created_at": datetime.utcnow(),
#     "points": 0,
#     "continuous_count": 3
# }).inserted_id

# # 3. 세션(sessions) 샘플 insert
# session_id = db.sessions.insert_one({
#     "user_id": user_id,
#     "study_date": datetime(2024, 8, 6, 9, 0),      # 시작 시각
#     "end_time": datetime(2024, 8, 6, 10, 0),
#     "focus_score": 82.4,
#     "blink_count": 10,
#     "yawn_count": 2,
#     "avg_yawn": 0.6,
#     "sum_study_time": 60.0
# }).inserted_id

# # 4. 타임라인 로그(session_events) 샘플 insert
# db.session_events.insert_one({
#     "session_id": session_id,
#     "timestamp": datetime(2024, 8, 6, 9, 30),
#     "event_type": "blink",
#     "attention": 80.0,
#     "yawn_weight": 0.5
# })

# # 5. 쉬는시간(breaks) 샘플 insert
# db.breaks.insert_one({
#     "session_id": session_id,
#     "start_time": datetime(2024, 8, 6, 9, 30),
#     "end_time": datetime(2024, 8, 6, 9, 35),
#     "reason": "focus_drop",
#     "focus_score": 60.2
# })

# # 6. 필기 OCR(writin_ocr) 샘플 insert
# db.writin_ocr.insert_one({
#     "user_id": user_id,
#     "pdf_url": "https://fileurl/sample.pdf",
#     "ocr_text": "파이썬은 쉬운 언어입니다.",
#     "regist_at": datetime.utcnow(),
#     "summary": "파이썬의 장점 요약"
# })

# # 7. 퀴즈(quizzes) 샘플 insert (객관식)
# db.quizzes.insert_one({
#     "user_id": user_id,
#     "quiz_type": "ocr",
#     "quiz": {
#         "quiz_text": "파이썬의 대표 자료구조는?",
#         "answer": "리스트",
#         "choices": ["리스트", "배열", "집합", "튜플"]
#     },
#     "user_answer": "리스트",
#     "is_correct": True,
#     "bet_point": 10,
#     "reward_point": 12,
#     "created_at": datetime.utcnow()
# })

# # 8. 목표(goals) 샘플 insert
# db.goals.insert_one({
#     "user_id": user_id,
#     "goal_type": "study_time",
#     "target_value": 90,
#     "bet_point": 20,
#     "achieved": False,
#     "set_date": datetime.utcnow()
# })

# # 9. 포인트(points) 샘플 insert
# db.points.insert_one({
#     "user_id": user_id,
#     "gain_date": datetime.utcnow(),
#     "point": 12,
#     "reason": "session"
# })

# # 10. 메모(memo) 샘플 insert
# db.memo.insert_one({
#     "user_id": user_id,
#     "contests": "오늘 목표: 2시간 집중 공부!",
#     "created_at": datetime.utcnow()
# })

# # 11. 할일(todo) 샘플 insert
# db.todo.insert_one({
#     "user_id": user_id,
#     "contents": "수학 챕터3 복습",
#     "complete": False,
#     "todo_date": datetime.utcnow()
# })

# print("✅ 샘플 데이터 insert 완료!")


from server.common_sign import db, hash_pw, now_kst

UID  = "yu@gmail.com"
PW   = "123"
NICK = "유저"

# 로컬 계정은 (provider, local_user_id)로 식별
db.User.update_one(
    {"provider": "local", "local_user_id": UID},
    {
        "$set": {
            "provider": "local",
            "provider_id": 0,            # null 말고 0으로 통일
            "local_user_id": UID,
            "nickname": NICK,
            "passwd": hash_pw(PW),
            "last_login_log": now_kst(),
        },
        "$setOnInsert": {
            "created_at": now_kst(),
            "points": 0,
            "continuous_count": 0,
        },
    },
    upsert=True,
)

print("✅ 로컬 계정 upsert 완료:", UID)