# pages/ranking.py
# -*- coding: utf-8 -*-
import streamlit as st
import os, base64, requests
from components.header import render_header
from components.auth import require_login

print(f"✅✅✅ Executing: {__file__} ✅✅✅")
BACKEND_URL = "http://127.0.0.1:8080"
require_login(BACKEND_URL)

# ─────────────────────────────────────────────
# 세션 유저 기본값
user = st.session_state.get("user", {}) or {}
USER_ID = (user.get("_id") or user.get("id") or user.get("user_id") or "")
USER_ID = USER_ID.get("$oid") if isinstance(USER_ID, dict) and "$oid" in USER_ID else USER_ID

# -------------------- paths & items --------------------
ASSETS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))

# -------------------- catalog --------------------
CHARACTERS = [
    {"id": "ddalkkak", "name": "딸깍공", "price": 0},
    {"id": "shiba",    "name": "강아지", "price": 1000},  # assets 파일명은 siba.png 임
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

ALL_CHAR_IDS = [c["id"] for c in CHARACTERS]

# -------------------- session storage --------------------
DEFAULT_DATA = {
    "nickname": st.session_state.get("user", {}).get("nickname", "-"),
    "coins": 0,                         # 서버 points 동기화
    "mode": "ranking",                  # 'ranking' | 'shop'
    "active_char": "ddalkkak",
    "owned_chars": [],                  # 서버와 동기화
    "owned_hats": [], "equipped_hat": None,
    "owned_glasses": [], "equipped_glasses": None,
    "owned_scarves": [],  "equipped_scarf": None,
    "owned_clothes": [],  "equipped_clothes": None,
    "owned_shoes": [],    "equipped_shoes": None,
    "owned_wings": [],    "equipped_wings": None,
}
def _init_user_data():
    data = {k: (v[:] if isinstance(v, list) else v) for k, v in DEFAULT_DATA.items()}
    st.session_state.user_data = data
if "user_data" not in st.session_state:
    _init_user_data()

# ─────────────────────────────────────────────
# 서버 API
def _auth_headers():
    tok = st.session_state.get("auth_token")
    return {"Authorization": f"Bearer {tok}"} if tok else {}

def api_shop_state():
    r = requests.get(f"{BACKEND_URL}/shop/state",
                     params={"user_id": USER_ID}, timeout=8, headers=_auth_headers())
    r.raise_for_status()
    return r.json()["state"]

def api_shop_buy(char_id: str):
    body = {"user_id": USER_ID, "char_id": char_id}
    r = requests.post(f"{BACKEND_URL}/shop/buy", json=body, timeout=8, headers=_auth_headers())
    if r.status_code >= 400:
        try: st.error(r.json().get("detail") or "구매 실패")
        except Exception: st.error("구매 실패")
        return api_shop_state()
    return r.json()["state"]

def api_shop_select(char_id: str):
    body = {"user_id": USER_ID, "char_id": char_id}
    r = requests.post(f"{BACKEND_URL}/shop/select", json=body, timeout=8, headers=_auth_headers())
    if r.status_code >= 400:
        try: st.error(r.json().get("detail") or "선택 실패")
        except Exception: st.error("선택 실패")
        return api_shop_state()
    return r.json()["state"]

def fetch_ranking(period_kor: str):
    period_map = {"주간": "weekly", "월간": "monthly", "전체": "all"}
    period = period_map.get(period_kor, "weekly")
    try:
        r = requests.get(
            f"{BACKEND_URL}/ranking/top",
            params={"period": period, "limit": 100},
            timeout=10, headers=_auth_headers()
        )
        r.raise_for_status()
        rows = r.json().get("rows", [])
        # ✅ 여기서 각 row에 active_char 채워 넣기
        return _enrich_rows_with_char(rows)
    except Exception as e:
        st.error(f"랭킹을 불러오지 못했습니다: {e}")
        return []
    
def _extract_user_id(doc) -> str | None:
    for k in ("user_id", "userId", "uid", "id", "_id"):
        if k in doc and doc[k]:
            v = doc[k]
            if isinstance(v, dict) and "$oid" in v:
                return v["$oid"]
            return str(v)
    return None

def _fetch_active_char(uid: str) -> str | None:
    try:
        r = requests.get(
            f"{BACKEND_URL}/shop/state",
            params={"user_id": uid},
            headers=_auth_headers(),
            timeout=6,
        )
        r.raise_for_status()
        return (r.json().get("state") or {}).get("active_char")
    except Exception:
        return None

def _enrich_rows_with_char(rows: list[dict]) -> list[dict]:
    cache: dict[str, str | None] = {}
    for row in rows:
        # 백엔드가 다른 키로 내려줄 수도 있어 대비
        char = (
            row.get("active_char")
            or row.get("character")
            or row.get("char")
            or row.get("avatar")
        )
        if not char:
            uid = _extract_user_id(row)
            if uid:
                if uid not in cache:
                    cache[uid] = _fetch_active_char(uid)
                char = cache[uid]
        row["active_char"] = (char or "ddalkkak")
    return rows

# ─────────────────────────────────────────────
# 쿼리 파라미터 유틸 (최신/구버전 호환)
def _get_query_params() -> dict:
    try:
        return {k: v for k, v in st.query_params.items()}
    except Exception:
        return st.experimental_get_query_params()

def _set_query_params(params: dict) -> None:
    try:
        st.query_params.clear()
        fixed = {k: (v if isinstance(v, str) else (v[0] if isinstance(v, list) and v else ""))
                 for k, v in params.items()}
        st.query_params.update(fixed)
    except Exception:
        st.experimental_set_query_params(**params)

# ─────────────────────────────────────────────
# 아바타 이미지 유틸
def to_data_uri(abs_path: str) -> str:
    with open(abs_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/png;base64,{b64}"

def get_char_image_uri(char_key: str | None, hat_id: str | None = None) -> str:
    if char_key:
        char_key = str(char_key).strip().lower()
    if not char_key or char_key == "ddalkkak":
        return ("data:image/svg+xml;utf8,"
                "<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'>"
                "<text x='50%' y='60%' font-size='28' text-anchor='middle'>🐾</text></svg>")
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
    char_key = u.get("active_char")
    hat_id = u.get("equipped_hat")
    if hat_id and (hat_id in u.get("owned_hats", [])):
        return get_char_image_uri(char_key, hat_id)
    return get_char_image_uri(char_key, None)

# ─────────────────────────────────────────────
# 상태 동기화 + 헤더 아이콘 반영
def sync_from_backend():
    try:
        s = api_shop_state()
        u = st.session_state.user_data
        u["coins"] = int(s.get("points", 0))
        u["active_char"] = s.get("active_char") or "ddalkkak"
        u["owned_chars"] = s.get("owned_chars", [])
    except Exception as e:
        st.warning(f"상점 상태를 불러오지 못했습니다. (오프라인 모드) - {e}")

# 최초 진입 시
if "_ranking_defaulted" not in st.session_state:
    st.session_state._ranking_defaulted = True
    st.session_state.user_data["mode"] = "ranking"
    sync_from_backend()

# ── 헤더 (내 캐릭터 아이콘) ──
render_header(char_key=st.session_state.user_data.get("active_char"))

# ─────────────────────────────────────────────
# 스타일
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

a, a:hover, a:focus, a:visited {{ text-decoration:none !important; }}
.panel {{ display:none !important; }} .panel-body {{ padding:0 !important; margin:0 !important; }}

.card {{ background:{card_bg}; border:1px solid rgba(0,0,0,.06); border-radius:18px; padding:16px; box-shadow:0 10px 28px rgba(0,0,0,.06); margin-top:16px; }}
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

.shop-grid {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:16px; margin-top:8px; }}
.card.shop-card {{ border-radius:28px; padding:28px; box-shadow:0 22px 55px rgba(0,0,0,.08); }}
.shop-name {{ font-weight:900; font-size:24px; color:#1f2937; margin-bottom:12px; }}
.shop-img {{ width:74%; max-width:260px; border-radius:16px; background:transparent; border:0; box-shadow:none; object-fit:contain; display:block; margin:10px auto 0; }}
.price-row {{ margin-top:16px; font-size:22px; font-weight:800; color:#1f2937; }}
.price-row .coin {{ font-size:1.05em; margin:0 6px; }}

.cta-pill {{ display:inline-block; padding:10px 16px; border-radius:14px; border:1px solid rgba(0,0,0,.06); background:#F1F2F4; color:#4B5563; font-weight:800; }}
.cta-pill.disabled {{ opacity:.55; }}

/* ────────────────────────────────────────────
   SHOP 버튼 래퍼까지 강제 리셋 (하얀 바 제거)
   ──────────────────────────────────────────── */
.shop-scope [data-testid="stButton"] {{ 
  display:inline-block !important; width:auto !important; 
  margin:0 !important; padding:0 !important;
  background:transparent !important; border:0 !important; box-shadow:none !important;
}}
.shop-scope [data-testid="stButton"] > div {{
  display:inline-block !important; width:auto !important; 
  margin:0 !important; padding:0 !important;
  background:transparent !important; border:0 !important; box-shadow:none !important;
}}
/* Streamlit 새 버튼 베이스 래퍼 */
.shop-scope [data-testid^="baseButton-"] {{
  display:inline-block !important; width:auto !important;
  margin:0 !important; padding:0 !important;
  background:transparent !important; border:0 !important; box-shadow:none !important;
}}
/* 혹시 남는 빈 래퍼 자체 숨김 */
.shop-scope [data-testid="stButton"]:has(button:empty) {{ display:none !important; }}

/* 버튼 자체 */
.shop-scope button[kind],
.shop-scope .stButton > button,
.shop-scope [data-testid^="baseButton-"] > button {{
  width:auto !important; min-width:auto !important;
  display:inline-flex !important; align-items:center; justify-content:center;
  padding:10px 18px !important; border-radius:14px !important;
  border:1px solid rgba(0,0,0,.06) !important; background:#FFFFFF !important; color:#111111 !important;
  font-weight:900 !important; box-shadow:0 8px 18px rgba(0,0,0,.06) !important;
}}
.shop-scope button[kind]:hover,
.shop-scope .stButton > button:hover,
.shop-scope [data-testid^="baseButton-"] > button:hover {{
  background:#F3F4F6 !important;
}}

/* CTA 줄 정렬 */
.shop-scope .cta-row {{ display:flex; gap:10px; flex-wrap:wrap; align-items:center; }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 뷰

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

        ranked = fetch_ranking(period)
        if search.strip():
            q = search.strip().lower()
            ranked = [r for r in ranked if q in (r.get("name","").lower())]

        st.markdown('<div class="card list-card">', unsafe_allow_html=True)
        for i, r in enumerate(ranked, 1):
            cls = "badge"
            if i == 1: cls += " gold"
            elif i == 2: cls += " silver"
            elif i == 3: cls += " bronze"
            name = r.get("name","-")
            attempts = int(r.get("attempts",0))
            points = int(r.get("points",0))

            # ✅ 각 유저의 active_char 로 개별 아이콘
            row_char = (r.get("active_char") or "ddalkkak").strip()
            row_avatar_uri = get_char_image_uri(row_char)

            st.markdown(
                '<div class="row">'
                f'  <div class="left"><div class="{cls}">{i}</div>'
                f'    <div class="rank-avatar"><img src="{row_avatar_uri}" alt="avatar"/></div>'
                f'    <div><div style="font-weight:700">{name}</div>'
                f'      <div class="small">출석횟수 {attempts}회</div></div>'
                f'  </div>'
                f'  <div style="display:flex; gap:10px; align-items:center;">'
                f'    <div class="small">출석횟수 {attempts}회</div>'
                f'    <div class="small">⭐ {points}</div>'
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
            st.session_state.user_data["mode"] = "shop"
            st.rerun()

def view_shop():
    u = st.session_state.user_data

    # (선택) 모드 쿼리만 읽어 초기 진입 시 딥링크 허용
    qp = _get_query_params()
    url_mode = qp.get("mode")
    if isinstance(url_mode, list):
        url_mode = url_mode[0]
    if url_mode in ("shop", "ranking") and st.session_state.user_data.get("mode") != url_mode:
        st.session_state.user_data["mode"] = url_mode

    # 최신 상태
    sync_from_backend()

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

        # ▼ shop-scope 시작 (이 안의 버튼은 모두 카드 스킨 & 바 제거)
        st.markdown('<div class="shop-scope">', unsafe_allow_html=True)

        order = ["shiba", "cat", "rabbit", "bear"]
        card_chars = [c for c in CHARACTERS if c["id"] in order]

        cols = st.columns(4, gap="small")
        for idx, ch in enumerate(card_chars):
            with cols[idx % 4]:
                owned = ch["id"] in u.get("owned_chars", [])
                active = (u.get("active_char") == ch["id"])
                img_uri = get_char_image_uri(ch["id"], None)

                st.markdown(
                    f'<div class="card shop-card">'
                    f'  <div class="shop-name">{ch["name"]}</div>'
                    f'  <div><img src="{img_uri}" class="shop-img" alt="char"/></div>'
                    f'  <div class="price-row">가격:<span class="coin"> 🪙</span> {ch["price"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                # CTA 줄(버튼/배지)
                st.markdown('<div class="cta-row">', unsafe_allow_html=True)

                if not owned:
                    can_buy = (u.get("coins", 0) >= ch["price"])
                    if can_buy:
                        if st.button("구매", key=f"buy_{ch['id']}"):
                            new_state = api_shop_buy(ch["id"])
                            u["coins"] = int(new_state.get("points", 0))
                            u["owned_chars"] = new_state.get("owned_chars", [])
                            u["active_char"] = new_state.get("active_char") or u.get("active_char")
                            # 헤더 아이콘 갱신
                            render_header(char_key=u["active_char"])
                            st.success(f"'{ch['name']}' 구매 완료!")
                            st.rerun()
                    else:
                        st.markdown('<span class="cta-pill disabled">포인트부족</span>', unsafe_allow_html=True)

                    if st.button("선택", key=f"use_{ch['id']}"):
                        new_state = api_shop_select(ch["id"])
                        u["active_char"] = new_state.get("active_char") or u.get("active_char")
                        u["coins"] = int(new_state.get("points", 0))
                        u["owned_chars"] = new_state.get("owned_chars", [])
                        render_header(char_key=u["active_char"])
                        st.rerun()

                elif active:
                    st.markdown(
                        '<span class="cta-pill">보유중</span>'
                        '<span class="cta-pill disabled">사용중</span>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown('<span class="cta-pill">보유중</span>', unsafe_allow_html=True)
                    if st.button("선택", key=f"use_{ch['id']}"):
                        new_state = api_shop_select(ch["id"])
                        u["active_char"] = new_state.get("active_char") or u.get("active_char")
                        u["coins"] = int(new_state.get("points", 0))
                        u["owned_chars"] = new_state.get("owned_chars", [])
                        render_header(char_key=u["active_char"])
                        st.success(f"{char_kor_name(ch['id'])} 캐릭터 사용 중!")
                        st.rerun()

                st.markdown('</div>', unsafe_allow_html=True)  # CTA 닫기

            if idx % 4 == 3 and idx != len(card_chars) - 1:
                cols = st.columns(4, gap="small")

        # ▲ shop-scope 끝
        st.markdown('</div>', unsafe_allow_html=True)

        # 하단 네비
        bl, _ = st.columns([1,5])
        with bl:
            st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
            if st.button("📊 랭킹페이지", use_container_width=True):
                st.session_state.user_data["mode"] = "ranking"
                st.rerun()

# -------------------- route --------------------
qp_route = _get_query_params()
url_mode = qp_route.get("mode")
if isinstance(url_mode, list): url_mode = url_mode[0]
if url_mode in ("ranking", "shop") and st.session_state.user_data.get("mode") != url_mode:
    st.session_state.user_data["mode"] = url_mode

mode = st.session_state.user_data.get("mode") or "ranking"
container_class = "container tight-top" + (" shop-mode" if mode == "shop" else "")
st.markdown(f'<div class="{container_class}">', unsafe_allow_html=True)
if mode == "ranking":
    view_ranking()
else:
    view_shop()
st.markdown('</div>', unsafe_allow_html=True)
