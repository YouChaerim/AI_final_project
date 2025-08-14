# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer
import av
import cv2
import os, json, time
from collections import deque
from datetime import datetime

# === 성능 튜닝(가급적 최상단) ===
cv2.setNumThreads(1)   # OpenCV 내부 스레드 경합 줄이기

# ===== YOLO =====
try:
    from ultralytics import YOLO
except Exception as e:
    st.error("⚠️ ultralytics( YOLO ) 모듈이 없습니다. 가상환경(파이썬3.10)에서 `pip install ultralytics opencv-python numpy<2` 후 다시 실행하세요.")
    st.stop()

# ===== 페이지/테마 세팅 =====
st.set_page_config(page_title="딸깍공 - 공부 집중모드 (YOLO 기반)", layout="wide", initial_sidebar_state="collapsed")

if "user_data" not in st.session_state:
    if os.path.exists("user_data.json"):
        with open("user_data.json", "r", encoding="utf-8") as f:
            st.session_state.user_data = json.load(f)
    else:
        st.session_state.user_data = {"dark_mode": False, "coins": 500}

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = st.session_state.user_data.get("dark_mode", False)

if st.session_state.dark_mode:
    bg_color = "#1C1C1E"; font_color = "#F2F2F2"
    nav_bg = "#2C2C2E"; card_bg = "#2C2C2E"; hover_bg = "#3A3A3C"
    dark_orange = "#FF9330"
else:
    bg_color = "#FAFAFA"; font_color = "#333"
    nav_bg = "rgba(255,255,255,0.9)"; card_bg = "white"; hover_bg = "#F5F5F5"
    dark_orange = "#FF9330"

# ===== 스타일 =====
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@500;700;900&display=swap');
html, body {{
    background-color: {bg_color};
    color: {font_color};
    font-family: 'Noto Sans KR', sans-serif;
    zoom: 1.10;
    margin: 0;
}}
.stApp {{ background-color: {bg_color}; }}
.block-container {{ padding-top: 0 !important; }}
.container {{ max-width: 1200px; margin: auto; padding: 40px; }}
a {{ text-decoration: none !important; color: {font_color}; }}

