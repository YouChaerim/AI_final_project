# pages/ranking_and_shop.py
# -*- coding: utf-8 -*-
import streamlit as st
import os, json, base64

st.set_page_config(page_title="랭킹 & 캐릭터/상점", layout="wide", initial_sidebar_state="collapsed")

# -------------------- paths --------------------
USER_JSON_PATH = "user_data.json"
ASSETS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))

# -------------------- items (모자 상점: 기존 변수 유지) --------------------
# 아이템은 500P 고정
ITEMS = [
    {"id": "cap", "name": "캡모자", "emoji": "🧢", "price": 500},
]
ITEMS_BY_ID = {it["id"]: it for it in ITEMS}

# ===== 추가 카탈로그 =====
CHARACTERS = [
    {"id": "bear",   "name": "곰",   "price": 1000},
    {"id": "cat",    "name": "고양이", "price": 1000},
    {"id": "rabbit", "name": "토끼",   "price": 1000},
    {"id": "shiba",  "name": "시바",   "price": 1000},
]

GLASSES_ITEMS = [
    {"id": "round", "name": "동그란 안경", "emoji": "👓", "price": 500},
]
SCARF_ITEMS = [
    {"id": "red_scarf", "name": "빨간 목도리", "emoji": "🧣", "price": 500},
]
CLOTHES_ITEMS = [
    {"id": "hoodie", "name": "후드티", "emoji": "🧥", "price": 500},
]
SHOES_ITEMS = [
    {"id": "sneakers", "name": "운동화", "emoji": "👟", "price": 500},
]
WINGS_ITEMS = [
    {"id": "angel_wing", "name": "천사 날개", "emoji": "🪽", "price": 500},
]

# 카테고리-세션키 매핑(기존 키 유지 + 확장)
SHOP_CATEGORIES = {
    "모자":    {"items": ITEMS,          "owned_key": "owned_hats",    "equipped_key": "equipped_hat"},
    "안경":    {"items": GLASSES_ITEMS,  "owned_key": "owned_glasses", "equipped_key": "equipped_glasses"},
    "목도리":  {"items": SCARF_ITEMS,    "owned_key": "owned_scarves", "equipped_key": "equipped_scarf"},
    "옷":      {"items": CLOTHES_ITEMS,  "owned_key": "owned_clothes", "equipped_key": "equipped_clothes"},
    "신발":    {"items": SHOES_ITEMS,    "owned_key": "owned_shoes",   "equipped_key": "equipped_shoes"},
    "날개":    {"items": WINGS_ITEMS,    "owned_key": "owned_wings",   "equipped_key": "equipped_wings"},
}

