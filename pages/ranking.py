# pages/ranking_and_shop.py
# -*- coding: utf-8 -*-
import streamlit as st
import os, json, base64

st.set_page_config(page_title="랭킹 & 캐릭터/상점", layout="wide", initial_sidebar_state="collapsed")

# -------------------- paths --------------------
USER_JSON_PATH = "user_data.json"
ASSETS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))

# -------------------- catalog --------------------
CHARACTERS = [
    {"id": "ddalkkak", "name": "딸깍공", "price": 0},
    {"id": "shiba",    "name": "강아지", "price": 1000},
    {"id": "cat",      "name": "고양이", "price": 1000},
    {"id": "rabbit",   "name": "토끼",   "price": 1000},
    {"id": "bear",     "name": "곰",     "price": 1000},
]
def char_kor_name(cid: str) -> str:
    return ("딸깍공" if cid=="ddalkkak" else
            "강아지" if cid=="shiba" else
            "고양이" if cid=="cat" else
            "토끼"   if cid=="rabbit" else
            "곰"     if cid=="bear" else "미보유")

# -------------------- defaults --------------------
ALL_CHAR_IDS = [c["id"] for c in CHARACTERS]
DEFAULT_DATA = {
    "dark_mode": False,
    "nickname": "-",
    "coins": 500,
    "mode": "ranking",                 # 'ranking' | 'shop'
    "active_char": "ddalkkak",
    "owned_chars": ALL_CHAR_IDS[:],    # ✅ 지금은 전부 보유로 세팅
    "owned_hats": [], "equipped_hat": None,
    "owned_glasses": [], "equipped_glasses": None,
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
    # 기본값 채우기
    for k, v in DEFAULT_DATA.items():
        if k not in data:
            data[k] = v
    # ✅ 지금은 항상 전부 보유(테스트용)
    data["owned_chars"] = ALL_CHAR_IDS[:]
    if not data.get("active_char"):
        data["active_char"] = "ddalkkak"
    return data

if "user_data" not in st.session_state:
    st.session_state.user_data = load_user_data()
else:
    # ✅ 세션 중에도 항상 전부 보유 상태 유지(테스트 기간)
    st.session_state.user_data["owned_chars"] = ALL_CHAR_IDS[:]

def save_user_data(silent=True):
    with open(USER_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(st.session_state.user_data, f, ensure_ascii=False, indent=2)
    if not silent: st.success("저장됨 💾")

def set_mode(m):
    st.session_state.user_data["mode"] = m
    save_user_data()

# 세션 첫 진입은 랭킹
if "_ranking_defaulted" not in st.session_state:
    st.session_state._ranking_defaulted = True
    set_mode("ranking")

# -------------------- theme & styles --------------------
dark = st.session_state.user_data.get("dark_mode", False)
if dark:
    bg_color = "#1C1C1E"; font_color = "#F2F2F2"
    card_bg = "#2C2C2E"; nav_bg = "#2C2C2E"; nav_link = "#F2F2F2"; sub_text = "#CFCFCF"
else:
    bg_color = "#F5F5F7"; font_color = "#2B2B2E"
    card_bg = "#FFFFFF"; nav_bg = "rgba(255,255,255,.9)"; nav_link = "#000"; sub_text = "#374151"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;800;900&display=swap');
html, body {{ background:{bg_color}; color:{font_color}; font-family:'Noto Sans KR', sans-serif; zoom:1.10; margin:0; }}
.stApp {{ background:{bg_color}; }}
.block-container {{ padding-top:0 !important; }}

/* 밑줄 전부 제거 */
a, a:hover, a:focus, a:visited {{ text-decoration:none !important; }}
.shop-name, .price-row, .side-chip, .nav-menu a, .nav-left a, .right-note-hero .hero-sub {{ text-decoration:none !important; }}

/* 본문 컨테이너 */
.container {{ max-width:1200px; margin:auto; padding:4px 40px 24px; }}
.container.tight-top {{ padding:0 40px 24px !important; }}

/* 스트림릿 기본 패널/툴바 숨김 */
.panel {{ display:none !important; }} .panel-body {{ padding:0 !important; margin:0 !important; }}
header, [data-testid="stSidebar"], [data-testid="stToolbar"] {{ display:none !important; }}
[data-testid="stHeading"] a, h1 a, h2 a, h3 a {{ display:none !important; }}

/* ===== 헤더 ===== */
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

/* ===== 랭킹 ===== */
.list-card {{ padding:0; }}
.row {{ display:flex; align-items:center; justify-content:space-between; padding:16px 18px; }}
.row + .row {{ border-top:1px dashed rgba(0,0,0,0.06); }}
.left {{ display:flex; align-items:center; gap:14px; }}
.badge {{ width:34px; height:34px; display:flex; align-items:center; justify-content:center; border-radius:10px; background:rgba(0,0,0,0.05); font-weight:800; color:#333; }}
.badge.gold   {{ background:#FCD34D; }}
.badge.silver {{ background:#E5E7EB; }}
.badge.bronze {{ background:#F59E0B; color:#fff; }}
.rank-avatar {{ width:44px; height:44px; border-radius:12px; display:flex; align-items:center; justify-content:center; background:linear-gradient(135deg,#DDEFFF,#F8FBFF); overflow:hidden; }}
.rank-avatar img {{ width:80%; height:80%; object-fit:contain; image-rendering:auto; }}
.small {{ color:{sub_text}; font-size:14px; }}

/* ===== 우측 캐릭터 카드 ===== */
.side-chip {{
  display:block; width:100%;
  background:linear-gradient(90deg,#FF9330,#FF7A00);
  color:#fff; font-weight:900; font-size:18px;
  padding:12px 16px; border-radius:18px;
  box-shadow:0 10px 22px rgba(255,147,48,.28);
  margin:0 0 12px 0;
}}
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
.right-note-hero .hero-sub {{ margin-top:8px; color:{sub_text}; font-size:13.5px; }}

/* ===== 상점: 카드 + 아래 CTA 카드 ===== */
.shop-grid {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:16px; margin-top:8px; }}
.card.shop-card {{ border-radius:28px; padding:28px; box-shadow:0 22px 55px rgba(0,0,0,.08); }}
.shop-name {{ font-weight:900; font-size:24px; color:#1f2937; margin-bottom:12px; }}
.shop-img {{ width:74%; max-width:260px; border-radius:16px; background:transparent; border:0; box-shadow:none; object-fit:contain; display:block; margin:10px auto 0; }}
.price-row {{ margin-top:16px; font-size:22px; font-weight:800; color:#1f2937; }}
.price-row .coin {{ font-size:1.05em; margin:0 6px; }}

/* CTA 아래 박스 */
.char-stack {{ display:flex; flex-direction:column; gap:10px; }}
.card.cta-card {{ border-radius:18px; padding:14px 16px; box-shadow:0 14px 34px rgba(0,0,0,.06); }}
.cta-row {{ display:flex; gap:10px; flex-wrap:wrap; align-items:center; }}
.cta-row form {{ display:inline-block; margin:0; }}

/* ⬜ 흰 배경 + 검정 글씨 버튼 */
.cta-btn {{ display:inline-block; padding:10px 18px; border-radius:14px; border:1px solid rgba(0,0,0,.06);
  font-weight:900; background:#FFFFFF; color:#111111; box-shadow:0 8px 18px rgba(0,0,0,.06); cursor:pointer; }}
.cta-btn:hover {{ background:#F3F4F6; }}
/* 회색 배지(보유중/사용중) */
.cta-pill {{ display:inline-block; padding:10px 16px; border-radius:14px; border:1px solid rgba(0,0,0,.06); background:#F1F2F4; color:#4B5563; font-weight:800; }}
.cta-pill.disabled {{ opacity:.55; }}

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
    if char_key == "ddalkkak" or not char_key:
        return ("data:image/svg+xml;utf8,"
                "<svg xmlns='http://www.w3.org/2000/svg' width='220' height='220'>"
                "<text x='50%' y='60%' font-size='96' text-anchor='middle'>🐾</text></svg>")
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
    return ("data:image/svg+xml;utf8,"
            "<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'>"
            "<text x='50%' y='60%' font-size='28' text-anchor='middle'>🐾</text></svg>")

def _avatar_uri_for_current_user() -> str:
    u = st.session_state.user_data
    return get_char_image_uri(u.get("active_char"), None)

# ---------- query params helpers ----------
def _get_query_params():
    try:
        return dict(st.query_params)  # >= 1.32
    except Exception:
        return {k: v[0] if isinstance(v, list) else v
                for k, v in st.experimental_get_query_params().items()}

def _set_query_params(new_params: dict):
    try:
        st.query_params.clear()
        if new_params:
            st.query_params.update(new_params)
    except Exception:
        st.experimental_set_query_params(**new_params)

# -------------------- header --------------------
header_avatar_uri = _avatar_uri_for_current_user()
st.markdown(
    '<div class="top-nav">'
    '  <div class="nav-left">'
    '    <div><a href="/mainpage" target="_self">🐾 딸깍공</a></div>'
    '    <div class="nav-menu">'
    '      <div><a href="/mainpage" target="_self">메인페이지</a></div>'
    '      <div><a href="/main" target="_self">공부 시작</a></div>'
    '      <div><a href="/ocr_paddle" target="_self">PDF요약</a></div>'
    '      <div><a href="/folder_page" target="_self">저장폴더</a></div>'
    '      <div><a href="/quiz" target="_self">퀴즈</a></div>'
    '      <div><a href="/report" target="_self">리포트</a></div>'
    '      <div><a href="/ranking" target="_self">랭킹</a></div>'
    '    </div>'
    '  </div>'
    f'  <div class="profile-group"><div class="profile-icon" title="내 캐릭터"><img src="{header_avatar_uri}" alt="avatar"/></div></div>'
    '</div>',
    unsafe_allow_html=True
)

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
    if period == "주간": return sorted(data, key=lambda x: (x["attempts"], x["points"]), reverse=True)
    if period == "월간": return sorted(data, key=lambda x: (x["points"], x["attempts"]), reverse=True)
    return sorted(data, key=lambda x: (x["attempts"]*2 + x["points"]//200), reverse=True)

# -------------------- views --------------------
def view_ranking():
    u = st.session_state.user_data
    left, right = st.columns([3,1], gap="large")

    with left:
        try:
            col1, col2 = st.columns([1.05, 2.2])
            with col1:
                period = st.segmented_control("기간", options=["주간","월간","전체"], default="주간")
            with col2:
                search = st.text_input("닉네임 검색", value="", placeholder="닉네임 검색", label_visibility="collapsed")
        except Exception:
            col1, col2 = st.columns([1.05, 2.2])
            with col1:
                period = st.radio("기간", ["주간","월간","전체"], horizontal=True, index=0)
            with col2:
                search = st.text_input("닉네임 검색", value="", placeholder="닉네임 검색")

        ranked = sort_by_period(period, RANK_DATA)
        if search.strip():
            q = search.strip().lower()
            ranked = [r for r in ranked if q in r["name"].lower()]

        avatar_uri = _avatar_uri_for_current_user()
        st.markdown('<div class="card list-card">', unsafe_allow_html=True)
        for i, r in enumerate(ranked, 1):
            cls = "badge"
            if i == 1: cls += " gold"
            elif i == 2: cls += " silver"
            elif i == 3: cls += " bronze"
            st.markdown(
                '<div class="row">'
                f'  <div class="left"><div class="{cls}">{i}</div>'
                f'    <div class="rank-avatar"><img src="{avatar_uri}" alt="avatar"/></div>'
                f'    <div><div style="font-weight:700">{r["name"]}</div>'
                f'      <div class="small">출석횟수 {r["attempts"]}회</div></div>'
                f'  </div>'
                f'  <div style="display:flex; gap:10px; align-items:center;">'
                f'    <div class="small">출석횟수 {max(1, r["attempts"]//2)}회</div>'
                f'    <div class="small">⭐ {r["points"]}</div>'
                f'  </div>'
                '</div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="side-chip">내 캐릭터</div>', unsafe_allow_html=True)
        active_name = char_kor_name(u.get("active_char") or "")
        preview_uri = _avatar_uri_for_current_user()
        st.markdown(
            f'<div class="card right-note right-note-hero">'
            f'  <div class="hero-circle"><img src="{preview_uri}" alt="avatar"/></div>'
            f'  <div class="hero-sub">{active_name}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
        st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)
        if st.button("🏬 상점페이지", key="go_shop_side", help="캐릭터/아이템 구매하러 가기"):
            set_mode("shop"); st.rerun()

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

    # ---- 쿼리파라미터 처리: 구매 / 사용 ----
    qp = _get_query_params()
    url_mode = qp.get("mode")
    if isinstance(url_mode, list): url_mode = url_mode[0]
    if url_mode in ("shop", "ranking") and st.session_state.user_data.get("mode") != url_mode:
        set_mode(url_mode)

    buy = qp.get("shop_buy")
    use = qp.get("use_char")
    if isinstance(buy, list): buy = buy[0]
    if isinstance(use, list): use = use[0]

    if buy:
        ch_map = {c["id"]: c for c in CHARACTERS}
        if buy in ch_map:
            ch = ch_map[buy]
            if buy in u.get("owned_chars", []):
                st.info("이미 보유중입니다.")
            else:
                _buy_item(u, ch["price"], "owned_chars", buy,
                          f"'{ch['name']}' 캐릭터 구매 완료! 이제 '선택'을 눌러 적용하세요.",
                          "포인트가 부족합니다.")
        qp.pop("shop_buy", None)
        qp["mode"] = "shop"
        _set_query_params(qp)

    if use:
        if use in u.get("owned_chars", []):
            u["active_char"] = use
            set_mode("shop")
            save_user_data()
            st.success(f"{char_kor_name(use)} 캐릭터 사용 중!")
            qp.pop("use_char", None)
            qp["mode"] = "shop"
            _set_query_params(qp)
            st.rerun()
        else:
            st.error("보유하지 않은 캐릭터입니다.")
            qp.pop("use_char", None); qp["mode"]="shop"; _set_query_params(qp)

    left, right = st.columns([3,1], gap="large")

    with right:
        st.markdown('<div class="side-chip">내 캐릭터</div>', unsafe_allow_html=True)
        preview_uri = _avatar_uri_for_current_user()
        active_name = char_kor_name(u.get("active_char") or "")
        st.markdown(
            f'<div class="card right-note right-note-hero">'
            f'  <div class="hero-circle"><img src="{preview_uri}" alt="avatar"/></div>'
            f'  <div class="hero-sub">{active_name}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    with left:
        st.markdown(f'<div style="font-weight:900; margin:6px 0 10px;">보유 포인트: 🪙 {u.get("coins",0)}</div>', unsafe_allow_html=True)

        # ---- HTML Grid 렌더(위: 이름/이미지/가격, 아래: 버튼 카드) ----
        order = ["shiba", "cat", "rabbit", "bear"]
        card_chars = [c for c in CHARACTERS if c["id"] in order]

        parts = ['<div class="shop-grid">']
        for ch in card_chars:
            owned = ch["id"] in u.get("owned_chars", [])
            active = (u.get("active_char") == ch["id"])
            img_uri = get_char_image_uri(ch["id"], None)

            top_card = (
                f'<div class="card shop-card">'
                f'  <div class="shop-name">{ch["name"]}</div>'
                f'  <div><img src="{img_uri}" class="shop-img" alt="char"/></div>'
                f'  <div class="price-row">가격:<span class="coin"> 🪙</span> {ch["price"]}</div>'
                f'</div>'
            )

            # 버튼 영역: form(method=get) → 같은 탭에서만 동작
            if not owned:
                btns = (
                    f'<form method="get">'
                    f'  <input type="hidden" name="mode" value="shop"/>'
                    f'  <input type="hidden" name="shop_buy" value="{ch["id"]}"/>'
                    f'  <button type="submit" class="cta-btn">구매</button>'
                    f'</form>'
                    f'<form method="get">'
                    f'  <input type="hidden" name="mode" value="shop"/>'
                    f'  <input type="hidden" name="use_char" value="{ch["id"]}"/>'
                    f'  <button type="submit" class="cta-btn">선택</button>'
                    f'</form>'
                )
            elif active:
                btns = (
                    f'<span class="cta-pill">보유중</span>'
                    f'<span class="cta-pill disabled">사용중</span>'
                )
            else:
                btns = (
                    f'<span class="cta-pill">보유중</span>'
                    f'<form method="get">'
                    f'  <input type="hidden" name="mode" value="shop"/>'
                    f'  <input type="hidden" name="use_char" value="{ch["id"]}"/>'
                    f'  <button type="submit" class="cta-btn">선택</button>'
                    f'</form>'
                )

            bottom_card = f'<div class="card cta-card"><div class="cta-row">{btns}</div></div>'
            parts.append(f'<div class="char-stack">{top_card}{bottom_card}</div>')

        parts.append('</div>')
        st.markdown("".join(parts), unsafe_allow_html=True)

        bl, _ = st.columns([1,5])
        with bl:
            st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
            st.button("📊 랭킹페이지", on_click=lambda: set_mode("ranking"))

# -------------------- route --------------------
qp_route = _get_query_params()
url_mode = qp_route.get("mode")
if isinstance(url_mode, list): url_mode = url_mode[0]
if url_mode in ("ranking", "shop") and st.session_state.user_data.get("mode") != url_mode:
    set_mode(url_mode)

mode = st.session_state.user_data.get("mode")
if mode not in ("ranking", "shop"):
    mode = "ranking"; set_mode(mode)

container_class = "container tight-top" + (" shop-mode" if mode == "shop" else "")
st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)
if mode == "ranking":
    view_ranking()
else:
    view_shop()
st.markdown('</div>', unsafe_allow_html=True)
