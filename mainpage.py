# mainpage.py — (merged) 메인 + 로그인성공/내부라우팅 처리

import streamlit as st
import json
import os
import base64
from urllib.parse import unquote_plus

# -------------------------------
# 0) 카카오 콜백 (?login=success...) 처리
# -------------------------------
qp = st.query_params
def _pick(v): 
    return v[0] if isinstance(v, list) else (v or "")

if _pick(qp.get("login")) == "success":
    st.session_state["user"] = {
        "provider": _pick(qp.get("provider")) or "kakao",
        "provider_id": int(_pick(qp.get("uid")) or 0),
        "nickname": unquote_plus(_pick(qp.get("nickname") or "")),
    }
    try:
        st.query_params.clear()  # 새로고침 루프 방지
    except:
        pass
    st.rerun()

# -------------------------------
# 1) 내부 라우팅 (?goto=...) → st.switch_page
# -------------------------------
if qp.get("goto"):
    dest = _pick(qp.get("goto"))  # 예: "pages/main.py"
    try:
        st.query_params.clear()
    except:
        pass
    st.switch_page(dest)
    st.stop()

# -------------------------------
# 2) 세션 상태/유저 데이터 초기화
# -------------------------------
if "user_data" not in st.session_state:
    if os.path.exists("user_data.json"):
        with open("user_data.json", "r", encoding="utf-8") as f:
            st.session_state.user_data = json.load(f)
    else:
        st.session_state.user_data = {
            "todo": "수학 예제 풀기\n영단어 암기",
            "memo": "중간고사 다음 주!",
            "study_hour": 1,
            "study_minute": 30,
            "dark_mode": False,
        }

ud = st.session_state.user_data
ud.setdefault("active_char", "rabbit")     # bear/cat/rabbit/shiba
ud.setdefault("owned_hats", [])            # ["cap", ...]
ud.setdefault("equipped_hat", None)        # "cap" or None
ud.setdefault("study_hour", ud.get("study_hour", 0))
ud.setdefault("study_minute", ud.get("study_minute", 0))

# -------------------------------
# 3) 다크모드 / 테마
# -------------------------------
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = ud.get("dark_mode", False)

if st.session_state.dark_mode:
    bg_color = "#1C1C1E"; font_color = "#F2F2F2"
    card_bg = "#2C2C2E"; hover_bg = "#3A3A3C"
    nav_bg = "#2C2C2E"; dark_orange = "#FF9330"; label_color = "white"
else:
    bg_color = "#FAFAFA"; font_color = "#333"
    card_bg = "white"; hover_bg = "#F5F5F5"
    nav_bg = "rgba(255, 255, 255, 0.9)"; dark_orange = "#FF9330"; label_color = font_color

st.set_page_config(layout="wide", page_title="딸깍공 메인페이지", initial_sidebar_state="collapsed")

# -------------------------------
# 4) 아바타 이미지 로딩 유틸
# -------------------------------
def _resolve_assets_root():
    here = os.path.dirname(__file__)
    cands = [
        os.path.abspath(os.path.join(here, "assets")),
        os.path.abspath(os.path.join(here, "..", "assets")),
    ]
    for p in cands:
        if os.path.isdir(p):
            return p
    return cands[0]

ASSETS_ROOT = _resolve_assets_root()

def _to_data_uri(path: str) -> str:
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")

def get_char_image_uri(char_key: str, hat_id: str | None = None) -> str:
    keys = [char_key] + (["siba"] if char_key == "shiba" else [])
    cands = []
    if hat_id:
        for k in keys:
            for sep in ["", "_", "-"]:
                cands.append(os.path.join(ASSETS_ROOT, "items", "hats", f"{k}{sep}{hat_id}.png"))
                cands.append(os.path.join(ASSETS_ROOT, "characters", f"{k}{sep}{hat_id}.png"))
    for k in keys:
        cands.append(os.path.join(ASSETS_ROOT, "characters", f"{k}.png"))
    for p in cands:
        if os.path.exists(p):
            return _to_data_uri(p)
    # fallback SVG
    return (
        "data:image/svg+xml;utf8,"
        "<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'>"
        "<text x='50%' y='60%' font-size='28' text-anchor='middle'>🐾</text>"
        "</svg>"
    )

