import streamlit as st

# ✅ 페이지 설정
st.set_page_config(page_title="딸깍공 로그인", layout="centered")

# ✅ CSS 스타일 정의 (조금 더 내려서 위치 조정)
st.markdown("""
    <style>
    /* ✅ 기본 헤더 제거 */
    header, [data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu {
        display: none !important;
    }

    html, body, [class*="css"] { font-size: 15px; }
    body, .block-container, .main, .stApp {
        padding-top: 0 !important;
        margin-top: 0 !important;
        background-color: #fff;
    }

    /* ✅ 메인 컨테이너 위치 살짝 더 아래로 */
    .main-container {
        margin-top: 10vh;
    }

    .logo-box {
        display: flex; justify-content: center; align-items: center;
        font-size: 2.3rem; font-weight: bold; margin-bottom: 0.6rem; color: #FFA500;
    }

    .paw-icon { font-size: 2rem; margin-right: 0.4rem; }

    .stTextInput > div > input {
        padding: 0.8rem; font-size: 0.95rem; border-radius: 6px;
        border: 2px solid #FFA500; background-color: #F4F6FA;
    }

    .login-btn {
        font-weight: bold; width: 100%; padding: 0.8rem; border-radius: 0.6rem;
        margin-top: 1rem; font-size: 1rem;
        background-color: #FFF5E5; color: #FFA500; border: 2px solid #FFA500;
    }

    .checkbox-box { margin-top: 0.4rem; margin-bottom: 1.2rem; }

    .social-login {
        text-align: center; margin-top: 2rem; font-size: 1.07rem; color: #111; font-weight: bold;
        margin-bottom: 1.2rem; letter-spacing: 0.02em;
    }

    .simple-login-row {
        display: flex; flex-direction: row; justify-content: center; align-items: center;
        gap: 24px; margin: 16px 0 22px 0;
    }

    .simple-login-icon {
        width: 48px; height: 48px; border-radius: 50%;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        background: #fff;
        display: flex; align-items: center; justify-content: center;
        transition: box-shadow 0.2s;
    }

    .simple-login-icon:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.10);
        background: #f5f5f5;
    }

    .simple-login-icon img {
        width: 28px; height: 28px; object-fit: contain;
    }

    .footer-links {
        text-align: center; margin-top: 2.5rem; font-size: 1rem; font-weight: 600;
    }

    .footer-links span {
        margin: 0 12px; color: #333; text-decoration: underline; cursor: pointer;
    }
    </style>
""", unsafe_allow_html=True)

# ✅ 메인 UI 컨테이너
with st.container():
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # ✅ 타이틀 + 로고
    st.markdown("""
    <div class="logo-box">
        <span class="paw-icon">🐾</span>
        딸깍공
    </div>
    """, unsafe_allow_html=True)

    # ✅ 입력 필드
    user_id = st.text_input("아이디", label_visibility="collapsed")
    user_pw = st.text_input("비밀번호", type="password", label_visibility="collapsed")

    # ✅ 로그인 버튼
    st.markdown('<button class="login-btn">로그인</button>', unsafe_allow_html=True)

    # ✅ 로그인 상태 유지 체크박스
    st.markdown('<div class="checkbox-box">', unsafe_allow_html=True)
    stay_logged_in = st.checkbox("로그인 상태 유지", value=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ✅ 간편 로그인 텍스트
    st.markdown('<div class="social-login">간편 로그인</div>', unsafe_allow_html=True)

    # ✅ 간편 로그인 아이콘
    st.markdown("""
    <div class="simple-login-row">
        <div class="simple-login-icon">
            <img src="https://img.icons8.com/ios-filled/50/000000/mac-os.png" alt="apple">
        </div>
        <div class="simple-login-icon">
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/KakaoTalk_logo.svg/512px-KakaoTalk_logo.svg.png" alt="kakao">
        </div>
        <div class="simple-login-icon">
            <img src="https://img.icons8.com/fluency/48/000000/instagram-new.png" alt="insta">
        </div>
        <div class="simple-login-icon">
            <img src="https://img.icons8.com/color/48/000000/google-logo.png" alt="google">
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ✅ 하단 링크
    st.markdown("""
    <div class="footer-links">
        <span>비밀번호 찾기</span> | <span>아이디 찾기</span> | <span>회원가입</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
