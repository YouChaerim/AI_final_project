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
    sub_text = "#CFCFCF"
else:
    bg_color = "#F5F5F7"; font_color = "#2B2B2E"
    card_bg = "#FFFFFF"; nav_bg = "rgba(255,255,255,.9)"; nav_link = "#000"
    sub_text = "#6B7280"

# 폴더 페이지와 동일한 패널 배경/그림자 변수
panel_bg     = "#1F1F22" if dark else "#FFFFFF"
panel_shadow = "rgba(0,0,0,.35)" if dark else "rgba(0,0,0,.08)"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;800;900&display=swap');
html, body {{ background:{bg_color}; color:{font_color}; font-family:'Noto Sans KR', sans-serif; zoom:1.10; margin:0; }}
.stApp {{ background:{bg_color}; }}
.block-container {{ padding-top:0 !important; }}

/* 본문 컨테이너: 헤더 바로 아래 간격 최소 (folder_page와 동일) */
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
.card {{ background:{card_bg}; border:1px solid rgba(0,0,0,.06); border-radius:16px; padding:14px; box-shadow:0 8px 22px rgba(0,0,0,.06); margin-top:16px; }}

/* ===== 폴더 페이지와 동일한 패널 규격 ===== */
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

/* 컨트롤 바 */
.toolbar {{ display:flex; gap:16px; align-items:center; }}
.pill {{ padding:10px 16px; border-radius:12px; background:{card_bg}; border:1px solid rgba(0,0,0,.06); font-weight:700; }}
.input {{ flex:1; }}

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

/* 사이드 카드 */
.side-card .big {{ font-size:28px; font-weight:800; }}
.side-card .muted {{ color:{sub_text}; }}
.full-btn {{
  width:100%; padding:12px 14px; border-radius:12px; border:none;
  background:#FF9330; color:white; font-weight:800; cursor:pointer;
}}
.full-btn:active {{ transform:translateY(1px); }}
.right-note {{ text-align:center; padding:18px 10px; }}
.right-note .emoji {{ font-size:42px; }}

/* 스트림릿이 간혹 뿌리는 빈 블럭 제거 */
.block-container > div:empty {{ display:none !important; margin:0 !important; padding:0 !important; }}
</style>
""", unsafe_allow_html=True)

# -------------------- helpers --------------------
def to_data_uri(abs_path: str) -> str:
    with open(abs_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:image/png;base64,{b64}"

def get_char_image_uri(char_key: str, hat_id: str | None = None) -> str:
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

    # 폴더 페이지와 동일한 패널 구조로 제목/본문 래핑
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-head">랭킹</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-body">', unsafe_allow_html=True)

    # Toolbar (기간 필터 + 검색)
    c1, c2 = st.columns([1,3])
    with c1:
        try:
            period = st.segmented_control("기간", options=["주간","월간","전체"], default="주간")
        except Exception:
            period = st.radio("기간", ["주간","월간","전체"], horizontal=True, index=0)
    with c2:
        q = st.text_input("닉네임 검색", "", placeholder="닉네임 검색", label_visibility="collapsed")

    # Two-column layout: list (left) / side (right)
    left, right = st.columns([3,1])

    # ---------- Left: Ranking list ----------
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
                  <div class="small">습관 실행 {r["attempts"]}회</div>
                </div>
              </div>
              <div style="display:flex; gap:10px; align-items:center;">
                <div class="small">습관 실행 {max(1, r["attempts"]//2)}회</div>
                <div class="small">⭐ {r["points"]}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ---------- Right: My info + Hat promo ----------
    with right:
        # 내 정보 카드
        st.markdown('<div class="card side-card">', unsafe_allow_html=True)

        # 내 랭크 계산
        my_name = (u.get("nickname") or "").strip()
        my_rank = None
        for idx, row in enumerate(ranked, 1):
            if row["name"] == my_name:
                my_rank = idx
                break

        rank_text = f"#{my_rank}" if my_rank else "—"
        total = len(ranked)

        st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
              <div style="font-weight:800;">내 정보</div>
              <div class="profile-icon"><img src="{header_avatar_uri}"/></div>
            </div>
            <div style="display:flex; align-items:center; gap:14px; margin:8px 2px 16px 2px;">
              <div class="big">{rank_text}</div>
              <div class="muted">전체 {total}명</div>
            </div>
        """, unsafe_allow_html=True)

        # 버튼: 상점으로 이동 (shop 모드)
        if st.button("상점으로 이동", key="go_shop_side", help="모자를 구매/착용하러 가기"):
            set_mode("shop")
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        # 모자 착용! 카드
        st.markdown(f"""
        <div class="card right-note">
          <div class="emoji">🧢</div>
          <div style="font-weight:800; margin-top:6px;">모자 착용!</div>
          <div class="muted" style="margin-top:6px;">상점에서 모자를 구매하고 착용하면<br/>캐릭터 이미지가 바뀝니다.</div>
        </div>
        """, unsafe_allow_html=True)

    # 패널 닫기
    st.markdown('</div>', unsafe_allow_html=True)  # </div> .panel-body
    st.markdown('</div>', unsafe_allow_html=True)  # </div> .panel

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
    <div class="card" style="max-width:420px; margin:10px auto 0;">
      <div style="position:relative; width:100%; aspect-ratio: 4/5; border-radius:14px; border:1px dashed rgba(0,0,0,.06);
                  background: radial-gradient(ellipse at center, rgba(255,147,48,0.10), transparent 60%), {card_bg}; overflow:hidden;">
        <img style="position:absolute; left:50%; top:62%; transform:translate(-50%,-62%); width:min(56%, 220px); image-rendering:auto;" src="{img_uri}" />
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
