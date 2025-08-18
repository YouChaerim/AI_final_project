import streamlit as st
import re

# ✅ 1. set_page_config 가장 위에!
st.set_page_config(
    page_title="딸깍공 회원가입",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": None
    }
)

st.markdown("""
    <style>
    /* ✅ 사이드바 제거 */
    [data-testid="stSidebar"],
    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    /* ✅ Deploy 버튼 제거 */
    [data-testid="stDeployButton"],
    [data-testid="stDeploymentButton"],
    [title="Deploy this app"] {
        display: none !important;
    }

    /* ✅ 점 3개 메뉴 버튼 제거 (가장 강력한 방식들 조합) */
    [data-testid="stMenuButton"] {
        display: none !important;
    }

    header button[aria-label="Main menu"] {
        display: none !important;
    }

    header svg,
    header path {
        display: none !important;
    }

    header button {
        display: none !important;
    }

    header div:nth-child(3),
    header div:nth-child(4),
    header > div > div:nth-child(2) {
        display: none !important;
    }

    /* ✅ 본문 전체 확장 */
    .main {
        margin-left: 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ✅ 3. 예시용 아이디/닉네임 데이터
existing_user_ids = ["testuser", "admin123"]
existing_nicknames = ["홍길동", "딸깍이"]

# 🔶 중앙 정렬 헤더
st.markdown("""
    <h1 style='text-align: center; color: orange;'>🐾 딸깍공 회원가입</h1>
    <p style='text-align: center; font-weight: bold;'>닉네임, 아이디, 비밀번호를 입력해주세요.</p>
""", unsafe_allow_html=True)

# ✅ 세션 상태 초기화
for key in ["user_id_checked", "last_checked_id", "user_id_msg",
            "nickname_checked", "last_checked_nickname", "nickname_msg"]:
    if key not in st.session_state:
        st.session_state[key] = "" if "msg" in key else False

# ✅ 중복 확인 함수들
def check_duplicate_id(user_id):
    if user_id in existing_user_ids:
        st.session_state.user_id_checked = False
        st.session_state.user_id_msg = "<span style='color: red;'>❌ 이미 사용 중인 아이디입니다.</span>"
    else:
        st.session_state.user_id_checked = True
        st.session_state.last_checked_id = user_id
        st.session_state.user_id_msg = "<span style='color: green;'>✅ 사용 가능한 아이디입니다.</span>"

def check_duplicate_nickname(nickname):
    if nickname in existing_nicknames:
        st.session_state.nickname_checked = False
        st.session_state.nickname_msg = "<span style='color: red;'>❌ 이미 사용 중인 닉네임입니다.</span>"
    else:
        st.session_state.nickname_checked = True
        st.session_state.last_checked_nickname = nickname
        st.session_state.nickname_msg = "<span style='color: green;'>✅ 사용 가능한 닉네임입니다.</span>"

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
        st.markdown("""
            <div style='background-color: #fff7cc; color: #333; padding: 10px; border-radius: 5px;'>
                암호가 틀립니다.
            </div>
        """, unsafe_allow_html=True)
    else:
        st.success("🎉 회원가입이 완료되었습니다!")
        st.write(f"닉네임: {nickname}")
        st.write(f"아이디: {user_id}")