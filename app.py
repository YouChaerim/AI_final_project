import streamlit as st
import base64

st.set_page_config(page_title="딸깍공", layout="wide")

st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-size: 17px !important;  /* ✅ 110% 확대 느낌 */
        }

        .navbar {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 24px 0px;
            background-color: white;
            border-bottom: 1px solid #eee;
        }

        .navbar-inner {
            display: flex;
            align-items: center;
            gap: 65px;  /* ✅ 약간 여유있게 */
        }

        .logo-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .logo-icon {
            font-size: 26px;
            color: #6A1B9A;
        }

        .logo-text {
            font-size: 30px;
            font-weight: 900;
            color: #FF6600;
        }

        .nav-links {
            display: flex;
            gap: 65px;
            font-size: 17px;
            color: #333;
            font-weight: 500;
            white-space: nowrap;
        }

        .profile-icon {
            font-size: 24px;
            color: #6A1B9A;
        }

        .icon-container {
            display: flex;
            justify-content: center;
            gap: 70px;
            margin-top: 90px;
        }

        .icon-card {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            width: 240px;
            height: 240px;
            border: 1px solid #eee;
            border-radius: 20px;
            padding: 22px;
            background-color: #fff;
            box-shadow: 1px 1px 10px rgba(0,0,0,0.04);
            cursor: pointer;
            transition: all 0.2s ease-in-out;
        }

        .icon-card:hover {
            background-color: #f9f9f9;
            transform: scale(1.04);
        }

        .icon-card img {
            height: 88px;
            margin-bottom: 16px;
        }

        .icon-card div {
            font-size: 17px;
            font-weight: 500;
            color: #111;
        }
    </style>
""", unsafe_allow_html=True)

# 상단 네비게이션
st.markdown(f"""
<div class="navbar">
    <div class="navbar-inner">
        <div class="logo-group">
            <div class="logo-icon">🐾</div>
            <div class="logo-text">딸깍공</div>
        </div>
        <div class="nav-links">
            <div>메인페이지</div>
            <div>공부 시작</div>
            <div>필기</div>
            <div>저장폴더</div>
            <div>퀴즈</div>
            <div>리포트(피드백)</div>
            <div>공지</div>
        </div>
        <div class="profile-icon">👤</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 이미지 → base64 변환 함수
def load_base64(path):
    try:
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return ""  # 이미지 없으면 빈 문자열 반환

# 카드 UI
# 카드 UI
st.markdown(f"""
<div class="icon-container">
    <div class="icon-card">
        <img src="data:image/png;base64,{load_base64('assets/pen.png')}">
        <div>필기인식</div>
    </div>
    <div class="icon-card">
        <img src="data:image/png;base64,{load_base64('assets/icon_folder.png')}">
        <div>폴더</div>
    </div>
    <div class="icon-card">
        <img src="data:image/png;base64,{load_base64('assets/quiz.png')}">
        <div>복습용 퀴즈</div>
    </div>
</div>
""", unsafe_allow_html=True)

