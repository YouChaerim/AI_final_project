# pages/main.py
# -*- coding: utf-8 -*-
import streamlit as st
from streamlit_webrtc import webrtc_streamer
import av
import cv2
import os, json, time, base64
from collections import deque
from datetime import datetime
import math
from components.header import render_header
import requests
from components.auth import require_login

print(f"✅✅✅ Executing: {__file__} ✅✅✅")
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8080")
require_login(BACKEND_URL)

user = st.session_state.get("user", {}) or {}
USER_ID = user.get("id") or user.get("_id") or user.get("user_id") or ""

if not USER_ID:
    st.error("세션에 사용자 정보가 없습니다. 다시 로그인해 주세요.")
    st.switch_page("onboarding.py")
    st.stop()

# === 성능 튜닝(가급적 최상단) ===
cv2.setNumThreads(1)   # OpenCV 내부 스레드 경합 줄이기

# ===== YOLO =====
try:
    from ultralytics import YOLO
except Exception as e:
    st.error("⚠️ ultralytics( YOLO ) 모듈이 없습니다. 가상환경(파이썬3.10)에서 `pip install ultralytics opencv-python numpy<2` 후 다시 실행하세요.")
    st.stop()

# ===== 페이지/테마 세팅 =====
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = st.session_state.user_data.get("dark_mode", False)

if st.session_state.dark_mode:
    bg_color = "#1C1C1E"; font_color = "#F2F2F2"
    nav_bg = "#2C2C2E"; card_bg = "#2C2C2E"; hover_bg = "#3A3A3C"
    border_color = "rgba(255,255,255,0.08)"
    subtle_text = "#CFCFCF"
else:
    bg_color = "#FAFAFA"; font_color = "#333"
    nav_bg = "rgba(255,255,255,0.9)"; card_bg = "white"; hover_bg = "#F5F5F5"
    border_color = "rgba(0,0,0,0.06)"
    subtle_text = "#666"

accent_orange = "#FF9330"   # 포인트 컬러

# =========================
# (추가) 헤더 아바타 로딩 (퀴즈/저장폴더와 동일 기능)
# =========================
def _hdr_resolve_assets_root():
    here = os.path.dirname(__file__)
    cands = [os.path.abspath(os.path.join(here, "assets")), os.path.abspath(os.path.join(here, "..", "assets"))]
    for p in cands:
        if os.path.isdir(p): return p
    return cands[0]
_HDR_ASSETS_ROOT = _hdr_resolve_assets_root()