.top-nav {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    margin-top: -40px !important;
    background-color: {nav_bg};
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}}
.nav-left {{ display: flex; align-items: center; gap: 60px; }}
.top-nav .nav-left > div:first-child a {{
    color: #000 !important;
    font-size: 28px;
    font-weight: bold;
}}
.nav-menu {{
    display: flex;
    gap: 36px;
    font-size: 18px;
    font-weight: 600;
}}
.nav-menu div a {{ color: #000 !important; transition: all 0.2s ease; }}
.nav-menu div:hover a {{ color: #FF9330 !important; }}
.profile-group {{ display: flex; gap: 16px; align-items: center; }}
.profile-icon {{
    background-color: #888; width: 36px; height: 36px; border-radius: 50%; cursor: pointer;
}}
header {{ display: none !important; }}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="container">', unsafe_allow_html=True)
st.markdown(f"""
<div class="top-nav">
  <div class="nav-left">
    <div><a href="/" target="_self">🐾 딸깍공</a></div>
    <div class="nav-menu">
      <div><a href="/"   target="_self">메인페이지</a></div>
      <div><a href="/main"   target="_self">공부 시작</a></div>
      <div><a href="/ocr_paddle" target="_self">필기</a></div>
      <div><a href="/folder_page" target="_self">저장폴더</a></div>
      <div><a href="/quiz" target="_self">퀴즈</a></div>
      <div><a href="/report" target="_self">리포트</a></div>
      <div><a href="/ranking" target="_self">랭킹</a></div>
    </div>
  </div>
  <div class="profile-group">
    <div class="profile-icon" title="내 프로필"></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ======== YOLO 모델/상수 ========
USER_ID = "user01"
USER_DATA_PATH = f"user_yawn_data_{USER_ID}.json"
MODEL_PATH = "runs/detect/train24-mixtrain/weights/best.pt"
YAWN_CLASS_INDEX = 2       # 하품
DROWSY_CLASS_INDEX = 3     # 졸음
CONF_THRESH = 0.45
IMGSZ = 640
TARGET_FPS = 30
SKIP = 1

# 카메라 캡처 vs 화면 표시
cam_cap_w, cam_cap_h   = 1280, 720
cam_disp_w, cam_disp_h = 720, 405

@st.cache_resource(show_spinner=False)
def load_model():
    m = YOLO(MODEL_PATH)
    return m

model = load_model()

# ======== 세션 상태(분석용) ========
def _load_user_data():
    if os.path.exists(USER_DATA_PATH):
        try:
            with open(USER_DATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {
        "threshold_ratio": 0.4,
        "min_duration_sec": 0.5,
        "avg_yawn_duration": 1.0,
        "yawn_events": [],
        "sleep_events": []
    }

def _save_user_data(data):
    try:
        with open(USER_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

if "analytics" not in st.session_state:
    user_data = _load_user_data()
    window_seconds = 3
    window_size = int(TARGET_FPS * window_seconds)
    drowsy_seconds = 2
    drowsy_frames = int(TARGET_FPS * drowsy_seconds)

    st.session_state.analytics = {
        "user_data": user_data,
        "yawn_events": user_data.get("yawn_events", []),
        "sleep_events": user_data.get("sleep_events", []),
        "initial_yawn_len": len(user_data.get("yawn_events", [])),
        "initial_sleep_len": len(user_data.get("sleep_events", [])),
        "BASE_ATTENTION": 100,
        "yawn_window": deque(maxlen=window_size),
        "weights": [i / window_size for i in range(1, window_size + 1)],
        "drowsy_window": deque(maxlen=drowsy_frames),
        "threshold_ratio": float(user_data.get("threshold_ratio", 0.4)),
        "avg_yawn_duration": float(user_data.get("avg_yawn_duration", 1.0)),
        "min_yawn_duration": int(TARGET_FPS * max(0.6, min(user_data.get("avg_yawn_duration", 1.0) * 0.9, 2.0))),
        "yawning": False,
        "sleeping": False,
        "yawn_start_time": None,
        "sleep_start_time": None,
        "durations": [],
        "last_save_ts": 0.0,
        # 성능/안정
        "frame_idx": 0,
        "last_status_change": 0.0,
        # 콜백→UI 전달 버퍼
        "latest_attention": 100,
        "fatigue_bump": 0,
        # 히스테리시스
        "threshold_ratio_on": 0.45,
        "threshold_ratio_off": 0.35,
    }

A = st.session_state.analytics

# ======== 뽀모도로/집중도 기본 ========
if "start_camera" not in st.session_state:
    st.session_state.start_camera = True
if "cam_active" not in st.session_state:          # ★ 실제 재생(playing) 중인지
    st.session_state.cam_active = False
if "focus_score" not in st.session_state:
    st.session_state.focus_score = 100
if "fatigue_count" not in st.session_state:
    st.session_state.fatigue_count = 0
if "pomodoro_mode" not in st.session_state:
    st.session_state.pomodoro_mode = "공부 중"
if "pomodoro_start" not in st.session_state:
    st.session_state.pomodoro_start = time.time()
if "pomodoro_duration" not in st.session_state:
    st.session_state.pomodoro_duration = 25 * 60

# ======== 🔴 빨간 박스 로직용 추가 상태 ========
def _init_red_states():
    ss = st.session_state
    ss.setdefault("low_focus_since", None)         # 집중도<80 시작 시각
    ss.setdefault("rest_prompt_active", False)     # 휴식 제안 배너 표시 여부
    ss.setdefault("rest_cooldown_ts", 0.0)         # 제안 쿨다운
    ss.setdefault("break_active", False)           # 5분 휴식 진행중
    ss.setdefault("break_end_ts", 0.0)             # 휴식 종료 시각
    ss.setdefault("show_start_alert", False)       # 휴식 끝 안내 토스트
    ss.setdefault("last_tick_ts", time.time())     # 누적용 틱
    ss.setdefault("total_study_sec", 0.0)          # 공부 누적 시간(초)
    ss.setdefault("awarded_hours", 0)              # 포인트 지급된 시간 블록 수
    ss.setdefault("ended", False)                  # 학습 종료 여부
    ss.setdefault("last_break_reason", None)       # 휴식 사유: suggest/pomodoro/manual 등

_init_red_states()

# ======== 휴식 헬퍼 ========
def start_break(seconds=300, reason="manual"):
    ss = st.session_state
    ss.break_active = True
    ss.break_end_ts = time.time() + seconds
    ss.start_camera = False
    ss.cam_active = False     # ★ 카메라 비활성 처리
    ss.pomodoro_mode = "휴식 중"
    ss.pomodoro_duration = seconds
    ss.pomodoro_start = time.time()
    # 제안 배너/저집중 트래킹 정리
    ss.rest_prompt_active = False
    ss.low_focus_since = None
    ss.last_break_reason = reason

def end_break():
    ss = st.session_state
    ss.break_active = False
    ss.start_camera = True    # cam_active는 webrtc가 실제 재생되면 True로 갱신됨
    ss.pomodoro_mode = "공부 중"
    ss.pomodoro_duration = 25 * 60
    ss.pomodoro_start = time.time()
    ss.show_start_alert = True  # “학습 시작” 토스트

# ======== 뽀모도로 업데이트(25분 종료 시 동일 빨간 로직 자동 발동) ========
def update_pomodoro():
    elapsed = time.time() - st.session_state.pomodoro_start
    if elapsed > st.session_state.pomodoro_duration:
        if st.session_state.pomodoro_mode == "공부 중":
            # ✅ 25분 종료 → 동일한 5분 휴식 자동 시작
            if not st.session_state.break_active:
                start_break(seconds=5*60, reason="pomodoro")
        else:
            # 휴식 타이머 끝 → 공부 재개
            end_break()

# ======== 감지 유틸 ========
def detect_yawn(results):
    for box in results.boxes.data.tolist():
        if int(box[5]) == YAWN_CLASS_INDEX:
            return True
    return False

def detect_drowsy(results):
    for box in results.boxes.data.tolist():
        if int(box[5]) == DROWSY_CLASS_INDEX:
            return True
    return False

def compute_attention():
    yawn_count = sum(1 for e in A["yawn_events"][A["initial_yawn_len"]:] if e["type"] == "yawn_end")
    sleep_count = sum(1 for e in A["sleep_events"][A["initial_sleep_len"]:] if e["type"] in ["end", "drowys_end"])
    return A["BASE_ATTENTION"] - (5 * sleep_count) - (2 * yawn_count)

# --- 상태 전이 디바운스 ---
DEBOUNCE_SEC = 0.3
def set_state(new_yawning: bool, new_sleeping: bool, attention_on_event: int):
    now = time.time()
    if now - A["last_status_change"] < DEBOUNCE_SEC:
        return
    changed = (A["yawning"] != new_yawning) or (A["sleeping"] != new_sleeping)
    if not changed:
        return
    A["last_status_change"] = now

    # 하품 상태 전이
    if not A["yawning"] and new_yawning:
        A["yawn_start_time"] = now
        A["yawn_events"].append({"type": "start", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    elif A["yawning"] and not new_yawning:
        if A["yawn_start_time"]:
            duration = now - A["yawn_start_time"]
            A["durations"].append(duration)
            A["yawn_start_time"] = None
            if A["durations"]:
                A["avg_yawn_duration"] = sum(A["durations"]) / len(A["durations"])
        A["yawn_events"].append({
            "type": "yawn_end",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "avg_yawn_duration": round(A["avg_yawn_duration"], 2),
            "attention_score": attention_on_event
        })

    # 졸음 상태 전이
    if not A["sleeping"] and new_sleeping:
        A["sleep_start_time"] = now
        A["sleep_events"].append({"type": "start", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    elif A["sleeping"] and not new_sleeping:
        A["sleep_events"].append({
            "type": "drowys_end",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "attention_score": attention_on_event
        })
        A["sleep_start_time"] = None

    A["yawning"] = new_yawning
    A["sleeping"] = new_sleeping
    if A["yawning"] or A["sleeping"]:
        A["fatigue_bump"] += 1

# ======== WebRTC 콜백(YOLO 추론) ========
def video_frame_callback(frame: av.VideoFrame) -> av.VideoFrame:
    img = frame.to_ndarray(format="bgr24")
    A["frame_idx"] += 1
    run_infer = (A["frame_idx"] % SKIP == 0)

    if run_infer:
        results = model.predict(
            img,
            conf=CONF_THRESH,
            iou=0.5,
            imgsz=IMGSZ,
            classes=[YAWN_CLASS_INDEX, DROWSY_CLASS_INDEX],
            verbose=False,
            max_det=10,
            agnostic_nms=False
            # , device=0
        )[0]

        # 감지 결과
        is_yawning = detect_yawn(results)
        is_drowsy  = detect_drowsy(results)

        # 윈도우 업데이트
        A["yawn_window"].append(is_yawning)
        A["drowsy_window"].append(is_drowsy)

        # 박스 시각화
        if results.boxes is not None:
            for box in results.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                color = (0, 0, 255) if cls_id == YAWN_CLASS_INDEX else ((255, 255, 0) if cls_id == DROWSY_CLASS_INDEX else (0, 255, 0))
                label = f"{model.names.get(cls_id, str(cls_id))} {conf:.2f}"
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                cv2.putText(img, label, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # 하품 판단(히스테리시스 + 연속 프레임)
        weights = A["weights"]
        weighted_sum = sum(w for yawning, w in zip(A["yawn_window"], weights) if yawning)
        weighted_ratio = weighted_sum / (sum(weights) if sum(weights) else 1.0)
        continuous_count = 0
        for status in reversed(A["yawn_window"]):
            if status: continuous_count += 1
            else: break

        if (not A["yawning"] and weighted_ratio > A["threshold_ratio_on"]  and continuous_count > A["min_yawn_duration"]):
            new_yawning = True
        elif (A["yawning"]    and weighted_ratio > A["threshold_ratio_off"] and continuous_count > A["min_yawn_duration"]):
            new_yawning = True
        else:
            new_yawning = False

        # 졸음 판단(최근 N프레임 중 비율)
        drowsy_frames = A["drowsy_window"].maxlen or 1
        new_sleeping = (sum(A["drowsy_window"]) >= int(drowsy_frames * 0.8))

        # 집중도(이벤트에 기록용)
        attention_for_event = max(0, min(100, compute_attention()))
        set_state(new_yawning, new_sleeping, attention_for_event)

    # 현재 상태/집중도 화면 표기
    attention_score = max(0, min(100, compute_attention()))
    A["latest_attention"] = attention_score

    status_text = "Yawning" if A["yawning"] else ("Sleeping" if A["sleeping"] else "Awake")
    status_color = (0,0,255) if A["yawning"] else ((255,255,0) if A["sleeping"] else (0,255,0))
    cv2.putText(img, f"Status: {status_text}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, status_color, 3)
    cv2.putText(img, f"Attention: {attention_score}", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), 3)

    # 화면 표시용 축소
    small = cv2.resize(img, (cam_disp_w, cam_disp_h), interpolation=cv2.INTER_AREA)
    return av.VideoFrame.from_ndarray(small, format="bgr24")

# ===== 레이아웃 =====
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
    st.markdown(
        '''
        <span style="font-size:2.3rem; vertical-align:middle; margin-right:7px;">📌</span>
        <span style="font-size:2.1rem; font-weight:900; vertical-align:middle;">오늘의 목표</span>
        <ul style="margin-top:24px; margin-bottom:30px; font-size:1.35rem; list-style:none; padding-left:0;">
            <li style="margin-bottom:9px;"><span style="color:#6F50E5; font-size:1.4rem;">✔️</span> <span style="margin-left:10px;">단원 복습</span></li>
            <li style="margin-bottom:9px;"><span style="color:#6F50E5; font-size:1.4rem;">✔️</span> <span style="margin-left:10px;">문제 풀이</span></li>
            <li><span style="color:#6F50E5; font-size:1.4rem;">✔️</span> <span style="margin-left:10px;">암기 테스트</span></li>
        </ul>
        <span style="font-size:2.0rem; vertical-align:middle;">💡</span>
        <span style="font-size:1.7rem; font-weight:700; vertical-align:middle; margin-left:8px;">집중 팁</span>
        <ul style="margin-top:13px; font-size:1.18rem; padding-left:22px;">
            <li>눈을 자주 깜빡이세요</li>
            <li>물 한 잔 마시기</li>
            <li>스트레칭으로 전환</li>
        </ul>
        ''', unsafe_allow_html=True
    )

with col2:
    # 🔧 카메라만 좌우로 '약간' 이동: 오른쪽 spacer를 더 크게 주면 카메라가 왼쪽으로 밀립니다.
    # 숫자를 미세 조정해 보세요. 예: [0.98, 1, 1.02] → 아주 살짝 왼쪽 / [1.02, 1, 0.98] → 아주 살짝 오른쪽
    left_sp, cam_col, right_sp = st.columns([0.1, 1.6, 0.3])  # ← 현재는 '조금 왼쪽' 설정

    with cam_col:
        st.markdown(
            f'<div style="width:{cam_disp_w}px;height:{cam_disp_h}px;display:flex;'
            f'align-items:center;justify-content:center;margin:0;padding:0;">',
            unsafe_allow_html=True
        )
        if st.session_state.start_camera and not st.session_state.ended:
            # ★ webrtc_streamer 컨텍스트로 실제 재생 여부 확인
            ctx = webrtc_streamer(
                key="camera",
                video_frame_callback=video_frame_callback,
                media_stream_constraints={
                    "video": {"width": {"ideal": cam_cap_w}, "height": {"ideal": cam_cap_h}},
                    "audio": False
                },
                async_processing=True,
            )
            st.session_state.cam_active = bool(ctx) and getattr(ctx.state, "playing", False)
        else:
            st.session_state.cam_active = False
            st.markdown(
                f'<div style="width:{cam_disp_w}px; height:{cam_disp_h}px; background: transparent;"></div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

with col3:
    # 1초마다 UI 리프레시
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=1000, key="auto_refresh")

    # 뽀모도로(25분 완료 → 자동 휴식 / 휴식 완료 → 자동 재개)
    update_pomodoro()
    remaining = max(0, int(st.session_state.pomodoro_duration - (time.time() - st.session_state.pomodoro_start)))
    mins, secs = divmod(remaining, 60)

    st.markdown(
        f"""
        <div style="margin-top:12px;">
            <span style="font-size:2.3rem; vertical-align:middle;">⏱️</span>
            <span style="font-size:2.1rem; font-weight:900; vertical-align:middle;">뽀모도로 타이머</span>
        </div>
        <div style="margin:22px 0 7px 0;">
            <b style="font-size:1.15rem;">현재 상태:</b> <span style="font-size:1.15rem;">{st.session_state.pomodoro_mode}</span><br>
            <b style="font-size:1.15rem;">남은 시간:</b> <span style="font-size:1.15rem;">{mins:02d}:{secs:02d}</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.progress(remaining / st.session_state.pomodoro_duration if st.session_state.pomodoro_duration > 0 else 0.0)

    # 콜백→UI 전달값 반영
    st.session_state.focus_score = int(A.get("latest_attention", st.session_state.get("focus_score", 100)))
    if A.get("fatigue_bump", 0) > 0:
        st.session_state.fatigue_count += A["fatigue_bump"]
        A["fatigue_bump"] = 0

    # 집중도 표시
    st.markdown(
        f"""<span style="font-size:2.0rem; vertical-align:middle;">🧠</span>
            <span style="font-size:1.7rem; font-weight:700; vertical-align:middle; margin-left:8px;">집중도</span>""",
        unsafe_allow_html=True
    )
    st.progress(st.session_state.focus_score / 100)
    st.markdown(f"""<span style="font-size:1.13rem;">📊 점수: {st.session_state.focus_score} / 100</span>""",
                unsafe_allow_html=True)

    if st.session_state.fatigue_count >= 5:
        st.markdown(
            '<div style="color:#ff5555; font-weight:700; margin-top:10px;">⚠️ 졸음/하품이 반복적으로 감지되고 있어요!<br>잠시 쉬어보는 건 어떨까요?</div>',
            unsafe_allow_html=True
        )

    # ========== 빨간 박스 로직 ==========
    now_ts = time.time()

    # (1) 공부 시간 누적 (공부 중 & 휴식 아님 & 종료 아님 & 카메라 playing)
    dt = max(0, now_ts - st.session_state.last_tick_ts)
    st.session_state.last_tick_ts = now_ts
    if (st.session_state.pomodoro_mode == "공부 중") \
        and (not st.session_state.break_active) \
        and (not st.session_state.ended) \
        and (st.session_state.cam_active):            # ★ 추가 조건
        st.session_state.total_study_sec += dt

    # (2) 집중도 < 80 지속 시 5분 휴식 제안
    THRESHOLD = 80
    HOLD_SEC = 10
    if (st.session_state.focus_score < THRESHOLD) and (st.session_state.pomodoro_mode == "공부 중") \
        and (not st.session_state.break_active) and (not st.session_state.ended) and (now_ts > st.session_state.rest_cooldown_ts):
        if st.session_state.low_focus_since is None:
            st.session_state.low_focus_since = now_ts
    else:
        st.session_state.low_focus_since = None

    if (st.session_state.low_focus_since is not None) and (now_ts - st.session_state.low_focus_since >= HOLD_SEC) \
        and (not st.session_state.rest_prompt_active) and (not st.session_state.break_active):
        st.session_state.rest_prompt_active = True

    # (3) 휴식 제안 배너(UI)
    if st.session_state.rest_prompt_active and not st.session_state.ended:
        st.warning("집중도가 80 미만으로 떨어졌어요. **5분 쉬기**를 시작할까요?", icon="⏸️")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("지금 5분 쉬기", key="accept_break"):
                start_break(seconds=5*60, reason="suggest")
                st.session_state.rest_cooldown_ts = time.time() + 10 * 60  # 10분 쿨다운
        with c2:
            if st.button("괜찮아요, 계속 할게요", key="decline_break"):
                st.session_state.rest_prompt_active = False
                st.session_state.low_focus_since = None
                st.session_state.rest_cooldown_ts = time.time() + 5 * 60   # 5분 뒤 재제안 가능

    # (4) 휴식 종료 알림
    if st.session_state.show_start_alert:
        st.success("✅ 쉬는시간 5분이 끝났습니다. 다시 학습을 시작해 볼까요? 📚")
        st.session_state.show_start_alert = False

    # (5) 학습 1시간마다 코인 지급
    hours = int(st.session_state.total_study_sec // 3600)
    if hours > st.session_state.awarded_hours:
        gain = 100
        st.session_state.awarded_hours = hours
        st.session_state.user_data["coins"] = int(st.session_state.user_data.get("coins", 0)) + gain
        try:
            with open("user_data.json", "w", encoding="utf-8") as f:
                json.dump(st.session_state.user_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        st.success(f"🎉 학습 {hours}시간 달성! 코인 {gain} 지급했어요. (보유: {st.session_state.user_data['coins']})")

    # (6) 학습 종료 버튼
    st.divider()
    left, right = st.columns([1,1])
    with left:
        if st.button("🛑 학습 종료", type="primary", key="end_study"):
            st.session_state.ended = True
            st.session_state.start_camera = False
            st.session_state.cam_active = False      # ★ 종료 시 비활성
    with right:
        h = int(st.session_state.total_study_sec // 3600)
        m = int((st.session_state.total_study_sec % 3600) // 60)
        s = int(st.session_state.total_study_sec % 60)
        st.markdown(f"**누적 공부 시간:** {h:02d}:{m:02d}:{s:02d}  &nbsp;|&nbsp; **코인:** {int(st.session_state.user_data.get('coins',0))}")

st.markdown('</div>', unsafe_allow_html=True)

# === 주기 저장 ===
now = time.time()
if now - A.get("last_save_ts", 0) >= 3.0:
    A["last_save_ts"] = now
    A["user_data"]["threshold_ratio"] = A["threshold_ratio"]
    A["user_data"]["min_duration_sec"] = A["min_yawn_duration"] / TARGET_FPS
    A["user_data"]["avg_yawn_duration"] = round(A["avg_yawn_duration"], 2)
    A["user_data"]["yawn_events"] = A["yawn_events"]
    A["user_data"]["sleep_events"] = A["sleep_events"]
    _save_user_data(A["user_data"])
