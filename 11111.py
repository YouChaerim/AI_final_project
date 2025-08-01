import streamlit as st
import sys
st.write(sys.executable)
from streamlit_webrtc import webrtc_streamer
import av
import cv2
import time
import sys
import os
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from EyeControl import detect_blink
from YawnControl import detect_yawn

# 세션 및 다크모드 초기화
if "user_data" not in st.session_state:
    if os.path.exists("user_data.json"):
        import json
        with open("user_data.json", "r", encoding="utf-8") as f:
            st.session_state.user_data = json.load(f)
    else:
        st.session_state.user_data = {"dark_mode": False}

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = st.session_state.user_data.get("dark_mode", False)

if st.session_state.dark_mode:
    bg_color = "#1C1C1E"; font_color = "#F2F2F2"
    nav_bg = "#2C2C2E"; card_bg = "#2C2C2E"; hover_bg = "#3A3A3C"
else:
    bg_color = "#FAFAFA"; font_color = "#333"
    nav_bg = "rgba(255,255,255,0.9)"; card_bg = "white"; hover_bg = "#F5F5F5"

st.set_page_config(page_title="딸깍공 - 공부 집중모드", layout="wide", initial_sidebar_state="collapsed")

# ===== 스타일 적용 =====
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
header {{ display: none !important; }}
.camera-fixed {{
    width: 100%;
    max-width: 720px;
    height: 340px;
    background: #E4E4E4;
    border-radius: 16px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto;
}}
</style>
""", unsafe_allow_html=True)

# ===== 세션 상태 초기화 =====
if "start_camera" not in st.session_state:
    st.session_state.start_camera = False
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

# ===== 상단 컨테이너 시작 =====
st.markdown('<div class="container">', unsafe_allow_html=True)

# ===== 네비게이션 바 (생략 가능 시 주석) =====
st.markdown("""
<div style="margin-bottom:32px;">
    <div style="font-size:28px; font-weight:bold;">🐾 딸깍공</div>
</div>
""", unsafe_allow_html=True)

# ===== 컬럼 레이아웃 =====
col1, col2, col3 = st.columns([1, 2.3, 1])

with col1:
    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
    st.markdown("""
        <h3>📌 오늘의 목표</h3>
        <ul style="font-size:1.2rem;">
            <li>✔️ 단원 복습</li>
            <li>✔️ 문제 풀이</li>
            <li>✔️ 암기 테스트</li>
        </ul>
        <h4>💡 집중 특가</h4>
        <ul>
            <li>눈을 자주 깜빡이기</li>
            <li>물 한 잔 마시기</li>
            <li>스트레칭으로 전환</li>
        </ul>
    """, unsafe_allow_html=True)

with col3:
    def update_pomodoro():
        elapsed = time.time() - st.session_state.pomodoro_start
        if elapsed > st.session_state.pomodoro_duration:
            if st.session_state.pomodoro_mode == "공부 중":
                st.session_state.pomodoro_mode = "휴식 중"
                st.session_state.pomodoro_duration = 5 * 60
            else:
                st.session_state.pomodoro_mode = "공부 중"
                st.session_state.pomodoro_duration = 25 * 60
            st.session_state.pomodoro_start = time.time()

    update_pomodoro()
    remaining = max(0, int(st.session_state.pomodoro_duration - (time.time() - st.session_state.pomodoro_start)))
    mins, secs = divmod(remaining, 60)

    st_autorefresh(interval=1000, key="auto_refresh")
    st.markdown(f"""
        <h3>⏱️ 뽀모도로 타이머</h3>
        <div>현재 상태: <b>{st.session_state.pomodoro_mode}</b></div>
        <div>남은 시간: <b>{mins:02d}:{secs:02d}</b></div>
    """, unsafe_allow_html=True)
    st.progress(remaining / st.session_state.pomodoro_duration if st.session_state.pomodoro_duration > 0 else 0.0)
    st.markdown(f"""
        <h4>🧠 집중도</h4>
        <div>📊 점수: {st.session_state.focus_score} / 100</div>
    """, unsafe_allow_html=True)
    st.progress(st.session_state.focus_score / 100)

    if st.session_state.fatigue_count >= 5:
        st.markdown('<div style="color:#ff5555;">⚠️ 졸음/하품이 반복적으로 감지되고 있어요! 잠시 쉬어보는 건 어떨까요?</div>', unsafe_allow_html=True)

# ===== 카메라 영역 중앙 배치 =====
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<center>", unsafe_allow_html=True)

if not st.session_state.start_camera:
    if st.button("📷 공부 시작 (카메라 ON)", key="start_btn", use_container_width=True):
        st.session_state.start_camera = True

if st.session_state.start_camera:
    st.markdown('<div class="camera-fixed">', unsafe_allow_html=True)

    def video_frame_callback(frame):
        img = frame.to_ndarray(format="bgr24")
        img_blink, is_blink = detect_blink(img.copy())
        img_final, is_yawn, ratio = detect_yawn(img_blink)
        if is_blink:
            cv2.putText(img_final, "Blink!", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0,255,255), 3)
        if is_yawn:
            cv2.putText(img_final, "Yawning!", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0,0,255), 3)
        cv2.putText(img_final, f"Yawn Ratio: {ratio:.2f}", (30, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), 2)
        return av.VideoFrame.from_ndarray(img_final, format="bgr24")

    webrtc_streamer(
        key="camera",
        video_frame_callback=video_frame_callback,
        media_stream_constraints={"video": {"width": {"ideal": 720}, "height": {"ideal": 340}}, "audio": False},
        async_processing=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("</center>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

