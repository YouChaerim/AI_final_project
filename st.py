import streamlit as st
from streamlit_webrtc import webrtc_streamer
import av

# 페이지 설정
st.set_page_config(page_title="📷 카메라 앱", layout="centered")

st.markdown("<h1 style='text-align: center;'>🎥 웹캠 보기</h1>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# 세션 상태를 사용해 버튼 누른 상태 저장
if "start_camera" not in st.session_state:
    st.session_state["start_camera"] = False

# 버튼 중앙 배치
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🎬 카메라 켜기"):
        st.session_state["start_camera"] = True

# 카메라 스트리밍 함수 정의
def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")
    return av.VideoFrame.from_ndarray(img, format="bgr24")

# 버튼 누르면 카메라 시작
if st.session_state["start_camera"]:
    st.markdown("<h4 style='text-align: center;'>카메라 활성화 중...</h4>", unsafe_allow_html=True)
    webrtc_streamer(
        key="camera",
        video_frame_callback=video_frame_callback,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )
