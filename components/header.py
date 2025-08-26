# components/header.py
import os, base64
import streamlit as st
import streamlit.components.v1 as components
from components.auth import require_login

# ---- 환경 ----
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8080")

# ---------- Assets ----------
def _resolve_assets_root() -> str:
    """components/ 기준 여러 위치를 순서대로 탐색해 assets 폴더를 찾는다."""
    here = os.path.dirname(__file__)
    candidates = [
        os.path.abspath(os.path.join(here, "..", "assets")),       # <project>/assets
        os.path.abspath(os.path.join(here, "..", "pages", "assets")),  # <project>/pages/assets (구조 호환)
        os.path.abspath(os.path.join(here, "assets")),              # components/assets
    ]
    for p in candidates:
        if os.path.isdir(p):
            return p
    # 마지막 폴백
    return os.path.abspath(os.path.join(here, "..", "assets"))

ASSETS_ROOT = _resolve_assets_root()

def _to_data_uri(path: str) -> str:
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")

def _paw_svg(size: int = 44) -> str:
    return (
        "data:image/svg+xml;utf8,"
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}'>"
        "<text x='50%' y='60%' font-size='28' text-anchor='middle'>🐾</text></svg>"
    )

def get_char_image_uri(char_key: str | None) -> str:
    """
    선택된 캐릭터 키를 받아 header 아이콘용 data URI 반환.
    - None/빈값 또는 'ddalkkak' 이면 발자국 🐾 아이콘
    - 'shiba'는 파일명이 'siba.png'인 경우까지 자동 탐색
    - 기본 탐색 경로: assets/characters/{key}.png
    """
    if not char_key or char_key == "ddalkkak":
        return _paw_svg(44)

    keys = [char_key]
    # 파일명 호환: shiba → siba.png
    if char_key == "shiba":
        keys.append("siba")

    for k in keys:
        p = os.path.join(ASSETS_ROOT, "characters", f"{k}.png")
        if os.path.exists(p):
            return _to_data_uri(p)

    # 못 찾으면 발자국
    return _paw_svg(44)

# ---------- 토큰 동기화 ----------
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
        # 다른 파라미터는 유지하고 token만 동기화
        st.query_params["token"] = sess_token

# 토큰 싱크 → 로그인 보장
_ensure_session_has_token_from_url()
_ensure_url_has_token_from_session()
require_login(BACKEND_URL)

# ---------- 메뉴 ----------
_MENU = [
    ("메인페이지", "pages/mainpage.py"),
    ("공부 시작",  "pages/main.py"),
    ("PDF요약",    "pages/writing_recognition.py"),
    ("퀴즈",       "pages/quiz.py"),
    ("리포트",     "pages/report.py"),
    ("랭킹",       "pages/ranking.py"),
]

def _resolve_avatar_uri(explicit_avatar_uri: str | None, explicit_char_key: str | None) -> str:
    """
    헤더에 표시할 아바타 URI 결정:
    1) 인자로 avatar_uri가 들어오면 최우선 사용
    2) 인자로 char_key가 들어오면 그려서 사용
    3) 세션의 'header_avatar_uri'가 있으면 사용(페이지에서 미리 세팅 가능)
    4) 세션 user_data.active_char → 세션 user.active_char 순으로 조회
    5) 폴백: ddalkkak(=🐾)
    """
    if explicit_avatar_uri:
        return explicit_avatar_uri
    if explicit_char_key:
        return get_char_image_uri(explicit_char_key)

    ss_uri = st.session_state.get("header_avatar_uri")
    if ss_uri:
        return ss_uri

    char_key = None
    # pages 쪽에서 user_data를 쓰는 구조를 우선
    if st.session_state.get("user_data"):
        char_key = st.session_state["user_data"].get("active_char")
    if not char_key and st.session_state.get("user"):
        char_key = st.session_state["user"].get("active_char")

    return get_char_image_uri(char_key or "ddalkkak")

