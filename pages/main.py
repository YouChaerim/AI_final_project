import streamlit as st
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
    dark_orange = "#FF9330"
else:
    bg_color = "#FAFAFA"; font_color = "#333"
    nav_bg = "rgba(255,255,255,0.9)"; card_bg = "white"; hover_bg = "#F5F5F5"
    dark_orange = "#FF9330"

st.set_page_config(page_title="딸깍공 - 공부 집중모드", layout="wide", initial_sidebar_state="collapsed")

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
.nav-menu div a {{
    color: #000 !important;
    transition: all 0.2s ease;
}}
.nav-menu div:hover a {{
    color: #FF9330 !important;
}}
.profile-group {{
    display: flex;
    gap: 16px;
    align-items: center;
}}
.profile-icon {{
    background-color: #888;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    cursor: pointer;
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
      <div><a href="/ocr_paddle"       target="_self">필기</a></div>
      <div><a href="/folder_page"   target="_self">저장폴더</a></div>
      <div><a href="/quiz"       target="_self">퀴즈</a></div>
      <div><a href="/report"     target="_self">리포트</a></div>
      <div><a href="/ranking"       target="_self">랭킹</a></div>
    </div>
  </div>
  <div class="profile-group">
    <div class="profile-icon" title="내 프로필"></div>
  </div>
</div>
""", unsafe_allow_html=True)

if "start_camera" not in st.session_state:
    st.session_state.start_camera = True
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

col1, col2, col3 = st.columns([1, 2.3, 1])

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
        <span style="font-size:1.7rem; font-weight:700; vertical-align:middle; margin-left:8px;">집중 특가</span>
        <ul style="margin-top:13px; font-size:1.18rem; padding-left:22px;">
            <li>눈을 자주 깜빡이세요</li>
            <li>물 한 잔 마시기</li>
            <li>스트레칭으로 전환</li>
        </ul>
        ''',
        unsafe_allow_html=True
    )

# ----------- 핵심! col2 카메라 영역 높이/길이 완벽 일치 -----------
cam_height = 390    # 이 값만 조정하면 됩니다! (390~410 사이 권장)
cam_width = 920     # col2 너비에 맞게(적당히 900~960 정도)

with col2:
    st.markdown(
        f'''
        <div style="width:{cam_width}px;height:{cam_height}px;display:flex;align-items:center;justify-content:center;margin:0 auto 0 auto;padding:0;">
        ''',
        unsafe_allow_html=True
    )
    if st.session_state["start_camera"]:
        webrtc_streamer(
            key="camera",
            video_frame_callback=video_frame_callback,
            media_stream_constraints={
                "video": {"width": {"ideal": cam_width}, "height": {"ideal": cam_height}}, "audio": False
            },
            async_processing=True,
        )
    else:
        st.markdown(
            f'<div style="width:{cam_width}px; height:{cam_height}px; background: transparent;"></div>',
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    update_pomodoro()
    remaining = max(0, int(st.session_state.pomodoro_duration - (time.time() - st.session_state.pomodoro_start)))
    mins, secs = divmod(remaining, 60)
    st_autorefresh(interval=1000, key="auto_refresh")
    
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
    
    st.markdown(
        f"""
        <span style="font-size:2.0rem; vertical-align:middle;">🧠</span>
        <span style="font-size:1.7rem; font-weight:700; vertical-align:middle; margin-left:8px;">집중도</span>
        """,
        unsafe_allow_html=True
    )
    st.progress(st.session_state.focus_score / 100)
    st.markdown(
        f"""<span style="font-size:1.13rem;">📊 점수: {st.session_state.focus_score} / 100</span>""",
        unsafe_allow_html=True
    )

    if st.session_state.fatigue_count >= 5:
        st.markdown(
            '<div style="color:#ff5555; font-weight:700; margin-top:10px;">⚠️ 졸음/하품이 반복적으로 감지되고 있어요!<br>잠시 쉬어보는 건 어떨까요?</div>',
            unsafe_allow_html=True
        )

st.markdown('</div>', unsafe_allow_html=True)
