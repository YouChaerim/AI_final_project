# 📁 파일명: pages/1_공부_시작.py
import streamlit as st
from streamlit_webrtc import webrtc_streamer
import av
import cv2
import time
from EyeControl import detect_blink
from YawnControl import detect_yawn

# ========================================
# 🧠 YOLO 모델 대신 사용할 더미 감지 함수
# ========================================
def detect_fatigue(img):
    cv2.putText(img, "Blinked", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 2)
    cv2.putText(img, "Yawning", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 0, 0), 2)
    return img, True, True

# ========================================
# ✅ 세션 상태 초기화
# ========================================
if "start_camera" not in st.session_state:
    st.session_state.start_camera = True  # ✅ 처음부터 카메라 자동 실행
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

# ========================================
# ⏱ 뽀모도로 타이머 업데이트
# ========================================
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

# ========================================
# 🎥 프레임 처리 콜백
# ========================================
# 프레임 처리 콜백 함수
def video_frame_callback(frame):
    img = frame.to_ndarray(format="bgr24")

    # 1. 눈 윤곽선/깜빡임 (img_blink = 눈 윤곽선까지 포함된 이미지)
    img_blink, is_blink = detect_blink(img.copy())

    # 2. 입 윤곽선/하품/ratio (img_final = 눈 + 입 폴리라인 모두 포함된 이미지)
    img_final, is_yawn, ratio = detect_yawn(img_blink)

    # 3. 텍스트 추가
    if is_blink:
        cv2.putText(img_final, "Blink!", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0,255,255), 3)
    if is_yawn:
        cv2.putText(img_final, "Yawning!", (30, 120), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0,0,255), 3)
    cv2.putText(img_final, f"Yawn Ratio: {ratio:.2f}", (30, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255,255,255), 2)

    return av.VideoFrame.from_ndarray(img_final, format="bgr24")





# ========================================
# 🖥 페이지 기본 설정
# ========================================
st.set_page_config(page_title="📚 공부 집중 모드", layout="centered")

# ========================================
# 🎨 CSS 스타일
# ========================================
st.markdown("""
<style>
.block-container {
    max-width: 1280px; /* 💻 노트북 기준 */
    padding-top: 2rem;
    padding-bottom: 4rem;
}
.orange-banner {
    background-color: #FFA726;
    padding: 30px;
    border-radius: 24px;
    text-align: center;
    color: white;
    font-size: 28px;
    font-weight: bold;
    margin-bottom: 30px;
}
.camera-box {
    ...
    display: flex;
    justify-content: center;
    align-items: center;  /* ✅ 수직 정렬 */
    flex-direction: column;
}


.card {
    background-color: #FFF8F0;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

# ========================================
# 🟧 상단 타이틀
# ========================================
st.markdown('<div class="orange-banner">📚 지금 공부 집중 모드가 활성화되었습니다</div>', unsafe_allow_html=True)

# ========================================
# 📐 3열 구성: 좌 | 중앙(카메라) | 우
# ========================================
col1, col2, col3 = st.columns([1, 2, 1])

# === 왼쪽: 오늘 목표 & 세션 ===
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📌 오늘의 목표")
    st.write("✔️ 단원 복습\n✔️ 문제 풀이\n✔️ 암기 테스트")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🍅 세션 현황")
    st.write("🍅🍅")
    st.markdown('</div>', unsafe_allow_html=True)

# === 중앙: 카메라 자동 실행 ===
with col2:
    st.markdown('<div class="camera-box">', unsafe_allow_html=True)

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

# === 오른쪽: 타이머 & 집중도 & 팁 ===
with col3:
    update_pomodoro()
    remaining = max(0, int(st.session_state.pomodoro_duration - (time.time() - st.session_state.pomodoro_start)))
    mins, secs = divmod(remaining, 60)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ⏱️ 뽀모도로 타이머")
    st.info(f"현재 상태: {st.session_state.pomodoro_mode}")
    st.write(f"⏰ 남은 시간: **{mins:02d}:{secs:02d}**")
    st.progress(remaining / st.session_state.pomodoro_duration)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🧠 집중도")
    st.progress(st.session_state.focus_score)
    st.write(f"📊 점수: {st.session_state.focus_score} / 100")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.fatigue_count >= 5:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.error("⚠️ 졸음/하품이 반복적으로 감지되고 있어요!\n잠시 쉬어보는 건 어떨까요?")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 💡 집중 팁")
    st.markdown("- 눈을 자주 깜빡이세요\n- 물 한 잔 마시기\n- 스트레칭으로 전환")
    st.markdown('</div>', unsafe_allow_html=True)

    st.button("🔁 타이머 초기화")
