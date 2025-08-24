# pages/folder_page.py
# -*- coding: utf-8 -*-
import os, base64
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv, find_dotenv
from urllib.parse import urlencode
from components.header import render_header
from components.auth import require_login

print(f"✅✅✅ Executing: {__file__} ✅✅✅")

# ─────────────────────────────────────────────────────────────────────────────
# 환경 로드
# ─────────────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / ".env"
loaded = load_dotenv(dotenv_path=ENV_PATH, override=True)
if not loaded:
    load_dotenv(find_dotenv(filename=".env", usecwd=True), override=True)

BACKEND_URL = "http://127.0.0.1:8080"

# ─────────────────────────────────────────────────────────────────────────────
# 토큰/세션 유지: 쿼리 → 세션 싱크 (다른 페이지로 이동해도 로그인 안풀리게)
# ─────────────────────────────────────────────────────────────────────────────
def _bootstrap_token_to_state_and_url():
    # 1) URL → session_state
    try:
        qp = st.query_params
    except Exception:
        qp = st.experimental_get_query_params()

    token_q = qp.get("token", None)
    if isinstance(token_q, list):
        token_q = token_q[0] if token_q else None

    # 현재 세션에 있는 값
    tok_ss = st.session_state.get("auth_token") or \
             st.session_state.get("token") or \
             st.session_state.get("access_token")

    # URL에 token이 있으면 세션에 싣기 (여러 키에 동시 저장)
    if token_q and token_q != tok_ss:
        st.session_state["auth_token"]   = token_q
        st.session_state["token"]        = token_q
        st.session_state["access_token"] = token_q
        tok_ss = token_q

    # 2) session_state → URL (URL에 없거나 다르면 추가/갱신)
    if tok_ss and token_q != tok_ss:
        # 새 API: st.query_params 할당 → rerun 유발
        st.query_params["token"] = tok_ss

    return tok_ss

# ✅ 반드시 require_login보다 먼저 호출!
_ = _bootstrap_token_to_state_and_url()

# 로그인 강제 (세션의 auth_token을 활용)
require_login(BACKEND_URL)

# 유저/테마
user = st.session_state.get("user", {}) or {}
dark = bool(user.get("dark_mode", False))

# ─────────────────────────────────────────────────────────────────────────────
# 아이콘 로딩(있으면 PNG, 없으면 이모지 폴백)
# ─────────────────────────────────────────────────────────────────────────────
ASSETS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))

def _to_data_uri(abs_path: str):
    try:
        with open(abs_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        return "data:image/png;base64," + b64
    except Exception:
        return None

def _pick_icon(candidates, fallback_emoji: str) -> str:
    for rel in candidates:
        p = os.path.join(ASSETS_ROOT, rel)
        if os.path.exists(p):
            uri = _to_data_uri(p)
            if uri:
                return f"<img src='{uri}' alt='icon' />"
    return f"<span class='emoji'>{fallback_emoji}</span>"

# 필요하면 파일명을 바꾸세요(assets 폴더 기준)
ICON_PDF   = _pick_icon(["cute1.png"], "📄")
ICON_WRONG = _pick_icon(["cute2.png"], "✍️")
ICON_MEMO  = _pick_icon(["cute3.png"], "🗒️")

# ─────────────────────────────────────────────────────────────────────────────
# 스타일 (스크린샷 느낌의 큰 카드 3개)
# ─────────────────────────────────────────────────────────────────────────────
if dark:
    bg = "#1C1C1E"; fg = "#F2F2F2"
    card_bg = "#2A2A2D"; border = "#3A3A3C"; shadow = "rgba(0,0,0,.45)"
    nav_bg = "#2C2C2E"
else:
    bg = "#F5F5F7"; fg = "#2B2B2E"
    card_bg = "#FFFFFF"; border = "#EDEDED"; shadow = "rgba(17,24,39,.08)"
    nav_bg = "rgba(255,255,255,.90)"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;800;900&display=swap');
html, body {{ background:{bg}; color:{fg}; font-family:'Noto Sans KR', sans-serif; margin:0; zoom:1.10; }}
.stApp {{ background:{bg}; }}
.block-container {{ padding-top:0 !important; }}
header, [data-testid="stToolbar"] {{ display:none !important; }}

a, a:hover, a:focus, a:visited {{ text-decoration:none !important; }}

.container {{
  max-width:1200px; margin:auto; padding:4px 40px 24px;
}}

.top-nav {{
  display:flex; justify-content:space-between; align-items:center;
  padding:12px 0; margin-top:40px !important; background:{nav_bg};
  box-shadow:0 2px 4px rgba(0,0,0,.05);
}}

/* 큰 카드 영역 */
.stack {{
  display:flex; flex-direction:column; gap:22px; margin-top:28px;
}}

.card-link {{
  display:block; width:100%;
  background:{card_bg}; border:1px solid {border}; border-radius:24px;
  box-shadow:0 12px 36px {shadow};
  padding:48px 16px; text-align:center;
  transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
}}
.card-link:hover {{
  transform: translateY(-2px);
  box-shadow:0 18px 50px {shadow};
  border-color:#E6E6E6;
}}
.card-inner {{ display:flex; flex-direction:column; align-items:center; gap:14px; }}

.card-inner img {{ width:92px; height:92px; object-fit:contain; image-rendering:auto; }}
.card-inner .emoji {{ font-size:72px; line-height:1; }}
.card-title {{ font-size:28px; font-weight:900; margin-top:4px; }}

</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 네비/헤더
# ─────────────────────────────────────────────────────────────────────────────
render_header()

# ─────────────────────────────────────────────────────────────────────────────
# 본문
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div class="container">', unsafe_allow_html=True)

# 토큰 포함한 안전 링크 생성기
token = st.session_state.get("auth_token", "")
def _page_href(slug: str) -> str:
    return f"./{slug}" + (f"?token={token}" if token else "")

st.markdown(
    f"""
    <div class="stack">
      <a class="card-link" href="{_page_href('pdf_folder')}" target="_self">
        <div class="card-inner">
          {ICON_PDF}
          <div class="card-title">PDF 폴더</div>
        </div>
      </a>

      <a class="card-link" href="{_page_href('wrong_folder')}" target="_self">
        <div class="card-inner">
          {ICON_WRONG}
          <div class="card-title">오답 폴더</div>
        </div>
      </a>

      <a class="card-link" href="{_page_href('memo_folder')}" target="_self">
        <div class="card-inner">
          {ICON_MEMO}
          <div class="card-title">메모 폴더</div>
        </div>
      </a>
    </div>
    """,
    unsafe_allow_html=True
)


st.markdown("</div>", unsafe_allow_html=True)
