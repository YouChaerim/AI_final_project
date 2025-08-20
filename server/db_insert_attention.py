# -*- coding: utf-8 -*-
# server/db_insert_attention.py (상단부)
from pymongo import MongoClient
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path
import os, random, uuid

# ✅ server/.env 만 명시적으로 로드
ENV_PATH = Path(__file__).resolve().parent / ".env"
loaded = load_dotenv(ENV_PATH, override=True)
print(f"[dotenv] loaded={loaded}, path={ENV_PATH}")

uri = os.getenv("MONGODB_URI")
if not uri:
    raise RuntimeError(f"server/.env의 MONGODB_URI가 비어있습니다. 경로: {ENV_PATH}")

client = MongoClient(uri)
db = client["ttalk"]

"""
사용법
1) .env에 MONGODB_URI 설정
2) python 이 파일 실행
   - 기본 DB: ttalk
   - 기본 사용자 2명(local) 없으면 생성: test1@email.com, test2@email.com
   - 기간: 2025-04-01 ~ 2025-08-13
   - 평일 1~3세션, 주말 0~2세션

생성/삽입 컬렉션
- sessions: 세션 본문(시작/종료/점수/횟수 등 + 부가 필드)
- session_events: 인터럽트/깜빡임/하품 이벤트 타임라인
- breaks: 세션 중 쉬는 시간
"""

# ====== 설정 ======
START_DATE = datetime(2025, 4, 1)
END_DATE   = datetime(2025, 8, 13)
WEEKDAY_SESSIONS = [1, 1, 2, 2, 3]   # 평일
WEEKEND_SESSIONS = [0, 1, 1, 2]      # 주말
RNG_SEED = 42

SUBJECTS = [
    "알고리즘","자료구조","운영체제","데이터베이스","컴퓨터네트워크",
    "선형대수","확률과통계","AI개론","강화학습","컴퓨터비전",
    "자연어처리","영어회화","기술면접","포트폴리오","프로젝트관리",
    "웹프론트엔드","백엔드","클라우드","리눅스","캡스톤디자인"
]
MODES = ["pomodoro", "deep_work", "group_study"]
LOCATIONS = ["home", "library", "cafe", "school_lab"]
DEVICES = ["macOS", "Windows", "iPad", "Linux"]
TAGS_POOL = ["YOLO", "OCR", "퀴즈", "리포트", "깃", "ERD", "OAuth", "FastAPI", "Streamlit"]
ATTN_MODELS = ["YOLOv8n", "YOLOv8s-attn", "Mediapipe-FaceMesh"]

random.seed(RNG_SEED)

def get_or_create_users():
    """local 사용자 2명을 조회/생성하고 ObjectId 매핑을 반환"""
    emails = ["test1@email.com", "test2@email.com"]
    ids = []
    for email in emails:
        found = db.User.find_one({"provider": "local", "local_user_id": email}, {"_id": 1})
        if found:
            ids.append(found["_id"])
            continue
        # 없으면 간단 생성
        inserted_id = db.User.insert_one({
            "provider": "local",
            "provider_id": None,
            "local_user_id": email,
            "nickname": email.split("@")[0],
            "passwd": "bcrypt_hash",     # 실제 서비스에서는 bcrypt로 해시하세요.
            "created_at": datetime.utcnow(),
            "points": 0,
            "continuous_count": 0
        }).inserted_id
        ids.append(inserted_id)
    return ids  # [ObjectId, ObjectId]

def rand_time_between(h1, m1, h2, m2):
    base = datetime(2025, 1, 1, h1, m1)
    span = int((datetime(2025, 1, 1, h2, m2) - base).total_seconds())
    t = base + timedelta(seconds=random.randint(0, span))
    return t.strftime("%H:%M")

def add_minutes(hhmm, minutes):
    dt = datetime.strptime(hhmm, "%H:%M") + timedelta(minutes=minutes)
    return dt.strftime("%H:%M")

def random_breaks(total_min):
    """세션 중 쉬는 시간(0~2개) 오프셋/지속분/유형"""
    out = []
    remaining = total_min
    cursor = 0
    for _ in range(random.choices([0,1,2],[0.35,0.45,0.2])[0]):
        if remaining < 30:
            break
        study_chunk = random.randint(15, 50)
        cursor += study_chunk
        remaining -= study_chunk
        bmin = random.choice([5,5,10,15])
        out.append({"offset_min": cursor, "duration_min": bmin, "type": random.choice(["short","walk","water"])})
        cursor += bmin
        remaining -= bmin
        if remaining <= 0:
            break
    return out

def gen_interruptions(duration_min):
    types = ["phone","chat","delivery","system_alert"]
    arr = []
    for _ in range(random.choices([0,1,2,3],[0.5,0.3,0.15,0.05])[0]):
        arr.append({
            "minute": random.randint(3, max(3, duration_min-3)),
            "type": random.choice(types)
        })
    return arr

