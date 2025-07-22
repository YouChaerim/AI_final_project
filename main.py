import streamlit as st
from streamlit_webrtc import webrtc_streamer
import av
from EyeControl import detect_blink

st.set_page_config(page_title="📷 카메라 앱", layout="centered")

st.markdown("<h1 style='text-align: center;'>🎥 웹캠 보기</h1>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# 카메라 버튼 세션 상태 관리
if "start_camera" not in st.session_state:
    st.session_state["start_camera"] = False

col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🎬 카메라 켜기"):
        st.session_state["start_camera"] = True

# 프레임 처리 콜백 함수
def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    img = detect_blink(img)
    return av.VideoFrame.from_ndarray(img, format="bgr24")

# 스트리밍 시작
if st.session_state["start_camera"]:
    st.markdown("<h4 style='text-align: center;'>카메라 활성화 중... (눈 깜빡이면 Blink라고 뜸)</h4>", unsafe_allow_html=True)
    webrtc_streamer(
        key="camera",
        video_frame_callback=video_frame_callback,
        media_stream_constraints={
            "video": {
                "width": {"ideal": 1280}, # 해상도 설정
                "height": {"ideal": 720}
            },
            "audio": False
        },
        async_processing=True,
    )