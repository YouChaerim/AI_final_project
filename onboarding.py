# onboarding.py (B안: 로그인 전용 + 성공 시 pages/mainpage.py로 전환)
import streamlit as st
import os
import requests
import time
from components.auth import remember_login

# --- 기본 설정 및 백엔드 URL ---
st.set_page_config(page_title="딸깍공", layout="wide", initial_sidebar_state="collapsed")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")

# --- 세션 상태 기본값 (재설정 금지: setdefault만 사용) ---
st.session_state.setdefault("view", "onboarding")
st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("user", {})

# --- 이미 로그인된 경우: 곧바로 메인 페이지로 ---
if st.session_state.get("logged_in", False):
    st.switch_page("pages/mainpage.py")
    st.stop()

# --- 공통 함수 ---
def logout():
    # (실제 페이지들에서 사용 예정. 여기선 참고용)
    st.session_state["logged_in"] = False
    st.session_state["user"] = {}
    st.session_state["view"] = "login"
    st.success("로그아웃 되었습니다.")
    time.sleep(1)
    st.rerun()

# --- 1. 온보딩 화면 UI ---
def show_onboarding_ui():
    st.markdown("""
    <style>
    .main .block-container { max-width: 1000px; margin: 0 auto; }
    [data-testid="stSidebar"], [data-testid="stSidebarNav"], [data-testid="stToolbar"] { display: none !important; }
    .block-container { padding-top: 2rem; padding-left: 2rem; padding-right: 2rem; }
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
    html, body { font-family: 'Noto Sans KR', sans-serif; background-color: #FFF8F0; }
    .title { font-size: 28px; font-weight: bold; text-align: center; margin-top: 40px; margin-bottom: 20px; color: #222; }
    .card-container { display: flex; justify-content: center; gap: 36px; margin: 20px 0 20px 0; }
    .card { background-color: white; border-radius: 18px; padding: 30px 20px; width: 280px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); text-align: center; }
    .circle { background-color: #FFA741; color: white; border-radius: 50%; width: 36px; height: 36px; display: inline-flex; align-items: center; justify-content: center; font-size: 16px; margin-bottom: 14px; }
    .card-title { font-size: 20px; font-weight: 700; margin-bottom: 8px; }
    .card-desc { font-size: 16px; color: #666; line-height: 1.6; }
    .start-btn { display: flex; justify-content: center; margin-top: 30px; }
    .start-btn a { text-decoration: none; }
    button.start { background-color: #FFA741; border: none; padding: 18px 48px; border-radius: 14px; font-size: 22px; font-weight: bold; color: white; cursor: pointer; transition: 0.2s; }
    button.start:hover { background-color: #FF9329; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="title">🐾 딸깍공에 오신 걸 환영해요!</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="card-container">
      <div class="card"><div class="circle">1</div><div class="card-title">공부 목표 설정</div><div class="card-desc">목표를 도달하며<br>성취감을 느껴요!</div></div>
      <div class="card"><div class="circle">2</div><div class="card-title">뽀모도로 기법 체험</div><div class="card-desc">25분 공부하고 5분 쉬며<br>몰입해요!</div></div>
      <div class="card"><div class="circle">3</div><div class="card-title">피드백리포트 받아보기</div><div class="card-desc">리포트를 보며<br>공부 패턴을 분석해요!</div></div>
    </div>
    """, unsafe_allow_html=True)

    # 원래 UI 유지: ?view=login으로 전환 신호만 보냄 (같은 파일 내에서만 사용)
    st.markdown("""
    <div class="start-btn">
      <a href="?view=login" target="_self">
        <button class="start">시작하기</button>
      </a>
    </div>
    """, unsafe_allow_html=True)

