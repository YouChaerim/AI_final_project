# pages/login_page.py
import streamlit as st
import os
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8080")

# ✅ 페이지 설정 (사이드바 기본 접기)
st.set_page_config(page_title="딸깍공 로그인", layout="centered", initial_sidebar_state="collapsed")

# ✅ CSS 스타일 정의 (사이드바/헤더 완전 숨김 + 기존 스타일 유지)
st.markdown("""
    <style>
    /* 헤더/툴바/메뉴 숨김 */
    header, [data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu { display: none !important; }
    /* 사이드바 완전 숨김 */
    [data-testid="stSidebar"], [data-testid="stSidebarNav"] { display: none !important; }

    html, body, [class*="css"] { font-size: 15px; }
    body, .block-container, .main, .stApp { padding-top: 0 !important; margin-top: 0 !important; }
    .main-container { margin-top: 10vh; }

    .logo-box { display:flex; justify-content:center; align-items:center; font-size:2.3rem; font-weight:bold; margin-bottom:0.6rem; color:#FFA500; }
    .paw-icon { font-size:2rem; margin-right:0.4rem; }

    .stTextInput > div > input { padding:0.8rem; font-size:0.95rem; border-radius:6px; border:2px solid #FFA500; background-color:#F4F6FA; }
    .login-btn-wrap button { width:100%; padding:0.8rem; border-radius:0.6rem; font-weight:700; font-size:1rem; background-color:#FFF5E5; color:#FFA500; border:2px solid #FFA500; }

    .checkbox-box { margin-top:0.4rem; margin-bottom:1.2rem; }
    .social-login { text-align:center; margin-top:2rem; font-size:1.07rem; color:#111; font-weight:bold; margin-bottom:1.2rem; letter-spacing:.02em; }
    .simple-login-row { display:flex; justify-content:center; align-items:center; gap:24px; margin:16px 0 22px 0; }
    .simple-login-icon { width:48px; height:48px; border-radius:50%; box-shadow:0 2px 10px rgba(0,0,0,.06); background:#fff; display:flex; align-items:center; justify-content:center; transition:box-shadow .2s; }
    .simple-login-icon:hover { box-shadow:0 4px 16px rgba(0,0,0,.10); background:#f5f5f5; }
    .simple-login-icon img { width:28px; height:28px; object-fit:contain; }

    .footer-links { text-align:center; margin-top:2.5rem; font-size:1rem; font-weight:600; }
    .footer-links a, .footer-links span { margin:0 12px; color:#333; text-decoration:underline; cursor:pointer; }
    </style>
""", unsafe_allow_html=True)

def _go_main():
    """루트의 main_page.py 또는 mainpage.py를 실행하는 pages/mainpage.py 래퍼로 이동"""
    try:
        st.switch_page("pages/mainpage.py")
    except Exception:
        try:
            st.switch_page("pages/main_page.py")
        except Exception:
            st.error("메인 페이지로 이동할 수 없습니다. pages/mainpage.py 래퍼가 있는지 확인하세요.")
            st.stop()

def _go_join():
    """루트의 join.py를 실행하는 pages/join.py 래퍼로 이동"""
    try:
        st.switch_page("pages/join.py")
    except Exception:
        st.error("회원가입 페이지로 이동할 수 없습니다. pages/join.py 래퍼가 있는지 확인하세요.")
        st.stop()

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

    # ✅ 로컬 로그인 폼
    st.markdown('<div class="login-btn-wrap">', unsafe_allow_html=True)
    with st.form("local_login_form", clear_on_submit=False):
        user_id = st.text_input("아이디", label_visibility="collapsed", key="local_login_id")
        user_pw = st.text_input("비밀번호", type="password", label_visibility="collapsed", key="local_login_pw")
        login_clicked = st.form_submit_button("로그인")
    st.markdown('</div>', unsafe_allow_html=True)

    # ✅ 로그인 처리
    if login_clicked:
        # ⬇️ 입력 없이도 바로 메인으로 (게스트)
        if not user_id and not user_pw:
            st.session_state["user"] = {
                "provider": "local",
                "provider_id": 0,
                "local_user_id": "",
                "nickname": "Guest",
            }
            st.success("로그인 없이 바로 시작합니다.")
            _go_main()

        # ⬇️ 실제 백엔드 로그인
        try:
            res = requests.post(
                f"{BACKEND_URL}/auth/local/login",
                json={"user_id": user_id, "password": user_pw},
                timeout=10,
            )
            data = res.json()
            if res.ok and data.get("result") == "ok":
                u = data["user"]
                st.session_state["user"] = {
                    "provider": "local",
                    "provider_id": 0,
                    "local_user_id": u["local_user_id"],
                    "nickname": u["nickname"],
                }
                st.success("로그인 완료!")
                _go_main()
            else:
                err = data.get("error")
                st.error({
                    "not_found": "존재하지 않는 아이디입니다.",
                    "wrong_password": "비밀번호가 올바르지 않습니다.",
                }.get(err, f"로그인 실패: {err}"))
        except Exception as e:
            st.error(f"로그인 오류: {e}")

    # ✅ 로그인 상태 유지 체크박스
    st.markdown('<div class="checkbox-box">', unsafe_allow_html=True)
    stay_logged_in = st.checkbox("로그인 상태 유지", value=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ✅ 간편 로그인 텍스트
    st.markdown('<div class="social-login">간편 로그인</div>', unsafe_allow_html=True)

    # ✅ 간편 로그인 아이콘
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

    # ✅ 하단 링크
    st.markdown("""
    <div class="footer-links">
        <span>아이디 찾기</span> | <span>비밀번호 찾기</span> |
        <a href="?go=join">회원가입</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ===== 쿼리 파라미터 처리 =====
qp = st.query_params
def pick(v): return v[0] if isinstance(v, list) else (v or "")

# ▶ 소셜 로그인 콜백
if pick(qp.get("login")) == "success":
    st.session_state["user"] = {
        "provider": pick(qp.get("provider")) or "kakao",
        "provider_id": int(pick(qp.get("uid")) or 0),
        "nickname": pick(qp.get("nickname")),
    }
    try: st.query_params.clear()
    except: pass
    _go_main()

# ▶ 회원가입 라우팅
if pick(qp.get("go")) == "join":
    try: st.query_params.clear()
    except: pass
    _go_join()
