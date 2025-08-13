# pages/ranking_and_shop.py
# -*- coding: utf-8 -*-
import streamlit as st
import os, json, base64

st.set_page_config(page_title="랭킹 & 캐릭터/상점", layout="wide", initial_sidebar_state="collapsed")

# -------------------- paths --------------------
USER_JSON_PATH = "user_data.json"
ASSETS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))

# -------------------- items (모자 상점) --------------------
ITEMS = [
    {"id": "cap", "name": "캡모자", "emoji": "🧢", "price": 100},
]
ITEMS_BY_ID = {it["id"]: it for it in ITEMS}

# -------------------- defaults --------------------
DEFAULT_DATA = {
    "dark_mode": False,
    "nickname": "-",
    "coins": 500,
    "mode": "ranking",        # 'ranking' | 'char' | 'shop'
    "active_char": "rabbit",  # bear/cat/rabbit/shiba
    "owned_hats": [],         # ["cap", ...]
    "equipped_hat": None
}

# -------------------- storage --------------------
def load_user_data():
    data = {}
    if os.path.exists(USER_JSON_PATH):
        try:
            with open(USER_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    for k, v in DEFAULT_DATA.items():
        if k not in data:
            data[k] = v
    return data

if "user_data" not in st.session_state:
    st.session_state.user_data = load_user_data()

def save_user_data(silent=True):
    with open(USER_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(st.session_state.user_data, f, ensure_ascii=False, indent=2)
    if not silent: st.success("저장됨 💾")

def set_mode(m):
    st.session_state.user_data["mode"] = m
    save_user_data()

# 처음 진입은 랭킹 우선
if "_ranking_defaulted" not in st.session_state:
    st.session_state._ranking_defaulted = True
    set_mode("ranking")

# -------------------- theme & styles --------------------
dark = st.session_state.user_data.get("dark_mode", False)
if dark:
    bg_color = "#1C1C1E"; font_color = "#F2F2F2"
    card_bg = "#2C2C2E"; nav_bg = "#2C2C2E"; nav_link = "#F2F2F2"
else:
    bg_color = "#FAFAFA"; font_color = "#333"
    card_bg = "white";    nav_bg = "rgba(255, 255, 255, 0.9)"; nav_link = "#000"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body {{ background-color:{bg_color}; color:{font_color}; font-family:'Noto Sans KR', sans-serif; zoom:1.10; margin:0; }}
.stApp {{ background-color:{bg_color}; }}
.block-container {{ padding-top:0 !important; }}
.container {{ max-width:1200px; margin:auto; padding:40px; }}
a {{ text-decoration:none !important; color:{font_color}; }}
header, [data-testid="stSidebar"], [data-testid="stToolbar"] {{ display:none !important; }}
::selection {{ background:#FF9330; color:white; }}

/* 헤더 */
.top-nav {{
  display:flex; justify-content:space-between; align-items:center;
  padding:12px 0; margin-top:40px !important; background-color:{nav_bg};
  box-shadow:0 2px 4px rgba(0,0,0,0.05);
}}
.nav-left {{ display:flex; align-items:center; gap:60px; }}
.top-nav .nav-left > div:first-child a {{ color:#000 !important; font-size:28px; font-weight:bold; }}
.nav-menu {{ display:flex; gap:36px; font-size:18px; font-weight:600; }}
.nav-menu div a {{ color:{nav_link} !important; transition:.2s; }}
.nav-menu div:hover a {{ color:#FF9330 !important; }}

/* 헤더 오른쪽 원형 아이콘 (동그라미 자체도 왼쪽으로 이동) */
.profile-group {{
  display:flex; gap:16px; align-items:center;
  margin-right: 12px;   /* ← 헤더 오른쪽 끝에서 약간 왼쪽으로 */
}}
.profile-icon {{
  width:36px; height:36px; border-radius:50%;
  background:linear-gradient(135deg,#DDEFFF,#F8FBFF);
  overflow:hidden; display:flex; align-items:center; justify-content:center;
  box-shadow:0 1px 2px rgba(0,0,0,0.06);
}}
.profile-icon img {{
  width:100%; height:100%; object-fit:contain; image-rendering:auto;
}}

.card {{ background:{card_bg}; border:1px solid rgba(0,0,0,.06); border-radius:16px; padding:14px; box-shadow:0 8px 22px rgba(0,0,0,.06); margin-top:16px; }}

/* 랭킹 리스트 */
.row {{ display:flex; align-items:center; justify-content:space-between; padding:10px 10px; border-radius:12px; }}
.row + .row {{ border-top:1px dashed rgba(0,0,0,0.06); }}
.left {{ display:flex; align-items:center; gap:12px; }}
.ranknum {{ width:34px; height:34px; display:flex; align-items:center; justify-content:center; border-radius:10px; background:rgba(0,0,0,0.05); font-weight:800; }}
.point {{ font-weight:800; }}

/* 랭킹용 아바타(44x44) */
.rank-avatar {{
  width:44px; height:44px; border-radius:12px;
  display:flex; align-items:center; justify-content:center;
  background:linear-gradient(135deg,#DDEFFF,#F8FBFF); overflow:hidden;
}}
.rank-avatar img {{ width:80%; height:80%; object-fit:contain; image-rendering:auto; }}

/* 캐릭터 박스 */
.char-card {{ max-width:420px; margin:10px auto 0; }}
.char-box {{ position:relative; width:100%; aspect-ratio: 4/5; border-radius:14px; border:1px dashed rgba(0,0,0,.06);
             background: radial-gradient(ellipse at center, rgba(255,147,48,0.10), transparent 60%), {card_bg}; overflow:hidden; }}
.scene {{ position:relative; width:100%; height:100%; }}
.sprite {{ position:absolute; left:50%; top:62%; transform:translate(-50%,-62%); width:min(56%, 220px); image-rendering:auto; }}
</style>
""", unsafe_allow_html=True)

# -------------------- helpers --------------------
def to_data_uri(abs_path: str) -> str:
    with open(abs_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/png;base64,{b64}"

def get_char_image_uri(char_key: str, hat_id: str | None = None) -> str:
    """
    장착 모자가 있으면 전용 이미지 우선 사용, 없으면 기본 이미지.
    탐색 위치:
      - assets/items/hats/{char}{sep}{hat_id}.png
      - assets/characters/{char}{sep}{hat_id}.png
    sep ∈ {"", "_", "-"}
    'shiba'는 'siba' 철자도 자동 지원.
    """
    keys = [char_key] + (["siba"] if char_key == "shiba" else [])
    candidates = []

    if hat_id:
        for k in keys:
            for sep in ["", "_", "-"]:
                candidates.append(os.path.join(ASSETS_ROOT, "items", "hats", f"{k}{sep}{hat_id}.png"))
                candidates.append(os.path.join(ASSETS_ROOT, "characters", f"{k}{sep}{hat_id}.png"))

    for k in keys:
        candidates.append(os.path.join(ASSETS_ROOT, "characters", f"{k}.png"))

    for p in candidates:
        if os.path.exists(p):
            return to_data_uri(p)

    # fallback
    return "data:image/svg+xml;utf8," \
           "<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'><text x='50%' y='60%' font-size='28' text-anchor='middle'>🐾</text></svg>"

def _avatar_uri_for_current_user() -> str:
    u = st.session_state.user_data
    char_key = u.get("active_char", "rabbit")
    hat_id = u.get("equipped_hat")
    if hat_id and (hat_id in u.get("owned_hats", [])):
        return get_char_image_uri(char_key, hat_id)
    return get_char_image_uri(char_key, None)

# -------------------- header --------------------
header_avatar_uri = _avatar_uri_for_current_user()
st.markdown(f"""
<div class="top-nav">
  <div class="nav-left">
    <div style="font-size:28px; font-weight:bold;">
      <a href="/" target="_self">🐾 딸깍공</a>
    </div>
    <div class="nav-menu">
      <div><a href="/"             target="_self">메인페이지</a></div>
      <div><a href="/main"         target="_self">공부 시작</a></div>
      <div><a href="/ocr_paddle"   target="_self">PDF요약</a></div>
      <div><a href="/folder_page"  target="_self">저장폴더</a></div>
      <div><a href="/quiz"         target="_self">퀴즈</a></div>
      <div><a href="/report"       target="_self">리포트</a></div>
      <div><a href="/ranking"      target="_self">랭킹</a></div>
    </div>
  </div>
  <div class="profile-group">
    <div class="profile-icon" title="내 캐릭터">
      <img src="{header_avatar_uri}" alt="avatar"/>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# -------------------- 랭킹 데이터 --------------------
RANK_DATA = [
    {"name":"소지섭","attempts":16,"points":1600},
    {"name":"유유유유유윤","attempts":9,"points":980},
    {"name":"상혁","attempts":8,"points":900},
    {"name":"똑깡아아야","attempts":8,"points":880},
    {"name":"민서","attempts":7,"points":720},
    {"name":"지우","attempts":5,"points":520},
    {"name":"다온","attempts":4,"points":460},
    {"name":"크림림","attempts":3,"points":300},
    {"name":"dbwngus","attempts":2,"points":180},
]

def sort_by_period(period, data):
    if period == "주간":
        return sorted(data, key=lambda x: (x["attempts"], x["points"]), reverse=True)
    if period == "월간":
        return sorted(data, key=lambda x: (x["points"], x["attempts"]), reverse=True)
    return sorted(data, key=lambda x: (x["attempts"]*2 + x["points"]//200), reverse=True)

def _rank_avatar_uri() -> str:
    return _avatar_uri_for_current_user()

# -------------------- views --------------------
def view_ranking():
    u = st.session_state.user_data
    st.subheader("📊 랭킹")
    st.caption(f"보유 코인: 🪙 {u.get('coins',0)}")
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        try:
            period = st.segmented_control("기간", options=["주간","월간","전체"], default="주간")
        except Exception:
            period = st.radio("기간", ["주간","월간","전체"], horizontal=True, index=0)
    with col2:
        q = st.text_input("닉네임 검색", "", placeholder="닉네임을 입력하세요")
    with col3:
        st.write("")
        st.button("🧢 상점으로 이동", on_click=lambda: set_mode("shop"))

    ranked = sort_by_period(period, RANK_DATA)
    if q.strip():
        ranked = [r for r in ranked if q.strip() in r["name"]]

    avatar_uri = _rank_avatar_uri()

    st.markdown('<div class="card">', unsafe_allow_html=True)
    for i, r in enumerate(ranked, 1):
        st.markdown(f"""
        <div class="row">
          <div class="left">
            <div class="ranknum">{i}</div>
            <div class="rank-avatar"><img src="{avatar_uri}" alt="avatar"/></div>
            <div>
              <div style="font-weight:700">{r["name"]}</div>
              <div class="small">습관 실행 {r["attempts"]}회 · ⭐ {r["points"]}</div>
            </div>
          </div>
          <div class="point">⭐ {r["points"]}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

def view_char():
    u = st.session_state.user_data
    st.subheader("🐾 캐릭터")

    top = st.columns([1,1,1])
    with top[0]:
        char_list = ["bear","cat","rabbit","shiba"]
        try:
            active = st.segmented_control("캐릭터 선택", options=char_list, default=u.get("active_char","rabbit"))
        except Exception:
            active = st.selectbox("캐릭터 선택", char_list, index=char_list.index(u.get("active_char","rabbit")))
        u["active_char"] = active; save_user_data()
    with top[1]:
        st.write("")
        st.button("📊 랭킹 보기", on_click=lambda: set_mode("ranking"))
    with top[2]:
        st.write("")
        st.button("🧢 상점 가기", on_click=lambda: set_mode("shop"))

    hat_id = u.get("equipped_hat")
    use_hat = bool(hat_id) and hat_id in u.get("owned_hats", [])
    img_uri = get_char_image_uri(u["active_char"], hat_id if use_hat else None)

    st.markdown(f"""
    <div class="card char-card">
      <div class="char-box">
        <div class="scene">
          <img class="sprite" src="{img_uri}" />
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def view_shop():
    u = st.session_state.user_data
    st.subheader("🧢 상점 — 모자 아이템")
    st.caption(f"보유 코인: 🪙 {u.get('coins',0)}")
    cols = st.columns(4)

    for i, it in enumerate(ITEMS):
        with cols[i % 4]:
            owned = it["id"] in u.get("owned_hats", [])
            equipped = (u.get("equipped_hat") == it["id"])
            st.markdown('<div class="card" style="text-align:center;">', unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:44px;'>{it['emoji']}</div>", unsafe_allow_html=True)
            st.markdown(f"**{it['name']}**<br>가격: 🪙 {it['price']}", unsafe_allow_html=True)
            if not owned:
                if st.button(f"구매 ({it['name']})", key=f"buy_{it['id']}"):
                    if u["coins"] >= it["price"]:
                        u["coins"] -= it["price"]
                        u.setdefault("owned_hats", []).append(it["id"])
                        save_user_data()
                        st.success(f"'{it['name']}' 구매 완료! 이제 착용하면 전용 이미지로 바뀝니다.")
                    else:
                        st.error("코인이 부족합니다.")
            else:
                if equipped:
                    if st.button(f"해제 ({it['name']})", key=f"unequip_{it['id']}"):
                        u["equipped_hat"] = None
                        save_user_data()
                        st.info(f"'{it['name']}' 해제됨. 기본 이미지로 돌아갑니다.")
                else:
                    if st.button(f"착용 ({it['name']})", key=f"equip_{it['id']}"):
                        u["equipped_hat"] = it["id"]
                        save_user_data()
                        st.success(f"'{it['name']}' 착용! 캐릭터 화면에서 전용 이미지가 표시됩니다.")
            st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    bottom = st.columns([1,1])
    with bottom[0]:
        st.button("🐾 내 캐릭터 보기", on_click=lambda: set_mode("char"))
    with bottom[1]:
        st.button("📊 랭킹으로", on_click=lambda: set_mode("ranking"))

# -------------------- route --------------------
st.markdown('<div class="container">', unsafe_allow_html=True)
mode = st.session_state.user_data.get("mode")
if mode == "ranking":
    view_ranking()
elif mode == "shop":
    view_shop()
else:
    view_char()
st.markdown('</div>', unsafe_allow_html=True)