def build_one_session(day, user_oid):
    subject = random.choice(SUBJECTS)
    mode = random.choice(MODES)
    location = random.choice(LOCATIONS)
    device = random.choice(DEVICES)
    attention_model = random.choice(ATTN_MODELS)
    tags = random.sample(TAGS_POOL, k=random.randint(1,3))

    duration = random.choice([25,30,40,45,50,60,75,80,90,120])
    start_hhmm = rand_time_between(6,0,22,0)
    end_hhmm   = add_minutes(start_hhmm, duration)

    # 시작/종료 datetime
    start_dt = datetime(day.year, day.month, day.day, int(start_hhmm[:2]), int(start_hhmm[3:]))
    end_dt   = datetime(day.year, day.month, day.day, int(end_hhmm[:2]),  int(end_hhmm[3:]))

    blink_rate = round(random.uniform(10.0, 22.0), 1)  # 분당 깜빡임
    blink_count = int(round(blink_rate * duration))
    yawn_count  = random.choices([0,1,2,3,4,5],[0.45,0.2,0.15,0.1,0.06,0.04])[0]
    drowsy_events = random.choices([0,1,2],[0.7,0.25,0.05])[0]
    interruptions = gen_interruptions(duration)

    focus_base = random.randint(60, 92)
    focus_penalty = yawn_count*2 + drowsy_events*5 + (2 if interruptions else 0)
    focus_score = max(35, min(99, focus_base - focus_penalty + random.randint(-3,3)))

    avg_yawn = round(random.uniform(0.4, 1.2), 2)  # 하품 평균 지속(초) 대용
    breaks = random_breaks(duration)

    session_doc = {
        # 필수/합의 필드
        "user_id": user_oid,
        "study_date": start_dt,   # 시작 시각
        "end_time": end_dt,       # 종료 시각
        "focus_score": float(focus_score),
        "blink_count": blink_count,
        "yawn_count": yawn_count,
        "avg_yawn": avg_yawn,
        "sum_study_time": float(duration),

        # 추가 메타(원하시면 삭제 가능)
        "subject": subject,
        "mode": mode,
        "location": location,
        "device": device,
        "tags": tags,
        "attention_model": attention_model,
        "drowsy_events": drowsy_events,
        "blink_rate_per_min": blink_rate,
        "notes": random.choice([
            "도중에 카톡으로 잠깐 산만해짐",
            "YOLO 인퍼런스 속도 개선 메모",
            "OCR 정합도 재검증 필요",
            "카페 소음 있음",
            "라이브러리 좌석 좋음",
            "중간에 졸려서 물 마심",
            "훌륭한 집중 상태 유지"
        ]),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),

        # 후속 컬렉션 생성을 위한 원본
        "_gen": {
            "duration_min": duration,
            "start_dt": start_dt,
            "breaks": breaks,
            "interruptions": interruptions,
            "focus_score": focus_score,
            "yawn_count": yawn_count
        }
    }
    return session_doc

def main():
    user_oids = get_or_create_users()
    all_sessions = []
    day = START_DATE
    while day <= END_DATE:
        n = random.choice(WEEKDAY_SESSIONS) if day.weekday() < 5 else random.choice(WEEKEND_SESSIONS)
        for _ in range(n):
            all_sessions.append(build_one_session(day, random.choice(user_oids)))
        day += timedelta(days=1)

    # 1) sessions 먼저 insert
    if not all_sessions:
        print("생성된 세션이 없습니다.")
        return
    res = db.sessions.insert_many([{k:v for k,v in s.items() if k != "_gen"} for s in all_sessions], ordered=False)
    inserted_ids = res.inserted_ids

    # 2) breaks / session_events 만들기
    breaks_docs = []
    events_docs = []
    for s, s_id in zip(all_sessions, inserted_ids):
        g = s["_gen"]
        start_dt = g["start_dt"]
        # breaks
        for b in g["breaks"]:
            st = start_dt + timedelta(minutes=b["offset_min"])
            et = st + timedelta(minutes=b["duration_min"])
            reason_map = {"short":"short_break", "walk":"walk", "water":"water"}
            breaks_docs.append({
                "session_id": s_id,
                "start_time": st,
                "end_time": et,
                "reason": reason_map.get(b["type"], "break"),
                "focus_score": float(g["focus_score"])
            })

        # interruptions -> session_events
        for it in g["interruptions"]:
            ts = start_dt + timedelta(minutes=it["minute"])
            events_docs.append({
                "session_id": s_id,
                "timestamp": ts,
                "event_type": it["type"],     # phone/chat/delivery/system_alert
                "attention": max(0.0, min(100.0, float(g["focus_score"] - random.randint(5,15)))),
                "yawn_weight": round(random.uniform(0.3, 1.1), 2)
            })

        # 추가로 blink / yawn 이벤트도 조금씩 생성 (보기 좋게)
        # blink 이벤트: 세션당 3~6개
        for i in range(random.randint(3,6)):
            ts = start_dt + timedelta(minutes=random.randint(1, max(1, g["duration_min"]-1)))
            events_docs.append({
                "session_id": s_id,
                "timestamp": ts,
                "event_type": "blink",
                "attention": max(0.0, min(100.0, float(g["focus_score"] + random.randint(-4,4)))),
                "yawn_weight": 0.0
            })
        # yawn 이벤트: yawn_count 만큼(최대 5로 제한)
        for i in range(min(g["yawn_count"], 5)):
            ts = start_dt + timedelta(minutes=random.randint(1, max(1, g["duration_min"]-1)))
            events_docs.append({
                "session_id": s_id,
                "timestamp": ts,
                "event_type": "yawn",
                "attention": max(0.0, min(100.0, float(g["focus_score"] - random.randint(3,10)))),
                "yawn_weight": round(random.uniform(0.5, 1.2), 2)
            })

    if breaks_docs:
        db.breaks.insert_many(breaks_docs, ordered=False)
    if events_docs:
        db.session_events.insert_many(events_docs, ordered=False)

    print("✅ 완료")
    print(f"- sessions:       {len(inserted_ids)} 건")
    print(f"- breaks:         {len(breaks_docs)} 건")
    print(f"- session_events: {len(events_docs)} 건")

if __name__ == "__main__":
    main()