def current_avatar_uri() -> str:
    char_key = ud.get("active_char", "rabbit")
    hat_id = ud.get("equipped_hat")
    if hat_id and (hat_id in ud.get("owned_hats", [])):
        return get_char_image_uri(char_key, hat_id)
    return get_char_image_uri(char_key, None)

# -------------------------------
# 5) 스타일
# -------------------------------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body {{
  background-color: {bg_color};
  color: {font_color};
  font-family: 'Noto Sans KR', sans-serif;
  zoom: 1.10;
  margin: 0;
}}
.stApp {{ background-color: {bg_color}; }}
.block-container {{ padding-top: 0 !important; }}
.container {{ max-width: 1200px; margin: auto; padding: 40px; }}
a {{ text-decoration: none !important; color: {font_color}; }}

/* 헤더 */
.top-nav {{
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 0; margin-top: -40px !important;
  background-color: {nav_bg}; box-shadow: 0 2px 4px rgba(0,0,0,0.05); position: relative;
}}
.nav-left {{ display: flex; align-items: center; gap: 60px; }}
.top-nav .nav-left > div:first-child a {{ color: #000 !important; font-size: 28px; font-weight: bold; }}
.nav-menu {{ display: flex; gap: 36px; font-size: 18px; font-weight: 600; }}
.nav-menu div a {{ color: #000 !important; transition: all .2s ease; }}
.nav-menu div:hover a {{ color: #FF9330 !important; }}

/* 프로필/닉네임 */
.profile-group {{ display: flex; gap: 16px; align-items: center; margin-right: 12px; }}
.profile-icon {{
  width: 36px; height: 36px; border-radius: 50%;
  background: linear-gradient(135deg,#DDEFFF,#F8FBFF);
  overflow: hidden; display: flex; align-items: center; justify-content: center;
  box-shadow: 0 1px 2px rgba(0,0,0,0.06);
}}
.profile-icon img {{ width: 100%; height: 100%; object-fit: contain; image-rendering: auto; }}
.nick {{ font-weight: 700; font-size: 16px; }}

/* 로그인 버튼 */
.stLoginBtn button {{
  font-size: 17px !important; font-weight: 600 !important; color: #FFA500 !important; background: white !important;
  border-radius: 18px !important; padding: 8px 22px !important; border: 1.5px solid #FFA500 !important;
  transition: background .15s, color .15s; box-shadow: 0 1px 4px rgba(255,165,0,0.03);
  height: 36px; margin-left: 18px;
}}
.stLoginBtn button:hover {{ background: #FFF5E5 !important; color: #FF9330 !important; }}

/* 메인 카드 */
.main-box {{
  background-color: {dark_orange};
  border-radius: 14px; padding: 90px 0 140px 0; text-align: center; color: white;
  font-size: 36px; font-weight: bold; margin-bottom: 16px;
}}
.main-btn {{
  margin-top: 30px; padding: 16px 40px; background: white; color: black;
  font-weight: bold; border: none; border-radius: 8px; font-size: 22px;
}}
.right-card {{
  background: {card_bg}; border-radius: 10px; padding: 18px 20px; margin-bottom: 14px;
  font-size: 17px; color: {font_color};
}}

header {{ display: none !important; }}
::selection {{ background: #FF9330; color: white; }}
label, .stTextInput label, .stTextArea label, .stSelectbox label {{ color: {label_color} !important; font-weight: 600; }}
.button-row > div {{ padding-right: 6px !important; }}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# 6) 상단 네비게이션
# -------------------------------
st.markdown('<div class="container">', unsafe_allow_html=True)

header_avatar_uri = current_avatar_uri()
logged_in = "user" in st.session_state
nickname = st.session_state.get("user", {}).get("nickname", "")

st.markdown(f"""
<div class="top-nav">
  <div class="nav-left">
    <div><a href="?goto=mainpage.py" target="_self">🐾 딸깍공</a></div>
    <div class="nav-menu">
      <div><a href="?goto=mainpage.py" target="_self">메인페이지</a></div>
      <div><a href="?goto=pages/main.py" target="_self">공부 시작</a></div>
      <div><a href="?goto=pages/ocr_paddle.py" target="_self">필기</a></div>
      <div><a href="?goto=pages/folder_page.py" target="_self">저장폴더</a></div>
      <div><a href="?goto=pages/quiz.py" target="_self">퀴즈</a></div>
      <div><a href="?goto=pages/report.py" target="_self">리포트</a></div>
      <div><a href="?goto=pages/ranking.py" target="_self">랭킹</a></div>
    </div>
  </div>
  <div class="profile-group">
    <div class="profile-icon" title="내 캐릭터">
      <img src="{header_avatar_uri}" alt="avatar"/>
    </div>
    {f'<div class="nick">{nickname}</div>' if logged_in and nickname else ''}
  </div>
</div>
""", unsafe_allow_html=True)

# 오른쪽 로그인/로그아웃 버튼 (원래 자리 유지)
nav_login = st.container()
with nav_login:
    if not logged_in:
        st.markdown(
            "<div class='stLoginBtn' style='position: absolute; top: 26px; right: 50px; z-index: 10;'></div>",
            unsafe_allow_html=True,
        )
        login_btn_col = st.columns([10, 1])[1]
        with login_btn_col:
            if st.button("로그인", key="go_login", help="로그인 페이지로 이동", use_container_width=True):
                st.switch_page("pages/login_page.py")
    else:
        def _logout():
            st.session_state.pop("user", None)
            st.rerun()
        logout_col = st.columns([10, 1])[1]
        with logout_col:
            st.button("로그아웃", key="logout_btn", help="로그아웃", on_click=_logout, use_container_width=True)

# -------------------------------
# 7) 메인 콘텐츠
# -------------------------------
col1, col2 = st.columns([2.5, 1])

with col1:
    st.markdown(f"""
    <div class="main-box">
      오늘 공부 시작하기<br>
      <a href="?goto=pages/main.py" target="_self">
        <button class="main-btn">공부 시작</button>
      </a>
    </div>
    """, unsafe_allow_html=True)

with col2:
    if not st.session_state.get("edit_mode", False):
        st.markdown(f"<div class='right-card'>📌 <b>오늘 할 일</b><br>{ud['todo']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='right-card'>🗓 <b>빠른 메모</b><br>{ud['memo']}</div>", unsafe_allow_html=True)
        h, m = ud["study_hour"], ud["study_minute"]
        st.markdown(f"<div class='right-card'>⏰ <b>오늘 공부시간</b><br>{h}시간 {m}분</div>", unsafe_allow_html=True)

        b1, b2 = st.columns([1, 1])
        with b1:
            if st.button("✏️ 변경하기", use_container_width=True):
                st.session_state.edit_mode = True
                st.rerun()
        with b2:
            if st.button("🗒️ 투두리스트", use_container_width=True, help="투두리스트로 이동"):
                st.switch_page("pages/folder_page.py")
    else:
        with st.form("save_form"):
            todo = st.text_area("📝 오늘 할 일", value=ud["todo"])
            memo = st.text_area("🗒 빠른 메모", value=ud["memo"])
            hour = st.selectbox("공부 시간(시간)", list(range(0, 13)), index=ud["study_hour"])
            minute = st.selectbox("공부 시간(분)", list(range(0, 61)), index=ud["study_minute"])
            if st.form_submit_button("저장하기"):
                ud.update({"todo": todo, "memo": memo, "study_hour": hour, "study_minute": minute})
                with open("user_data.json", "w", encoding="utf-8") as f:
                    json.dump(ud, f, ensure_ascii=False, indent=2)
                st.session_state.edit_mode = False
                st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# -------------------------------
# 8) 다크모드 토글
# -------------------------------
if st.button("🌗 다크모드 전환", key="dark_toggle"):
    st.session_state.dark_mode = not st.session_state.dark_mode
    ud["dark_mode"] = st.session_state.dark_mode
    with open("user_data.json", "w", encoding="utf-8") as f:
        json.dump(ud, f, ensure_ascii=False, indent=2)
    st.rerun()
