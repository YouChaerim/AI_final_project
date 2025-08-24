# components/header.py
import os, base64
import streamlit as st
from urllib.parse import urlencode
from components.auth import require_login, logout

# --- 환경 ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8080")


# -------- avatar util --------
def _resolve_assets_root():
    here = os.path.dirname(__file__)
    for p in [
        os.path.abspath(os.path.join(here, "..", "pages", "assets")),
        os.path.abspath(os.path.join(here, "assets")),
    ]:
        if os.path.isdir(p):
            return p
    return os.path.abspath(os.path.join(here, "..", "pages", "assets"))

ASSETS_ROOT = _resolve_assets_root()

def _to_data_uri(path: str) -> str:
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")

def get_char_image_uri(char_key: str) -> str:
    p = os.path.join(ASSETS_ROOT, "characters", f"{char_key}.png")
    if os.path.exists(p): 
        return _to_data_uri(p)
    return ("data:image/svg+xml;utf8,"
            "<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'>"
            "<text x='50%' y='60%' font-size='28' text-anchor='middle'>🐾</text></svg>")

# -------- 토큰 유틸 --------
def _get_qp() -> dict:
    try:
        return dict(st.query_params)
    except Exception:
        return dict(st.experimental_get_query_params())

def _ensure_session_has_token_from_url():
    qp = _get_qp()
    token_q = qp.get("token")
    if isinstance(token_q, list):
        token_q = token_q[0] if token_q else None

    tok_ss = (
        st.session_state.get("auth_token")
        or st.session_state.get("token")
        or st.session_state.get("access_token")
    )
    if token_q and token_q != tok_ss:
        st.session_state["auth_token"]   = token_q
        st.session_state["token"]        = token_q
        st.session_state["access_token"] = token_q

def _ensure_url_has_token_from_session():
    sess_token = st.session_state.get("auth_token")
    try:
        cur_q_tok = st.query_params.get("token")
    except Exception:
        cur_q_tok = _get_qp().get("token")
        if isinstance(cur_q_tok, list):
            cur_q_tok = cur_q_tok[0] if cur_q_tok else None
    if sess_token and cur_q_tok != sess_token:
        # 다른 쿼리파람 보존하면서 token만 세팅
        st.query_params["token"] = sess_token  # ← assignment가 가장 안전

# ✅ 순서: 토큰 싱크 → 로그인 보장
_ensure_session_has_token_from_url()
_ensure_url_has_token_from_session()
require_login(BACKEND_URL)
# -------- 메뉴 정의 --------
_MENU = [
    ("메인페이지", "pages/mainpage.py"),
    ("공부 시작",  "pages/main.py"),
    ("PDF요약",    "pages/writing_recognition.py"),
    ("저장폴더",    "pages/folder_page.py"),
    ("퀴즈",       "pages/quiz.py"),
    ("리포트",     "pages/report.py"),
    ("랭킹",       "pages/ranking.py"),
]

def render_header():
    u = st.session_state.get("user_data", {}) if st.session_state.get("logged_in") else {}
    nickname = st.session_state.get("user", {}).get("nickname", "사용자")
    avatar_uri = get_char_image_uri(u.get("active_char", "rabbit"))

    # ---- 헤더 스타일 (UI 유지 + 요구 반영) ----
    st.markdown("""
    <style>
      /* Streamlit 기본 헤더/툴바 숨기기 */
      header,[data-testid="stToolbar"] { display:none !important; }

      /* ✅ 최상단 여백(하얀 박스) 제거 */
      .block-container { padding-top:0 !important; }
      .block-container > div:first-child { margin-top:0 !important; padding-top:0 !important; }

      .top-nav { 
        background:#fff; 
        border-bottom:1px solid #eee; 
        margin-top:-80px !important;   /* 기본 상단 패딩 상쇄 */
        margin-bottom:0 !important;
      }
      .top-nav .wrap { 
        max-width:1000px; 
        margin:0 auto; 
        padding:12px 24px; 
        display:flex; 
        align-items:center; 
        justify-content:space-between; 
      }

      /* ✅ 브랜드(딸깍공) 크게 + 볼드 */
      .brand a { 
        font-size:52px; 
        font-weight:900; 
        color:#000; 
        text-decoration:none !important; 
        letter-spacing:-.2px;
      }

      /* 메뉴를 가로로 한 줄 정렬 */
      .menu-row { display:flex; align-items:center; }
      .menu-row [data-testid="column"]{ padding:0 28px 0 0 !important; }
      .menu-row [data-testid="stHorizontalBlock"]{ gap:0 !important; }

      /* ✅ 메뉴도 볼드 처리 */
      [data-testid="stPageLink"] { display:inline-block !important; margin:0 !important; padding:0 !important; }
      [data-testid="stPageLink"] > a {
        text-decoration:none !important; 
        color:#000 !important;
        font-weight:900;
        font-size:20px; 
        line-height:1;
      }
      [data-testid="stPageLink"] > a:hover { color:#FF9330 !important; }

      .profile-group { display:flex; align-items:center; gap:12px; justify-content:flex-end; }
      .profile-nickname { font-weight:600; font-size:16px; color:#000; }
      .profile-icon{
        width:36px; height:36px; border-radius:50%; overflow:hidden;
        background:linear-gradient(135deg,#DDEFFF,#F8FBFF);
        display:flex; align-items:center; justify-content:center;
        box-shadow:0 1px 2px rgba(0,0,0,.06);
      }
      .profile-icon img{ width:100%; height:100%; object-fit:contain; }
    </style>
    """, unsafe_allow_html=True)

    # ---- 레이아웃: 브랜드 | 메뉴(가로 한줄) | 프로필 ----
    st.markdown('<div class="top-nav"><div class="wrap">', unsafe_allow_html=True)
    col_brand, col_menu, col_prof = st.columns([0.18, 0.62, 0.20])

    with col_brand:
        st.markdown('<div class="brand">', unsafe_allow_html=True)
        st.page_link("pages/mainpage.py", label="🐾 딸깍공")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_menu:
        st.markdown('<div class="menu-row">', unsafe_allow_html=True)
        cols = st.columns(len(_MENU))
        for c, (label, page) in zip(cols, _MENU):
            with c:
                st.page_link(page, label=label)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_prof:
        st.markdown(
            f"""<div class="profile-group">
                    <span class="profile-nickname">{nickname}님</span>
                    <div class="profile-icon"><img src="{avatar_uri}" alt="avatar" /></div>
                </div>""",
            unsafe_allow_html=True,
        )

    st.markdown('</div></div>', unsafe_allow_html=True)