def _hdr_to_data_uri(abs_path: str) -> str:
    with open(abs_path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")

def _hdr_get_char_image_uri(char_key: str, hat_id: str | None = None) -> str:
    keys = [char_key] + (["siba"] if char_key == "shiba" else [])
    candidates = []
    if hat_id:
        for k in keys:
            for sep in ["", "_", "-"]:
                candidates.append(os.path.join(_HDR_ASSETS_ROOT, "items", "hats", f"{k}{sep}{hat_id}.png"))
                candidates.append(os.path.join(_HDR_ASSETS_ROOT, "characters", f"{k}{sep}{hat_id}.png"))
    for k in keys:
        candidates.append(os.path.join(_HDR_ASSETS_ROOT, "characters", f"{k}.png"))
    for p in candidates:
        if os.path.exists(p):
            return _hdr_to_data_uri(p)
    # fallback
    return ("data:image/svg+xml;utf8,"
            "<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'>"
            "<text x='50%' y='60%' font-size='28' text-anchor='middle'>🐾</text></svg>")

header_avatar_uri = _hdr_get_char_image_uri(user.get("active_char", "rabbit"))

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

/* [UI] 공통 카드/패널 */
.card {{
    background:{card_bg};
    border:1px solid {border_color};
    border-radius:16px;
    box-shadow:0 2px 8px rgba(0,0,0,.06);
    padding:18px 20px;
    margin-bottom:18px;
}}
.panel {{
    background:{card_bg};
    border:1px solid {border_color};
    border-radius:16px;
    box-shadow:0 2px 10px rgba(0,0,0,.06);
    overflow:hidden;
    margin-bottom:18px;
}}
.panel-body {{ padding:18px 20px; }}
.panel-foot {{
    padding: 14px 20px;
    border-top:1px solid {border_color};
}}

/* [UI] 헤더 뒤 연한 흰 배경 + 둥근모서리 */
.soft-bg {{
    background: rgba(255,255,255,0.65);
    border:1px solid {border_color};
    border-radius:14px;
    padding:10px 12px;
    backdrop-filter: blur(2px);
    box-shadow: inset 0 1px 2px rgba(0,0,0,0.02);
}}
.badge-head {{
    display:inline-flex;
    align-items:center;
    gap:10px;
    background: linear-gradient(135deg,#FFB776,#FF8A3D);
    color:#fff;
    border-radius:12px;
    padding:8px 14px;
    font-weight:900;
    font-size:18px;
}}
.badge-head.alt {{
    background: linear-gradient(135deg,#FFD39A,#FF9C55);
}}
.small-subtle {{
    font-size: 0.92rem;
    color: {subtle_text};
}}

/* [UI] 겹침 방지 */
.cam-wrap   {{ position:relative; z-index:0; overflow:hidden; }}
.right-pane {{ position:relative; z-index:2; }}

/* [UI] 좌/우 컬럼 내부 여백 소폭 감소 */
[data-testid="column"]:first-child > div {{ padding-right: 6px; }}
[data-testid="column"]:last-child  > div {{ padding-left:  6px; }}
</style>
""", unsafe_allow_html=True)

# ── 헤더 (저장폴더/퀴즈와 동일 구조 & 캐릭터 표시) ──
st.markdown('<div class="container">', unsafe_allow_html=True)
render_header()

st.session_state.setdefault("user_data", {})
st.session_state.user_data.setdefault("todo_items", [])

# TODOS 서버 연동 헬퍼
def fetch_today_todos():
    """오늘 할 일 목록을 서버에서 받아와 세션에 반영."""
    try:
        r = requests.get(f"{BACKEND_URL}/todos/{USER_ID}", timeout=10)
        r.raise_for_status()
        items = r.json()
        st.session_state.user_data["todo_items"] = [
            {"id": t["id"], "text": t["contents"], "done": t["complete"]}
            for t in items
        ]
    except requests.exceptions.RequestException as e:
        st.session_state.user_data.setdefault("todo_items", [])
        st.error(f"오늘 할 일 불러오기 실패: {getattr(e, 'response', None) and e.response.text or e}")

def toggle_goal(todo_id: str, idx: int, new_val: bool):
    """완료 여부 토글."""
    try:
        requests.put(f"{BACKEND_URL}/todos/toggle/{USER_ID}/{todo_id}", timeout=10).raise_for_status()
        st.session_state.user_data["todo_items"][idx]["done"] = new_val
    except requests.exceptions.RequestException:
        st.error("상태 변경 실패")

# 첫 진입 시 한 번만 오늘 목록 동기화
if not st.session_state.user_data.get("_today_loaded_main"):
    fetch_today_todos()
    st.session_state.user_data["_today_loaded_main"] = True

# ===== 세션 시작: 백엔드로 생성 =====
def ensure_session_started():
    if st.session_state.get("study_session_id"):
        return
    try:
        r = requests.post(f"{BACKEND_URL}/study/sessions/start/{USER_ID}", timeout=5)
        r.raise_for_status()
        st.session_state.study_session_id = r.json()["session_id"]
    except requests.exceptions.RequestException as e:
        st.error(f"세션 시작 실패: {e}")

ensure_session_started()

# ======== YOLO 모델/상수 ========
MODEL_PATH = "runs/detect/train24-mixtrain/weights/best.pt"
YAWN_CLASS_INDEX = 2       # 하품
DROWSY_CLASS_INDEX = 3     # 졸음
CONF_THRESH = 0.45
IMGSZ = 640
TARGET_FPS = 30
SKIP = 1

# 카메라 캡처 vs 화면 표시
cam_cap_w, cam_cap_h   = 1280, 720
cam_disp_w, cam_disp_h = 720, 405   # 필요시 640x360/560x315 등으로 줄여도 됨

@st.cache_resource(show_spinner=False)
def load_model():
    m = YOLO(MODEL_PATH)
    return m

model = load_model()

# ======== 세션 상태(분석용) ========
# ===== 사용자 하품 가중치(평균 하품 시간) 불러오기 =====
def get_user_yawn_weight() -> float | None:
    try:
        r = requests.get(f"{BACKEND_URL}/study/users/{USER_ID}/yawn-weight", timeout=5)
        r.raise_for_status()
        data = r.json() or {}
        val = data.get("avg_yawn")
        if isinstance(val, (int, float)) and val > 0:
            return float(val)
    except requests.exceptions.RequestException:
        pass
    return None

if "analytics" not in st.session_state:
    window_seconds = 3
    window_size = int(TARGET_FPS * window_seconds)
    drowsy_seconds = 2
    drowsy_frames = int(TARGET_FPS * drowsy_seconds)

    if "user_yawn_weight" not in st.session_state:
        st.session_state.user_yawn_weight = get_user_yawn_weight()
    avg_base = float(st.session_state.user_yawn_weight or 1.0)

    st.session_state.analytics = {
        "yawn_events": [],
        "sleep_events": [],
        "initial_yawn_len": 0,
        "initial_sleep_len": 0,
        "BASE_ATTENTION": 100,
        "yawn_window": deque(maxlen=window_size),
        "weights": [i / window_size for i in range(1, window_size + 1)],
        "drowsy_window": deque(maxlen=drowsy_frames),
        "threshold_ratio": 0.4,
        "avg_yawn_duration": avg_base,
        "min_yawn_duration": int(TARGET_FPS * max(0.6, min(avg_base * 0.9, 2.0))),
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
        # 백엔드 전송용 포인터
        "last_flushed_yawn_len": 0,
        "last_flushed_sleep_len": 0,
        "last_flush_ts": 0.0,
    }

A = st.session_state.analytics

# 사용자 가중치가 있으면 초기 평균에 반영(기존 평균 갱신 로직 유지)
if st.session_state.user_yawn_weight:
    A["durations"].append(st.session_state.user_yawn_weight)

def flush_events(force: bool = False):
    sid = st.session_state.get("study_session_id")
    if not sid:
        return
    now_ts = time.time()
    if not force and (now_ts - A["last_flush_ts"] < 5.0):
        return

    # 새로 쌓인 이벤트만 잘라서 보냄
    ys = A["yawn_events"][A["last_flushed_yawn_len"]:]
    ss = A["sleep_events"][A["last_flushed_sleep_len"]:]
    if not ys and not ss and not force:
        return

    payload = {"yawn_events": ys, "sleep_events": ss}
    try:
        requests.post(
            f"{BACKEND_URL}/study/sessions/{sid}/events/batch",
            json=payload, timeout=5
        ).raise_for_status()
        A["last_flushed_yawn_len"] = len(A["yawn_events"])
        A["last_flushed_sleep_len"] = len(A["sleep_events"])
        A["last_flush_ts"] = now_ts
    except requests.exceptions.RequestException as e:
        # 실패 시 다음 주기 재시도
        print("flush_events error:", e)

def finish_session():
    sid = st.session_state.get("study_session_id")
    if not sid:
        return
    try:
        # 남은 이벤트 모두 밀어넣기
        flush_events(force=True)

        body = {
            "focus_score": float(st.session_state.get("focus_score", 0)),
            "yawn_count": sum(1 for e in A["yawn_events"] if e.get("type") == "yawn_end"),
            "avg_yawn": float(A.get("avg_yawn_duration") or 0),
            "sum_study_time": float(st.session_state.get("total_study_sec", 0.0)),
        }
        requests.post(
            f"{BACKEND_URL}/study/sessions/finish/{USER_ID}/{sid}",
            json=body, timeout=5
        ).raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"세션 종료 저장 실패: {e}")

# ======== 뽀모도로/집중도 기본 ========
if "start_camera" not in st.session_state:
    st.session_state.start_camera = True
if "cam_active" not in st.session_state:
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
if "last_study_tick_ts" not in st.session_state:
    st.session_state.last_study_tick_ts = time.time()

# ======== 🔴 빨간 박스 로직용 추가 상태 ========
def _init_red_states():
    ss = st.session_state
    ss.setdefault("low_focus_since", None)
    ss.setdefault("rest_prompt_active", False)
    ss.setdefault("rest_cooldown_ts", 0.0)
    ss.setdefault("break_active", False)
    ss.setdefault("break_end_ts", 0.0)
    ss.setdefault("show_start_alert", False)
    ss.setdefault("last_tick_ts", time.time())
    ss.setdefault("total_study_sec", 0.0)
    ss.setdefault("awarded_hours", 0)
    ss.setdefault("ended", False)
    ss.setdefault("last_break_reason", None)
    ss.setdefault("show_break_alert", False)

_init_red_states()

# ======== 휴식 헬퍼 ========
def start_break(seconds=300, reason="manual"):
    ss = st.session_state
    ss.break_active = True
    ss.break_end_ts = time.time() + seconds
    ss.start_camera = False
    ss.cam_active = False
    ss.pomodoro_mode = "휴식 중"
    ss.pomodoro_duration = seconds
    ss.pomodoro_start = time.time()
    ss.rest_prompt_active = False
    ss.low_focus_since = None
    ss.last_break_reason = reason
    ss.show_break_alert = (reason == "pomodoro")
    sid = ss.get("study_session_id")
    if sid:
        api_reason = "focus_drop" if reason == "low_focus" else reason
        try:
            r = requests.post(
                f"{BACKEND_URL}/study/sessions/{sid}/breaks/start",
                json={
                    "reason": api_reason,
                    "focus_score": float(ss.get("focus_score", 0)),
                },
                timeout=5,
            )
            if r.status_code == 409:
                # 이미 열린 break가 있으면 무시 (백엔드에서 409 반환)
                pass
            else:
                r.raise_for_status()
                ss.open_break_id = r.json().get("break_id")
        except requests.exceptions.RequestException as e:
            print("break start error:", e)

def end_break():
    ss = st.session_state
    ss.break_active = False
    ss.start_camera = True
    ss.pomodoro_mode = "공부 중"
    ss.pomodoro_duration = 25 * 60
    ss.pomodoro_start = time.time()
    ss.show_start_alert = True
    sid = ss.get("study_session_id")
    if sid:
        try:
            requests.post(
                f"{BACKEND_URL}/study/sessions/{sid}/breaks/end",
                json={
                    "break_id": ss.get("open_break_id"),
                    "focus_score": float(ss.get("focus_score", 0)),
                },
                timeout=5,
            ).raise_for_status()
        except requests.exceptions.RequestException as e:
            print("break end error:", e)
        finally:
            ss.open_break_id = None

# ======== 뽀모도로 업데이트 ========
def update_pomodoro():
    elapsed = time.time() - st.session_state.pomodoro_start
    if elapsed > st.session_state.pomodoro_duration:
        if st.session_state.pomodoro_mode == "공부 중":
            if not st.session_state.break_active:
                start_break(seconds=5*60, reason="pomodoro")
        else:
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
        )[0]

        is_yawning = detect_yawn(results)
        is_drowsy  = detect_drowsy(results)

        A["yawn_window"].append(is_yawning)
        A["drowsy_window"].append(is_drowsy)

        if results.boxes is not None:
            for box in results.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                color = (0, 0, 255) if cls_id == YAWN_CLASS_INDEX else ((255, 255, 0) if cls_id == DROWSY_CLASS_INDEX else (0, 255, 0))
                label = f"{model.names.get(cls_id, str(cls_id))} {conf:.2f}" if hasattr(model, "names") else f"{cls_id} {conf:.2f}"
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                cv2.putText(img, label, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

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

        drowsy_frames = A["drowsy_window"].maxlen or 1
        new_sleeping = (sum(A["drowsy_window"]) >= int(drowsy_frames * 0.8))

        attention_for_event = max(0, min(100, compute_attention()))
        set_state(new_yawning, new_sleeping, attention_for_event)

    attention_score = max(0, min(100, compute_attention()))
    A["latest_attention"] = attention_score

    status_text = "Yawning" if A["yawning"] else ("Sleeping" if A["sleeping"] else "Awake")
    status_color = (0,0,255) if A["yawning"] else ((255,255,0) if A["sleeping"] else (0,255,0))
    cv2.putText(img, f"Status: {status_text}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, status_color, 3)
    cv2.putText(img, f"Attention: {attention_score}", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255,255,255), 3)

    small = cv2.resize(img, (cam_disp_w, cam_disp_h), interpolation=cv2.INTER_AREA)
    return av.VideoFrame.from_ndarray(small, format="bgr24")

# ===== 유틸: 안전한 토스트(낮은 버전 호환) =====
def _toast(msg: str, icon: str | None = None):
    try:
        st.toast(msg, icon=icon)  # Streamlit 최신
    except Exception:
        st.warning(msg)           # 구버전 호환

# ===== 레이아웃 =====
col1, col2, col3 = st.columns([0.9, 2.2, 0.9])

with col1:
    st.markdown('<div class="right-pane">', unsafe_allow_html=True)
    st.markdown('<div style="height:56px;"></div>', unsafe_allow_html=True)

    st.markdown('<div class="soft-bg" style="padding:16px 18px; margin-bottom:12px;">'
                '<div class="badge-head">📌 오늘의 목표</div>',
                unsafe_allow_html=True)

    # 3-1) 목록 + 토글
    todos = st.session_state.user_data.get("todo_items", [])
    if not todos:
        st.caption("오늘 등록된 목표가 없습니다.")

    for i, item in enumerate(todos):
        # 체크 토글
        checked = st.checkbox(
            item["text"], value=item["done"], key=f"goal_chk_{item['id']}"
        )
        if checked != item["done"]:
            toggle_goal(item["id"], i, checked)
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        '''
        <div class="soft-bg" style="padding:16px 18px; margin-bottom:12px;">
        <div class="badge-head alt">💡 집중 팁</div>
        <ul style="margin:10px 0 0 0; font-size:1.03rem; padding-left:18px;">
            <li style="margin:6px 0;">눈을 자주 깜빡이세요</li>
            <li style="margin:6px 0;">물 한 잔 마시기</li>
            <li style="margin:6px 0;">스트레칭으로 전환</li>
        </ul>
        </div>
        ''',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="panel cam-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="panel-body">', unsafe_allow_html=True)

    spacer_l, cam_col, spacer_r = st.columns([0.10, 0.80, 0.27])

    with cam_col:
        st.markdown(
            f'''
            <div style="
                width:100%;
                max-width:{cam_disp_w}px;
                margin:0 auto;
                display:flex;
                align-items:center;
                justify-content:center;">
            ''',
            unsafe_allow_html=True
        )
        if st.session_state.start_camera and not st.session_state.ended:
            ctx = webrtc_streamer(
    key="camera",
    video_frame_callback=video_frame_callback,
    media_stream_constraints={
        "video": {"width": {"ideal": cam_cap_w}, "height": {"ideal": cam_cap_h}},
        "audio": False
    },
    async_processing=True,
    desired_playing_state=True  # 카메라 강제로 키기
)

            st.session_state.cam_active = bool(ctx) and getattr(ctx.state, "playing", False)
        else:
            st.session_state.cam_active = False
            st.markdown(
                f'<div style="width:{cam_disp_w}px; height:{cam_disp_h}px; background: transparent;"></div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-foot small-subtle">웹캠 연결 후 하품/졸음 감지를 통해 실시간으로 집중도를 계산합니다.</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="right-pane">', unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-body">', unsafe_allow_html=True)

    # from streamlit_autorefresh import st_autorefresh
    # with st.sidebar:
    #     st_autorefresh(interval=1000, key="auto_refresh")

    if st.session_state.get("cam_active"):
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=15000, key="auto_refresh_cam")

    update_pomodoro()
    remain_exact = st.session_state.pomodoro_duration - (time.time() - st.session_state.pomodoro_start)
    remaining = int(math.ceil(max(0, remain_exact)))
    remaining = min(remaining, int(st.session_state.pomodoro_duration))

    phase = (st.session_state.pomodoro_mode, st.session_state.pomodoro_duration)
    if st.session_state.get("last_phase") == phase:
        prev = st.session_state.get("last_remaining", remaining)
        if remaining < prev - 1:
            remaining = prev - 1
    st.session_state.last_phase = phase
    st.session_state.last_remaining = remaining

    mins, secs = divmod(remaining, 60)
    ratio = remaining / st.session_state.pomodoro_duration if st.session_state.pomodoro_duration > 0 else 0.0
    ratio = max(0.0, min(1.0, ratio))

    _now = time.time()
    if (
        st.session_state.get("pomodoro_mode") == "공부 중"
        and st.session_state.get("start_camera", False)
        and st.session_state.get("cam_active", False)
        and not st.session_state.get("break_active", False)
        and not st.session_state.get("ended", False)
    ):
        dt = int(max(0, _now - st.session_state.last_study_tick_ts))
        st.session_state.total_study_sec += dt

    st.session_state.last_study_tick_ts = _now

    if st.session_state.get("show_break_alert", False):
        st.markdown("""
        <style>
        .break-alert-overlay{
            position: fixed; top: 24px; left: 0; right: 0;
            display: flex; justify-content: center;
            z-index: 9999; pointer-events: none;
        }
        .break-alert-card{
            position: relative; pointer-events: auto;
            background: linear-gradient(135deg,#6F50E5, #FF9330);
            color: #fff; padding: 16px 22px; border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,.25), 0 0 0 6px rgba(255,255,255,.12) inset;
            animation: slideDown .45s ease, fadeOut .6s ease 6.5s forwards;
        }
        .break-alert-title{ font-weight: 900; font-size: 20px; letter-spacing: .2px; display: flex; align-items: center; gap: 8px; }
        .break-alert-sub{ font-size: 14px; opacity: .95; margin-top: 4px; }
        .sparkles{
            position: absolute; inset: -8px;
            background:
            radial-gradient(6px 6px at 20% 30%, rgba(255,255,255,.45), transparent 60%),
            radial-gradient(4px 4px at 70% 20%, rgba(255,255,255,.35), transparent 60%),
            radial-gradient(5px 5px at 40% 70%, rgba(255,255,255,.35), transparent 60%),
            radial-gradient(3px 3px at 85% 60%, rgba(255,255,255,.4),  transparent 60%);
            filter: blur(.3px); animation: twinkle 1.6s ease-in-out infinite alternate;
            border-radius: 16px; pointer-events: none;
        }
        @keyframes slideDown { from{ transform: translateY(-18px); opacity: 0 } to{ transform: translateY(0); opacity: 1 } }
        @keyframes fadeOut   { to{ opacity: 0; transform: translateY(-12px) } }
        @keyframes twinkle   { from{ opacity: .6 } to{ opacity: 1 } }
        </style>
        <div class="break-alert-overlay">
        <div class="break-alert-card">
            <div class="sparkles"></div>
            <div class="break-alert-title">⏰ 25분 경과!</div>
            <div class="break-alert-sub">5분 휴식이 시작됩니다</div>
        </div>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.show_break_alert = False

    if st.session_state.get("show_start_alert", False):
        st.markdown("""
        <style>
        .study-alert-overlay{
            position: fixed; top: 24px; left: 0; right: 0;
            display: flex; justify-content: center;
            z-index: 9999; pointer-events: none;
        }
        .study-alert-card{
            position: relative; pointer-events: auto;
            background: linear-gradient(135deg,#28C76F,#00CFE8);
            color: #fff; padding: 16px 22px; border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,.25), 0 0 0 6px rgba(255,255,255,.12) inset;
            animation: slideDown2 .45s ease, fadeOut2 .6s ease 6.5s forwards;
        }
        .study-alert-title{ font-weight: 900; font-size: 20px; letter-spacing: .2px; display: flex; align-items: center; gap: 8px; }
        .study-alert-sub{ font-size: 14px; opacity: .95; margin-top: 4px; }
        @keyframes slideDown2 { from{ transform: translateY(-18px); opacity: 0 } to{ transform: translateY(0); opacity: 1 } }
        @keyframes fadeOut2   { to{ opacity: 0; transform: translateY(-12px) } }
        </style>
        <div class="study-alert-overlay">
        <div class="study-alert-card">
            <div class="study-alert-title">📖 휴식 종료!</div>
            <div class="study-alert-sub">다시 집중해서 공부를 시작하세요 🚀</div>
        </div>
        </div>
        """, unsafe_allow_html=True)
        st.session_state.show_start_alert = False

    st.markdown(
        f'''
        <div class="soft-bg" style="padding:16px 18px; margin-bottom:10px;">
        <div class="badge-head">⏱️ 뽀모도로 타이머</div>
        <div style="margin:8px 0 10px 0; font-size:1.02rem;">
            <b>현재 상태:</b> <span>{st.session_state.pomodoro_mode}</span><br>
            <b>남은 시간:</b> <span>{mins:02d}:{secs:02d}</span>
        </div>
        ''',
        unsafe_allow_html=True
    )

    st.progress(ratio)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

    st.markdown('<div class="soft-bg" style="margin-bottom:10px;"><div class="badge-head alt">🧠 집중도</div></div>', unsafe_allow_html=True)

    st.session_state.focus_score = int(A.get("latest_attention", st.session_state.get("focus_score", 100)))
    if A.get("fatigue_bump", 0) > 0:
        st.session_state.fatigue_count += A["fatigue_bump"]
        A["fatigue_bump"] = 0

    st.progress(st.session_state.focus_score / 100)
    st.markdown(
        f"""<div style="margin-top:6px;" class="small-subtle">📊 점수: <b>{st.session_state.focus_score}</b> / 100</div>""",
        unsafe_allow_html=True
    )

    ss = st.session_state
    ss.setdefault("low_focus_since", None)
    ss.setdefault("rest_prompt_active", False)
    ss.setdefault("rest_cooldown_ts", 0.0)

    _now = time.time()
    _low_focus_threshold = 80
    _low_focus_sustain_sec = 5
    _low_focus_cooldown_sec = 180

    _h = int(st.session_state.total_study_sec // 3600)
    _m = int((st.session_state.total_study_sec % 3600) // 60)
    _s = int(st.session_state.total_study_sec % 60)

    st.markdown(
        f"""
        <div class="soft-bg" style="padding:12px 14px; margin-top:10px;">
        <div style="font-weight:900; margin-bottom:4px;">⏳ 누적 공부 시간</div>
        <div class="small-subtle"><b>{_h:02d}:{_m:02d}:{_s:02d}</b></div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ↓↓↓ 집중도 감지 + 모달 트리거(그대로 유지)
if not ss.get("break_active", False) and not ss.get("ended", False):
    if not ss.get("rest_prompt_active", False):
        if ss.focus_score <= _low_focus_threshold:
            if ss.low_focus_since is None:
                ss.low_focus_since = _now
            elif (_now - ss.low_focus_since >= _low_focus_sustain_sec) and (_now >= ss.rest_cooldown_ts):
                ss.rest_prompt_active = True
                ss.low_focus_since = None
            try:
                if ss.rest_prompt_active:
                    st.toast("⚠️ 집중도가 80 이하입니다. 5분 휴식을 시작할까요?")
            except Exception:
                if ss.rest_prompt_active:
                    st.warning("⚠️ 집중도가 80 이하입니다. 5분 휴식을 시작할까요?")
        else:
            ss.low_focus_since = None

if ss.get("rest_prompt_active", False):
    if hasattr(st, "dialog"):
        @st.dialog("집중도 낮음 • 5분 휴식할까요?")
        def __low_focus_dialog():
            st.markdown(
                f"현재 집중도는 <b>{ss.focus_score}</b> 입니다.<br>"
                f"5분간 휴식을 하면 이후 집중 효율이 좋아질 수 있어요.",
                unsafe_allow_html=True
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🛌 지금 5분 쉬기", key="btn_take_break_low_focus"):
                    start_break(seconds=5*60, reason="low_focus")
                    ss.rest_prompt_active = False
            with c2:
                if st.button("💪 계속 공부하기", key="btn_keep_studying_low_focus"):
                    ss.rest_prompt_active = False
                    ss.rest_cooldown_ts = time.time() + _low_focus_cooldown_sec
            st.caption("팁: 충분히 피곤하면 짧은 휴식이 전체 공부 효율을 높여줘요. (다음 알림은 3분 후)")
        __low_focus_dialog()
    elif hasattr(st, "experimental_dialog"):
        @st.experimental_dialog("집중도 낮음 • 5분 휴식할까요?")
        def __low_focus_dialog():
            st.markdown(
                f"현재 집중도는 <b>{ss.focus_score}</b> 입니다.<br>"
                f"5분간 휴식을 하면 이후 집중 효율이 좋아질 수 있어요.",
                unsafe_allow_html=True
            )
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🛌 지금 5분 쉬기", key="btn_take_break_low_focus"):
                    start_break(seconds=5*60, reason="low_focus")
                    ss.rest_prompt_active = False
            with c2:
                if st.button("💪 계속 공부하기", key="btn_keep_studying_low_focus"):
                    ss.rest_prompt_active = False
                    ss.rest_cooldown_ts = time.time() + _low_focus_cooldown_sec
            st.caption("팁: 충분히 피곤하면 짧은 휴식이 전체 공부 효율을 높여줘요. (다음 알림은 3분 후)")
        __low_focus_dialog()

    if st.session_state.fatigue_count >= 5:
        st.markdown(
            '<div style="color:#ff6b6b; font-weight:700; margin-top:10px;">⚠️ 졸음/하품이 반복적으로 감지되고 있어요! 잠시 쉬어보는 건 어떨까요?</div>',
            unsafe_allow_html=True
        )

if "last_study_tick_ts" not in st.session_state:
    st.session_state.last_study_tick_ts = _now

dt = int(max(0, _now - st.session_state.last_study_tick_ts))
st.session_state.total_study_sec += dt
st.session_state.last_study_tick_ts = _now

remaining = max(0, int(st.session_state.pomodoro_duration - (time.time() - st.session_state.pomodoro_start)))

# === 주기 저장 ===
now = time.time()
flush_events(force=False)
