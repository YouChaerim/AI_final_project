# pages/join.py
import streamlit as st
import re
import requests
import json
import time

BACKEND_URL = "http://127.0.0.1:8080"

st.markdown("""
    <style>
    [data-testid="stSidebar"], [data-testid="stSidebarNav"] { display: none !important; }
    [data-testid="stDeployButton"], [data-testid="stDeploymentButton"], [title="Deploy this app"] { display:none !important; }
    [data-testid="stMenuButton"] { display: none !important; }
    header button[aria-label="Main menu"] { display: none !important; }
    header svg, header path, header button { display: none !important; }
    header div:nth-child(3), header div:nth-child(4), header > div > div:nth-child(2) { display: none !important; }
    .main { margin-left: 0 !important; }
    .go-login-wrap { text-align:center; margin-top: 12px; }
    </style>
""", unsafe_allow_html=True)

# 🔶 헤더
st.markdown("""
    <h1 style='text-align: center; color: orange;'>🐾 딸깍공 회원가입</h1>
    <p style='text-align: center; font-weight: bold;'>닉네임, 아이디, 비밀번호를 입력해주세요.</p>
""", unsafe_allow_html=True)

# ✅ 세션 상태
for key in ["user_id_checked", "last_checked_id", "user_id_msg",
            "nickname_checked", "last_checked_nickname", "nickname_msg"]:
    if key not in st.session_state:
        st.session_state[key] = "" if "msg" in key else False

# ✅ 중복 확인
def check_duplicate_id(user_id):
    try:
        response = requests.get(f"{BACKEND_URL}/auth/local/check-id/{user_id}")
        if response.status_code == 200:
            if response.json()["exists"]:
                st.session_state.user_id_checked = False
                st.session_state.user_id_msg = "<span style='color: red;'>❌ 이미 사용 중인 아이디입니다.</span>"
            else:
                st.session_state.user_id_checked = True
                st.session_state.last_checked_id = user_id
                st.session_state.user_id_msg = "<span style='color: green;'>✅ 사용 가능한 아이디입니다.</span>"
        else:
            st.session_state.user_id_msg = "<span style='color: red;'>⚠️ 서버 오류. 잠시 후 시도하세요.</span>"
    except requests.exceptions.RequestException:
        st.session_state.user_id_msg = "<span style='color: red;'>⚠️ 서버에 연결할 수 없습니다.</span>"

def check_duplicate_nickname(nickname):
    try:
        response = requests.get(f"{BACKEND_URL}/auth/local/check-nickname/{nickname}")
        if response.status_code == 200:
            if response.json()["exists"]:
                st.session_state.nickname_checked = False
                st.session_state.nickname_msg = "<span style='color: red;'>❌ 이미 사용 중인 닉네임입니다.</span>"
            else:
                st.session_state.nickname_checked = True
                st.session_state.last_checked_nickname = nickname
                st.session_state.nickname_msg = "<span style='color: green;'>✅ 사용 가능한 닉네임입니다.</span>"
        else:
            st.session_state.nickname_msg = "<span style='color: red;'>⚠️ 서버 오류. 잠시 후 시도하세요.</span>"
    except requests.exceptions.RequestException:
        st.session_state.nickname_msg = "<span style='color: red;'>⚠️ 서버에 연결할 수 없습니다.</span>"

# ✅ 입력 폼
with st.form("signup_form", clear_on_submit=False):
    col1, col2 = st.columns([3, 1])
    with col1:
        nickname = st.text_input("닉네임 *", placeholder="닉네임 입력", max_chars=20)
        if st.session_state.nickname_msg:
            st.markdown(f"<div style='margin-top: -10px;'>{st.session_state.nickname_msg}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("닉네임 중복확인"):
            if not nickname.strip():
                st.session_state.nickname_msg = "<span style='color: orange;'>닉네임을 입력해주세요.</span>"
                st.session_state.nickname_checked = False
            else:
                check_duplicate_nickname(nickname)

    col3, col4 = st.columns([3, 1])
    with col3:
        user_id = st.text_input("아이디 *", placeholder="영문+숫자 조합", max_chars=20)
        if st.session_state.user_id_msg:
            st.markdown(f"<div style='margin-top: -10px;'>{st.session_state.user_id_msg}</div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("아이디 중복확인"):
            if not re.fullmatch(r"^[a-z0-9]+$", user_id):
                st.session_state.user_id_msg = "<span style='color: orange;'>소문자 영어와 숫자만 입력하세요.</span>"
                st.session_state.user_id_checked = False
            else:
                check_duplicate_id(user_id)

    password = st.text_input("비밀번호 *", type="password", placeholder="8자 이상")
    confirm_password = st.text_input("비밀번호 확인 *", type="password")
    submit = st.form_submit_button("회원가입")

# ✅ 제출 후 검증
if submit:
    if not user_id or not nickname or not password or not confirm_password:
        st.warning("모든 항목을 입력해주세요.")
    elif not re.fullmatch(r"^[a-z0-9]+$", user_id):
        st.error("아이디는 소문자 영어와 숫자만 입력 가능합니다.")
    elif not st.session_state.user_id_checked or st.session_state.last_checked_id != user_id:
        st.error("아이디 중복 확인을 해주세요.")
    elif not st.session_state.nickname_checked or st.session_state.last_checked_nickname != nickname:
        st.error("닉네임 중복 확인을 해주세요.")
    elif len(password) < 8:
        st.error("비밀번호는 8자 이상이어야 합니다.")
    elif password != confirm_password:
        st.markdown("<div style='background-color:#fff7cc;color:#333;padding:10px;border-radius:5px;'>암호가 틀립니다.</div>", unsafe_allow_html=True)
    else:
        payload = {
            "user_id": user_id,
            "password": password,
            "nickname": nickname
        }
        try:
            response = requests.post(f"{BACKEND_URL}/auth/local/signup", json=payload)
            if response.status_code == 200:
                res_data = response.json()
                if res_data.get("result") == "ok":
                    st.success("🎉 회원가입이 완료되었습니다!")
                    time.sleep(2)
                    st.switch_page("pages/login_page.py") # 경로는 실제에 맞게 수정
                else:
                    # 백엔드에서 보낸 에러 메시지 표시
                    error_type = res_data.get("error", "unknown")
                    if error_type == "user_exists":
                        st.error("이미 가입된 아이디입니다. 아이디 중복 확인을 다시 해주세요.")
                    elif error_type == "nickname_exists":
                        st.error("이미 사용 중인 닉네임입니다. 닉네임 중복 확인을 다시 해주세요.")
                    else:
                        st.error(f"회원가입 중 오류가 발생했습니다: {error_type}")
            else:
                st.error(f"서버 오류가 발생했습니다. (Code: {response.status_code})")
        
        except requests.exceptions.RequestException:
            st.error("서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인하세요.")

st.markdown("<div class='go-login-wrap'>이미 계정이 있으신가요?</div>", unsafe_allow_html=True)
if st.button("로그인하기"):
    st.switch_page("onboarding.py")