# -------------------- defaults --------------------
DEFAULT_DATA = {
    "dark_mode": False,
    "nickname": "-",
    "coins": 500,
    "mode": "ranking",        # 'ranking' | 'char' | 'shop'
    # 캐릭터가 없으면 None → 발바닥 프리뷰
    "active_char": None,      # bear/cat/rabbit/shiba
    "owned_chars": [],

    # 기존 모자 키(유지)
    "owned_hats": [],
    "equipped_hat": None,

    # 추가 장비 슬롯
    "owned_glasses": [],  "equipped_glasses": None,
    "owned_scarves": [],  "equipped_scarf": None,
    "owned_clothes": [],  "equipped_clothes": None,
    "owned_shoes": [],    "equipped_shoes": None,
    "owned_wings": [],    "equipped_wings": None,
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
    sub_text = "#CFCFCF"
else:
    bg_color = "#F5F5F7"; font_color = "#2B2B2E"
    card_bg = "#FFFFFF"; nav_bg = "rgba(255,255,255,.9)"; nav_link = "#000"
    sub_text = "#6B7280"

panel_bg     = "#1F1F22" if dark else "#FFFFFF"
panel_shadow = "rgba(0,0,0,.35)" if dark else "rgba(0,0,0,.08)"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;800;900&display=swap');
html, body {{ background:{bg_color}; color:{font_color}; font-family:'Noto Sans KR', sans-serif; zoom:1.10; margin:0; }}
.stApp {{ background:{bg_color}; }}
.block-container {{ padding-top:0 !important; }}

/* 본문 컨테이너 */
.container {{ max-width:1200px; margin:auto; padding:4px 40px 24px; }}
.container.tight-top {{ padding:4px 40px 24px; }}

a, a:hover, a:focus, a:visited {{ text-decoration:none !important; }}
header, [data-testid="stSidebar"], [data-testid="stToolbar"] {{ display:none !important; }}
::selection {{ background:#FF9330; color:white; }}

/* ===== 헤더(고정 규격) ===== */
.top-nav {{
  display:flex; justify-content:space-between; align-items:center;
  padding:12px 0; margin-top:40px !important; background:{nav_bg};
  box-shadow:0 2px 4px rgba(0,0,0,.05);
}}
.nav-left {{ display:flex; align-items:center; gap:60px; }}
.top-nav .nav-left > div:first-child a {{ color:#000 !important; font-size:28px; font-weight:900; }}
.nav-menu {{ display:flex; gap:36px; font-size:18px; font-weight:700; }}
.nav-menu div a {{ color:{nav_link} !important; transition:.2s; }}
.nav-menu div:hover a {{ color:#FF9330 !important; }}

/* 헤더 오른쪽 원형 아이콘 */
.profile-group {{ display:flex; gap:16px; align-items:center; margin-right:12px; }}
.profile-icon {{
  width:36px; height:36px; border-radius:50%;
  background:linear-gradient(135deg,#DDEFFF,#F8FBFF);
  overflow:hidden; display:flex; align-items:center; justify-content:center;
  box-shadow:0 1px 2px rgba(0,0,0,.06);
}}
.profile-icon img {{ width:100%; height:100%; object-fit:contain; image-rendering:auto; }}

/* 공통 카드 */
.card {{ background:{card_bg}; border:1px solid rgba(0,0,0,.06); border-radius:18px; padding:16px; box-shadow:0 10px 28px rgba(0,0,0,.06); margin-top:16px; }}

/* ===== 패널 (공통) ===== */
.panel {{
  position: relative;
  background:{panel_bg};
  border-radius:18px;
  box-shadow:0 6px 24px {panel_shadow};
  overflow:hidden;
  margin-top:0px;
}}
.panel-head {{
  background: linear-gradient(90deg,#FF9330,#FF7A00);
  color:white; text-align:center; font-size:34px; font-weight:900; padding:18px 20px;
}}
.panel-body {{ padding:24px 36px 20px; }}

/* 랭킹 리스트 */
.list-card {{ padding:0; }}
.row {{ display:flex; align-items:center; justify-content:space-between; padding:16px 18px; }}
.row + .row {{ border-top:1px dashed rgba(0,0,0,0.06); }}
.left {{ display:flex; align-items:center; gap:14px; }}
.badge {{
  width:34px; height:34px; display:flex; align-items:center; justify-content:center;
  border-radius:10px; background:rgba(0,0,0,0.05); font-weight:800; color:#333;
}}
.badge.gold   {{ background:#FCD34D; }}
.badge.silver {{ background:#E5E7EB; }}
.badge.bronze {{ background:#F59E0B; color:white; }}
.rank-avatar {{
  width:44px; height:44px; border-radius:12px;
  display:flex; align-items:center; justify-content:center;
  background:linear-gradient(135deg,#DDEFFF,#F8FBFF); overflow:hidden;
}}
.rank-avatar img {{ width:80%; height:80%; object-fit:contain; image-rendering:auto; }}
.small {{ color:{sub_text}; font-size:14px; }}

/* 사이드 */
.side-card .big {{ font-size:28px; font-weight:800; }}
.side-card .muted {{ color:{sub_text}; }}

/* 사이드 상단 칩 */
.side-chip {{
  display:block; width:100%;
  background:linear-gradient(90deg,#FF9330,#FF7A00);
  color:#fff; font-weight:900; font-size:18px;
  padding:12px 16px; border-radius:18px;
  box-shadow:0 10px 22px rgba(255,147,48,.28);
  margin:0 0 12px 0;
}}

/* 캐릭터 히어로 */
.right-note {{ text-align:center; padding:22px 16px; }}
.right-note-hero {{ padding-top:26px; padding-bottom:26px; }}
.right-note-hero .hero-circle {{
  width:190px; height:190px; margin:6px auto 0; border-radius:50%;
  display:flex; align-items:center; justify-content:center;
  background: radial-gradient(ellipse at 50% 40%, #EAF4FF 0%, #F8FBFF 60%);
  border:1px solid rgba(0,0,0,.04);
  box-shadow: 0 8px 22px rgba(0,0,0,.06), inset 0 -14px 24px rgba(0,0,0,.03);
}}
.right-note-hero .hero-circle img {{ width:72%; height:72%; object-fit:contain; image-rendering:auto; }}
.right-note-hero .hero-title {{ margin-top:16px; font-weight:800; font-size:18px; letter-spacing:.2px; }}
.right-note-hero .hero-sub {{ margin-top:4px; color:{sub_text}; font-size:13.5px; }}

/* 상점 전용 */
.shop-toolbar {{ display:flex; gap:12px; align-items:center; margin:4px 0 14px 0; }}
.coin-pill {{ padding:8px 12px; border-radius:999px; background:#FFF; border:1px solid rgba(0,0,0,.06); font-weight:700; box-shadow:0 4px 10px rgba(0,0,0,.04); }}

.shop-card {{ text-align:center; padding-top:18px; padding-bottom:14px; }}
.shop-name {{ font-weight:800; margin-top:10px; }}
.shop-price {{ color:{sub_text}; margin-top:4px; }}
.shop-img {{
  width:72%; max-width:220px; border-radius:16px;
  background:#FFF; border:1px solid rgba(0,0,0,.06);
  box-shadow:0 8px 22px rgba(0,0,0,.06); object-fit:contain;
}}
.shop-btn :where(button) {{
  width:100%; margin-top:10px; border-radius:12px; border:0; padding:10px 12px; font-weight:800;
  background:#F5F7FB; color:#2B2B2E; box-shadow:0 4px 10px rgba(0,0,0,.05); cursor:pointer;
}}
.shop-btn :where(button):hover {{ background:#EBF0FF; }}
.shop-btn :where(button):active {{ transform:translateY(1px); }}

/* 모자 미리보기 하단 썸네일 */
.thumb-row {{ display:flex; justify-content:center; gap:10px; margin-top:10px; }}
.thumb {{
  width:52px; height:52px; border-radius:12px; overflow:hidden;
  border:2px solid rgba(0,0,0,.06); background:#FFF;
  box-shadow:0 4px 10px rgba(0,0,0,.05);
}}
.thumb.active {{ border-color:#FF9330; box-shadow:0 6px 16px rgba(255,147,48,.25); }}
.thumb img {{ width:100%; height:100%; object-fit:cover; }}

/* 사이드 CTA 버튼 */
.side-cta :where(.stButton) button {{
  width:100%; padding:12px 14px; border-radius:12px; border:0; font-weight:800; cursor:pointer;
  background:#F5F7FB; color:#2B2B2E; box-shadow:0 4px 10px rgba(0,0,0,.05);
}}
.side-cta :where(.stButton) button:hover {{ background:#EBF0FF; }}
.side-cta :where(.stButton) button:active {{ transform:translateY(1px); }}

/* 스트림릿 빈 블럭 정리 */
.block-container > div:empty {{ display:none !important; margin:0 !important; padding:0 !important; }}
</style>
""", unsafe_allow_html=True)

# -------------------- helpers --------------------
def to_data_uri(abs_path: str) -> str:
    with open(abs_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/png;base64,{b64}"

def get_char_image_uri(char_key: str | None, hat_id: str | None = None) -> str:
    # 캐릭터가 없으면 발바닥
    if not char_key:
        return "data:image/svg+xml;utf8," \
               "<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'><text x='50%' y='60%' font-size='96' text-anchor='middle'>🐾</text></svg>"
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
        if os.path.exists(p): return to_data_uri(p)
    return "data:image/svg+xml;utf8," \
           "<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'><text x='50%' y='60%' font-size='28' text-anchor='middle'>🐾</text></svg>"

# ▼ 아이템 프리뷰: (업데이트) 캐릭터별 모자 이미지를 우선 사용
def get_shop_item_image_uri(category_name: str, item_id: str, char_key: str | None = None) -> str:
    """
    assets/items/<folder>/ 에서 아이템 프리뷰 이미지를 찾아 반환.
    - 모자(category '모자'): char_key가 있으면 <char_alias><item_id>.png 를 우선 사용
      예) assets/items/hats/rabbitcap.png, bearcap.png, catcap.png, sibacap.png
    - 그 외: item_id.png → placeholder
    """
    folder_map = {
        "모자": "hats",
        "안경": "glasses",
        "목도리": "scarves",
        "옷": "clothes",
        "신발": "shoes",
        "날개": "wings",
    }
    folder = folder_map.get(category_name, "")
    base_dir = os.path.join(ASSETS_ROOT, "items", folder) if folder else None

    # alias: shiba → siba
    if char_key == "shiba":
        char_aliases = ["siba", "shiba"]
    elif char_key:
        char_aliases = [char_key]
    else:
        char_aliases = []

    if base_dir and os.path.isdir(base_dir):
        candidates = []
        # 1) 캐릭터별 미리보기 (모자)
        if category_name == "모자" and char_aliases:
            for c in char_aliases:
                candidates.append(os.path.join(base_dir, f"{c}{item_id}.png"))      # rabbitcap.png
                candidates.append(os.path.join(base_dir, f"{c}_{item_id}.png"))     # rabbit_cap.png
                candidates.append(os.path.join(base_dir, f"{c}-{item_id}.png"))     # rabbit-cap.png
        # 2) 일반 파일명
        candidates.append(os.path.join(base_dir, f"{item_id}.png"))
        for p in candidates:
            if os.path.exists(p):
                return to_data_uri(p)

    # placeholder (흰박스)
    return ("data:image/svg+xml;utf8,"
            "<svg xmlns='http://www.w3.org/2000/svg' width='280' height='280'>"
            "<rect x='0' y='0' width='100%' height='100%' rx='26' ry='26' fill='white'/>"
            "</svg>")

def _avatar_uri_for_current_user() -> str:
    u = st.session_state.user_data
    char_key = u.get("active_char")  # None이면 발바닥
    hat_id = u.get("equipped_hat")
    if hat_id and (hat_id in u.get("owned_hats", [])):
        return get_char_image_uri(char_key, hat_id)
    return get_char_image_uri(char_key, None)

# -------------------- header --------------------
header_avatar_uri = _avatar_uri_for_current_user()
st.markdown(f"""
<div class="top-nav">
  <div class="nav-left">
    <div><a href="/mainpage" target="_self">🐾 딸깍공</a></div>
    <div class="nav-menu">
      <div><a href="/mainpage" target="_self">메인페이지</a></div>
      <div><a href="/main" target="_self">공부 시작</a></div>
      <div><a href="/ocr_paddle" target="_self">PDF요약</a></div>
      <div><a href="/folder_page" target="_self">저장폴더</a></div>
      <div><a href="/quiz" target="_self">퀴즈</a></div>
      <div><a href="/report" target="_self">리포트</a></div>
      <div><a href="/ranking" target="_self">랭킹</a></div>
    </div>
  </div>
  <div class="profile-group">
    <div class="profile-icon" title="내 캐릭터"><img src="{header_avatar_uri}" alt="avatar"/></div>
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

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-head">랭킹</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-body">', unsafe_allow_html=True)

    c1, c2 = st.columns([1,3])
    with c1:
        try:
            period = st.segmented_control("기간", options=["주간","월간","전체"], default="주간")
        except Exception:
            period = st.radio("기간", ["주간","월간","전체"], horizontal=True, index=0)
    with c2:
        q = ""

    left, right = st.columns([3,1])

    ranked = sort_by_period(period, RANK_DATA)
    if q.strip():
        ranked = [r for r in ranked if q.strip() in r["name"]]

    avatar_uri = _rank_avatar_uri()

    with left:
        st.markdown('<div class="card list-card">', unsafe_allow_html=True)
        for i, r in enumerate(ranked, 1):
            cls = "badge"
            if i == 1: cls += " gold"
            elif i == 2: cls += " silver"
            elif i == 3: cls += " bronze"

            st.markdown(f"""
            <div class="row">
              <div class="left">
                <div class="{cls}">{i}</div>
                <div class="rank-avatar"><img src="{avatar_uri}" alt="avatar"/></div>
                <div>
                  <div style="font-weight:700">{r["name"]}</div>
                  <div class="small">출석횟수 {r["attempts"]}회</div>
                </div>
              </div>
              <div style="display:flex; gap:10px; align-items:center;">
                <div class="small">출석횟수 {max(1, r["attempts"]//2)}회</div>
                <div class="small">⭐ {r["points"]}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="side-chip">내 캐릭터</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="card right-note right-note-hero">
          <div class="hero-circle"><img src="{header_avatar_uri}" alt="avatar"/></div>
          <div class="hero-title">{'캐릭터 선택됨' if u.get('active_char') else '캐릭터 없음'}</div>
          <div class="hero-sub">상점에서 캐릭터와 아이템을 구매해 꾸며보세요</div>
        </div>
        """, unsafe_allow_html=True)

        # ▶ 상점 진입 버튼 (🏬)
        st.markdown('<div class="side-cta">', unsafe_allow_html=True)
        if st.button("🏬 상점", key="go_shop_side", help="캐릭터/아이템 구매하러 가기"):
            set_mode("shop")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)  # .panel-body
    st.markdown('</div>', unsafe_allow_html=True)  # .panel

def view_char():
    u = st.session_state.user_data
    st.subheader("🐾 캐릭터")

    top = st.columns([1,1,1])
    with top[0]:
        char_list = ["bear","cat","rabbit","shiba"]
        try:
            active = st.segmented_control("캐릭터 선택", options=char_list, default=u.get("active_char") or "rabbit")
        except Exception:
            active = st.selectbox("캐릭터 선택", char_list, index=char_list.index((u.get("active_char") or "rabbit")))
        u["active_char"] = active; save_user_data()
    with top[1]:
        st.write("")
        st.button("📊 랭킹 보기", on_click=lambda: set_mode("ranking"))
    with top[2]:
        st.write("")
        st.button("🏬 상점 가기", on_click=lambda: set_mode("shop"))

    hat_id = u.get("equipped_hat")
    use_hat = bool(hat_id) and hat_id in u.get("owned_hats", [])
    img_uri = get_char_image_uri(u.get("active_char"), hat_id if use_hat else None)

    st.markdown(f"""
    <div class="card" style="max-width:420px; margin:10px auto 0;">
      <div style="position:relative; width:100%; aspect-ratio: 4/5; border-radius:14px; border:1px dashed rgba(0,0,0,.06);
                  background: radial-gradient(ellipse at center, rgba(255,147,48,0.10), transparent 60%), {card_bg}; overflow:hidden;">
        <img style="position:absolute; left:50%; top:62%; transform:translate(-50%,-62%); width:min(56%, 220px); image-rendering:auto;" src="{img_uri}" />
      </div>
    </div>
    """, unsafe_allow_html=True)

def _equip_item(u, owned_key, equipped_key, item_id):
    if item_id is None:
        u[equipped_key] = None
    else:
        if item_id in u.get(owned_key, []):
            u[equipped_key] = item_id
    save_user_data()

def _buy_item(u, price, owned_key, item_id, success_msg, not_enough_msg):
    if u["coins"] >= price:
        u["coins"] -= price
        u.setdefault(owned_key, []).append(item_id)
        save_user_data()
        st.success(success_msg)
    else:
        st.error(not_enough_msg)

def view_shop():
    u = st.session_state.user_data

    # ===== 랭킹과 동일한 패널 레이아웃 =====
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-head">상점</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-body">', unsafe_allow_html=True)

    left, right = st.columns([3,1])

    # ---------- Right: 내 캐릭터 프리뷰 ----------
    with right:
        st.markdown('<div class="side-chip">내 캐릭터</div>', unsafe_allow_html=True)
        hat_id = u.get("equipped_hat")
        use_hat = bool(hat_id) and hat_id in u.get("owned_hats", [])
        preview_uri = get_char_image_uri(u.get("active_char"), hat_id if use_hat else None)

        chips = []
        if u.get("equipped_hat"): chips.append("🧢")
        if u.get("equipped_glasses"): chips.append("👓")
        if u.get("equipped_scarf"): chips.append("🧣")
        if u.get("equipped_clothes"): chips.append("🧥")
        if u.get("equipped_shoes"): chips.append("👟")
        if u.get("equipped_wings"): chips.append("🪽")
        equipped_summary = " ".join(chips) if chips else "—"

        st.markdown(f"""
        <div class="card right-note right-note-hero">
          <div class="hero-circle">
            <img src="{preview_uri}" alt="avatar"/>
          </div>
          <div class="hero-title">{'선택된 캐릭터' if u.get('active_char') else '미보유'}</div>
          <div class="hero-sub">착용 중: {equipped_summary}</div>
        </div>
        """, unsafe_allow_html=True)

    # ---------- Left: 상점 콘텐츠 ----------
    with left:
        st.markdown(f"""
        <div class="shop-toolbar">
          <div class="coin-pill">보유 코인: 🪙 {u.get('coins',0)}</div>
        </div>
        """, unsafe_allow_html=True)

        # 상단 탭: 캐릭터 / 아이템
        tabs_col1, tabs_col2 = st.columns([1,3])
        with tabs_col1:
            try:
                top_tab = st.segmented_control("구분", options=["캐릭터", "아이템"], default="캐릭터")
            except Exception:
                top_tab = st.radio("구분", ["캐릭터","아이템"], horizontal=True, index=0)

        if top_tab == "캐릭터":
            cols = st.columns(4)
            for i, ch in enumerate(CHARACTERS):
                with cols[i % 4]:
                    owned = ch["id"] in u.get("owned_chars", [])
                    active = (u.get("active_char") == ch["id"])
                    img_uri = get_char_image_uri(ch["id"], None)

                    st.markdown('<div class="card shop-card">', unsafe_allow_html=True)
                    st.markdown(f'<div><img src="{img_uri}" class="shop-img" alt="char"/></div>', unsafe_allow_html=True)
                    st.markdown(f"<div class='shop-name'>{ch['name']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='shop-price'>가격: 🪙 {ch['price']}</div>", unsafe_allow_html=True)

                    st.markdown("<div class='shop-btn'>", unsafe_allow_html=True)
                    if not owned:
                        if st.button(f"구매 ({ch['name']})", key=f"buy_char_{ch['id']}"):
                            _buy_item(u, ch["price"], "owned_chars", ch["id"],
                                      f"'{ch['name']}' 캐릭터 구매 완료! 적용하려면 '선택'을 눌러주세요.",
                                      "코인이 부족합니다.")
                    else:
                        if active:
                            if st.button("선택 해제", key=f"unset_char_{ch['id']}"):
                                u["active_char"] = None
                                save_user_data()
                                st.info("캐릭터 선택 해제됨.")
                        else:
                            if st.button("선택", key=f"set_char_{ch['id']}"):
                                u["active_char"] = ch["id"]
                                save_user_data()
                                st.success(f"{ch['name']} 캐릭터 적용!")
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

        else:
            # 아이템 카테고리 탭
            try:
                cat = st.segmented_control("카테고리", options=list(SHOP_CATEGORIES.keys()), default="모자")
            except Exception:
                cat = st.radio("카테고리", list(SHOP_CATEGORIES.keys()), horizontal=True, index=0)

            cfg = SHOP_CATEGORIES[cat]
            items = cfg["items"]; owned_key = cfg["owned_key"]; eq_key = cfg["equipped_key"]

            cols = st.columns(4)
            for i, it in enumerate(items):
                with cols[i % 4]:
                    owned    = it["id"] in u.get(owned_key, [])
                    equipped = (u.get(eq_key) == it["id"])

                    st.markdown('<div class="card shop-card">', unsafe_allow_html=True)

                    # === 모자: 캐릭터 선택형 프리뷰 ===
                    if cat == "모자":
                        # 프리뷰 캐릭터 선택(세그먼트/라디오)
                        char_map = [("bear","곰"), ("cat","고양이"), ("rabbit","토끼"), ("shiba","시바")]
                        default_id = st.session_state.get("hat_preview_char") or (u.get("active_char") or "rabbit")
                        default_label = next((label for cid,label in char_map if cid==default_id), "토끼")
                        try:
                            sel_label = st.segmented_control("프리뷰 캐릭터", options=[l for _,l in char_map], default=default_label)
                        except Exception:
                            sel_label = st.radio("프리뷰 캐릭터", [l for _,l in char_map], horizontal=True,
                                                 index=[l for _,l in char_map].index(default_label))
                        sel_id = next(cid for cid,lbl in char_map if lbl==sel_label)
                        st.session_state["hat_preview_char"] = sel_id

                        main_img = get_shop_item_image_uri(cat, it["id"], sel_id)
                        st.markdown(f'<div><img src="{main_img}" class="shop-img" alt="hat"/></div>', unsafe_allow_html=True)

                        # 썸네일 4개(표시용)
                        st.markdown("<div class='thumb-row'>", unsafe_allow_html=True)
                        for cid, lbl in char_map:
                            thumb_uri = get_shop_item_image_uri(cat, it["id"], cid)
                            active_cls = "thumb active" if cid==sel_id else "thumb"
                            st.markdown(f'<div class="{active_cls}"><img src="{thumb_uri}" alt="{lbl}"/></div>', unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

                    else:
                        # 다른 카테고리는 일반 미리보기
                        img_uri = get_shop_item_image_uri(cat, it["id"])
                        st.markdown(f'<div><img src="{img_uri}" class="shop-img" alt="item"/></div>', unsafe_allow_html=True)

                    st.markdown(f"<div class='shop-name'>{it['name']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='shop-price'>가격: 🪙 {it['price']}</div>", unsafe_allow_html=True)

                    st.markdown("<div class='shop-btn'>", unsafe_allow_html=True)
                    if not owned:
                        if st.button(f"구매 ({it['name']})", key=f"buy_{cat}_{it['id']}"):
                            _buy_item(u, it["price"], owned_key, it["id"],
                                      f"'{it['name']}' 구매 완료!", "코인이 부족합니다.")
                    else:
                        if equipped:
                            if st.button("해제", key=f"unequip_{cat}_{it['id']}"):
                                _equip_item(u, owned_key, eq_key, None)
                                st.info(f"'{it['name']}' 해제됨.")
                        else:
                            if st.button("착용", key=f"equip_{cat}_{it['id']}"):
                                _equip_item(u, owned_key, eq_key, it["id"])
                                st.success(f"'{it['name']}' 착용!")
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

        st.write("")
        bottom = st.columns([1,1])
        with bottom[0]:
            st.button("🐾 내 캐릭터 보기", on_click=lambda: set_mode("char"))
        with bottom[1]:
            st.button("📊 랭킹으로", on_click=lambda: set_mode("ranking"))

    # 패널 닫기
    st.markdown('</div>', unsafe_allow_html=True)   # .panel-body
    st.markdown('</div>', unsafe_allow_html=True)   # .panel

# -------------------- route --------------------
mode = st.session_state.user_data.get("mode")
container_class = "container tight-top" if mode == "ranking" else "container"
st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)

if mode == "ranking":
    view_ranking()
elif mode == "shop":
    view_shop()
else:
    view_char()

st.markdown('</div>', unsafe_allow_html=True)