def render_header(avatar_uri: str | None = None, char_key: str | None = None):
    """
    헤더 렌더 함수.
    - avatar_uri 또는 char_key 중 하나를 넘기면 그 값이 우선 적용된다.
    - 아무것도 넘기지 않으면 세션에서 active_char를 읽어 적용한다.
    - active_char == 'ddalkkak'이면 발자국 아이콘(🐾) 노출.
    """
    # 유저명
    nickname = st.session_state.get("user", {}).get("nickname", "사용자")

    # 아바타 결정
    resolved_avatar = _resolve_avatar_uri(avatar_uri, char_key)

    # 스타일(f-string)
    st.markdown(f"""
    <style>
      header,[data-testid="stToolbar"] {{ display:none !important; }}
      .block-container {{ padding-top:0 !important; }}
      .block-container > div:first-child {{ margin-top:0 !important; padding-top:0 !important; }}
      .top-nav {{ background:#fff; border-bottom:1px solid #eee; margin-top:-80px !important; margin-bottom:0 !important; }}
      .top-nav .wrap {{ max-width:1000px; margin:0 auto; padding:12px 24px; display:flex; align-items:center; justify-content:space-between; }}

      /* 헤더 내 page_link 공통 리셋 */
      .top-nav [data-testid^="stPageLink"]{{
          background:transparent !important;
          box-shadow:none !important;
          border-radius:0 !important;
          padding:6px 10px !important;
          font-weight:600 !important;
          font-size:16px !important;
          color:#000 !important;
      }}
      .top-nav [data-testid^="stPageLink"] :is(a,button,span){{
          font: inherit !important;
          line-height: inherit !important;
          color: inherit !important;
      }}

      /* 브랜드 라벨 크게 */
      #brand-wrap [data-testid^="stPageLink"]{{
          font-size: 40px !important;
          font-weight: 900 !important;
          line-height: 1.1 !important;
          letter-spacing: -0.2px;
          padding: 8px 0 !important;
      }}
      #brand-wrap [data-testid^="stPageLink"] :is(a,button,span){{
          font: inherit !important;
          line-height: inherit !important;
      }}

      .menu-row {{ display:flex; align-items:center; }}
      .menu-row [data-testid="column"]{{ padding:0 28px 0 0 !important; }}
      .menu-row [data-testid="stHorizontalBlock"]{{ gap:0 !important; }}

      .profile-group {{ display:flex; align-items:center; gap:12px; justify-content:flex-end; }}
      .profile-nickname {{ font-weight:600; font-size:16px; color:#000; }}
      .profile-icon {{ width:36px; height:36px; border-radius:50%; overflow:hidden;
                       background:linear-gradient(135deg,#DDEFFF,#F8FBFF);
                       display:flex; align-items:center; justify-content:center;
                       box-shadow:0 1px 2px rgba(0,0,0,.06); }}
      .profile-icon img{{ width:100%; height:100%; object-fit:contain; }}
    </style>
    """, unsafe_allow_html=True)

    # 레이아웃
    st.markdown('<div class="top-nav"><div class="wrap">', unsafe_allow_html=True)
    col_brand, col_menu, col_prof = st.columns([0.18, 0.62, 0.20])

    with col_brand:
        brand_css = """
        <style>
        #brand a span div p {
            font-size: 24px !important;
            font-weight: 700 !important;
        }
        </style>
        """
        st.markdown('<div id="brand"></div>', unsafe_allow_html=True)
        st.page_link("pages/mainpage.py", label="🐾 딸깍공")

        components.html("""
        <script>
        (function(){
          const HOST = '#brand';
          const TARGET_TEXT = '🐾 딸깍공';
          const norm = s => (s||'').replace(/\\u00A0/g,' ').replace(/\\s+/g,' ').trim();
          function move(){
            const host = parent.document.querySelector(HOST);
            if(!host) return false;
            const a = Array.from(parent.document.querySelectorAll("div[data-testid='stPageLink'] a"))
              .find(el => {
                const t = norm(el.textContent);
                const aria = el.getAttribute('aria-label') || '';
                return t === TARGET_TEXT || aria === TARGET_TEXT || t.includes(TARGET_TEXT);
              });
            if(!a) return false;
            const wrapper = a.closest("div[data-testid='stPageLink']") || a;
            host.appendChild(wrapper);
            return true;
          }
          if (!move()){
            const mo = new MutationObserver(() => { if (move()) mo.disconnect(); });
            mo.observe(parent.document.body, {childList:true, subtree:true});
          }
        })();
        </script>
        """, height=0)
        st.markdown(brand_css, unsafe_allow_html=True)

    with col_menu:
        st.markdown('<div id="brand-wrap" class="menu-row">', unsafe_allow_html=True)
        cols = st.columns(len(_MENU))
        for c, (label, page) in zip(cols, _MENU):
            with c:
                st.page_link(page, label=label)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_prof:
        st.markdown(
            f"""<div class="profile-group">
                    <span class="profile-nickname">{st.session_state.get("user", {}).get("nickname","사용자")}님</span>
                    <div class="profile-icon"><img src="{resolved_avatar}" alt="avatar" /></div>
                </div>""",
            unsafe_allow_html=True,
        )

    st.markdown('</div></div>', unsafe_allow_html=True)