# --- 2. 로그인 화면 UI ---
def show_login_ui():
    st.markdown("""
        <style>
        .main .block-container { max-width: 480px; margin: 0 auto; }
        [data-testid="stForm"] { width: 840px; margin: 0 auto; }
        [data-testid="stFormSubmitButton"] button { width: 100%; }
        header, [data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu { display: none !important; }
        [data-testid="stSidebar"], [data-testid="stSidebarNav"] { display: none !important; }
        html, body, [class*="css"] { font-size: 15px; }
        body, .block-container, .main, .stApp { padding-top: 0 !important; margin-top: 0 !important; }
        .main-container { margin-top: 10vh; }
        .logo-box { display:flex; justify-content:center; align-items:center; font-size:2.3rem; font-weight:bold; margin-bottom:0.6rem; color:#FFA500; }
        .paw-icon { font-size:2rem; margin-right:0.4rem; }
        .stTextInput > div > input { margin-top: 8; padding:4; font-size:0.95rem; border-radius:6px; border:2px solid #FFA500; background-color:#F4F6FA; }
        [data-testid="stFormSubmitButton"] button { padding:0.8rem; border-radius:0.6rem; font-weight:700; font-size:1rem; background-color:#FFF5E5; color:#FFA500; border:2px solid #FFA500; }
        .social-login { text-align:center; margin-top:2rem; font-size:1.07rem; color:#111; font-weight:bold; margin-bottom:1.2rem; letter-spacing:.02em; }
        .simple-login-row { display:flex; justify-content:center; align-items:center; gap:24px; margin:16px 0 22px 0; }
        .simple-login-icon { width:48px; height:48px; border-radius:50%; box-shadow:0 2px 10px rgba(0,0,0,.06); background:#fff; display:flex; align-items:center; justify-content:center; transition:box-shadow .2s; }
        .simple-login-icon:hover { box-shadow:0 4px 16px rgba(0,0,0,.10); background:#f5f5f5; }
        .simple-login-icon img { width:28px; height:28px; object-fit:contain; }
        .footer-links { text-align:center; margin-top:2.5rem; font-size:1rem; font-weight:600; }
        .footer-links a, .footer-links span { margin:0 12px; color:#333; text-decoration:underline; cursor:pointer; }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        st.markdown('<div class="logo-box"><span class="paw-icon">🐾</span>딸깍공</div>', unsafe_allow_html=True)
        with st.form("local_login_form"):
            user_id_input = st.text_input("아이디", placeholder="아이디", label_visibility="collapsed")
            user_pw_input = st.text_input("비밀번호", type="password", placeholder="비밀번호", label_visibility="collapsed")
            login_clicked = st.form_submit_button("로그인")

        if login_clicked:
            if user_id_input and user_pw_input:
                try:
                    res = requests.post(f"{BACKEND_URL}/auth/local/login",
                                        json={
                                                "user_id": user_id_input,
                                                "password": user_pw_input
                                            }, timeout=10)
                    if res.status_code == 200:
                        data = res.json()
                        if data.get("result") == "ok":
                            # ✅ 백엔드가 내려주는 토큰 키 예상 대응
                            token = data.get("token") or data.get("access_token") or data.get("jwt") or ""
                            profile = data.get("profile", {})

                            # ✅ 세션/URL에 토큰까지 저장
                            remember_login(user=data.get("user", {}), token=token, profile=profile, set_qp=True)

                            st.switch_page("pages/mainpage.py"); st.stop()
                        else:
                            st.error(data.get("message", "아이디 또는 비밀번호가 올바르지 않습니다."))
                    else:
                        st.error("로그인에 실패했습니다. 서버 응답을 확인하세요.")
                except requests.exceptions.RequestException as e:
                    st.error(f"서버 연결에 실패했습니다: {e}")
            else:
                st.warning("아이디와 비밀번호를 모두 입력해주세요.")

        st.markdown('<div class="social-login">간편 로그인</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="simple-login-row">
            <div class="simple-login-icon">
                <img src="https://img.icons8.com/ios-filled/50/000000/mac-os.png" alt="apple">
            </div>
            <a class="simple-login-icon" href="{BACKEND_URL}/auth/kakao/login">
                <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/KakaoTalk_logo.svg/512px-KakaoTalk_logo.svg.png" alt="kakao">
            </a>
            <div class="simple-login-icon">
                <img src="https://img.icons8.com/fluency/48/000000/instagram-new.png" alt="insta">
            </div>
            <div class="simple-login-icon">
                <img src="https://img.icons8.com/color/48/000000/google-logo.png" alt="google">
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="footer-links">
            <span>아이디 찾기</span> | <span>비밀번호 찾기</span> | <a href="?go=join">회원가입</a>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 회원가입 딥링크 처리
    qp = st.query_params
    if qp.get("go") == "join":
        st.query_params.clear()
        st.switch_page("pages/join.py")

# --- 3. 메인 라우팅 로직 (onboarding 파일 내부에서만 사용되는 전환) ---

# 온보딩 → 로그인 전환 (?view=login)
if st.query_params.get("view") == "login":
    st.session_state["view"] = "login"
    st.query_params.clear()
    st.rerun()

# 카카오 로그인 콜백 (?login=success&user_id=...&nickname=...&provider=...)
qp = st.query_params
if qp.get("login") == "success" and not st.session_state.get("logged_in", False):
    token = qp.get("token") or ""
    user_id = qp.get("user_id")
    nickname = qp.get("nickname")
    provider = qp.get("provider")
    if user_id:
        user = {"id": user_id, "nickname": nickname, "provider": provider}
        # ✅ 소셜 로그인도 동일하게 토큰 저장 + URL 유지
        remember_login(user=user, token=token, profile={}, set_qp=True)
        st.query_params.clear()
        st.switch_page("pages/mainpage.py"); st.stop()

# --- 4. 최종 렌더링 ---
if st.session_state.get("view") == "onboarding":
    show_onboarding_ui()
else:  # 'login'
    show_login_ui()
