import streamlit as st
from streamlit_webrtc import webrtc_streamer
import av
from EyeControl import detect_blink

st.set_page_config(page_title="딸깍공 - 공부 집중모드", layout="wide", initial_sidebar_state="collapsed")

# ===== 다크모드 색상 처리 =====
dark_mode = st.session_state.get("user_data", {}).get("dark_mode", False)
bg_color = "#1C1C1E" if dark_mode else "#FFFFFF"
font_color = "#F2F2F2" if dark_mode else "#1C1C1E"
card_color = "#2C2C2E" if dark_mode else "#F5F6FA"

# ===== 헤더 =====
st.markdown(f"""
    <div class='top-nav' style="background-color: {bg_color}; padding: 16px 0 8px 0; border-bottom: 1px solid #ccc;">
        <div style='max-width: 960px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center;'>
            <div style="font-size: 24px; font-weight: bold; color: {font_color};">🐾 딸깍공</div>
            <div style="display: flex; gap: 20px; font-weight: 600; color: {font_color}; font-size: 16px;">
                <div>메인페이지</div><div>공부 시작</div><div>필기</div><div>저장폴더</div>
                <div>퀴즈</div><div>리포트</div><div>랭킹</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ===== 빈 공간 여백 =====
st.markdown(f"<div style='background-color:{bg_color}; height: 20px;'></div>", unsafe_allow_html=True)

# ===== 카메라 박스 중앙 상단 배치 =====
if "start_camera" not in st.session_state:
    st.session_state["start_camera"] = False

with st.container():
    st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
    if st.button("🎬 카메라 켜기"):
        st.session_state["start_camera"] = True
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state["start_camera"]:
        st.markdown(f"""
            <div style='margin-top:10px; text-align:center; color:{font_color}; font-size:16px;'>
                카메라 활성화 중... (눈 깜빡이면 Blink라고 뜹니다)
            </div>
        """, unsafe_allow_html=True)

        webrtc_streamer(
            key="camera",
            video_frame_callback=lambda frame: av.VideoFrame.from_ndarray(
                detect_blink(frame.to_ndarray(format="bgr24")), format="bgr24"
            ),
            media_stream_constraints={
                "video": {"width": {"ideal": 640}, "height": {"ideal": 360}},
                "audio": False,
            },
            async_processing=True,
        )

# ===== 하단 3컬럼 레이아웃 (카메라 아래) =====
col1, col2, col3 = st.columns([1.5, 1.5, 2])

with col1:
    st.markdown(f"<h3 style='color: {font_color};'>📌 오늘의 목표</h3>", unsafe_allow_html=True)
    st.markdown(f"""
        <ul style="color: {font_color}; font-size: 18px;">
            <li>✔️ 단원 복습</li>
            <li>✔️ 문제 풀이</li>
            <li>✔️ 암기 테스트</li>
        </ul>
    """, unsafe_allow_html=True)

    st.markdown(f"<h4 style='color: {font_color}; margin-top:30px;'>💡 집중 특가</h4>", unsafe_allow_html=True)
    st.markdown(f"""
        <ul style="color: {font_color}; font-size: 16px;">
            <li>눈을 자주 깜빡이세요</li>
            <li>물 한 잔 마시기</li>
            <li>스트레칭으로 전환</li>
        </ul>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"<h3 style='color: {font_color};'>⏱️ 뽀모도로 타이머</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{font_color}; font-size: 16px;'>현재 상태: 공부 중<br>남은 시간: 24:49</p>", unsafe_allow_html=True)
    st.progress(100)

    st.markdown(f"<h4 style='margin-top:30px; color:{font_color};'>🧠 집중도</h4>", unsafe_allow_html=True)
    st.progress(100)
    st.markdown(f"<p style='color:{font_color};'>📊 점수: 100 / 100</p>", unsafe_allow_html=True)

# col3는 비워둠 or 추후 확장용

