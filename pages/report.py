# pages/report.py
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta, time
import random
import os, json, base64, requests
from components.header import render_header
from components.auth import require_login

print(f"✅✅✅ Executing: {__file__} ✅✅✅")
BACKEND_URL = "http://127.0.0.1:8080"  # 파일에 이미 있다면 그 값 사용
require_login(BACKEND_URL)

user = st.session_state.get("user", {}) or {}
USER_ID = user.get("id") or user.get("_id") or user.get("user_id") or ""

dark = user.get("dark_mode", False)

# ---- 컬러 ----
if dark:
    bg = "#1C1C1E"; fg = "#F2F2F2"; nav_bg = "#2C2C2E"
    panel_bg = "#1F1F22"; panel_shadow = "rgba(0,0,0,.35)"
else:
    bg = "#F5F5F7"; fg = "#2B2B2E"; nav_bg = "rgba(255,255,255,.9)"
    panel_bg = "#FFFFFF"; panel_shadow = "rgba(0,0,0,.08)"

# ---- 아바타/에셋 ----
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
                cands += [
                    os.path.join(ASSETS_ROOT, "items", "hats", f"{k}{sep}{hat_id}.png"),
                    os.path.join(ASSETS_ROOT, "characters", f"{k}{sep}{hat_id}.png"),
                ]
    for k in keys:
        cands.append(os.path.join(ASSETS_ROOT, "characters", f"{k}.png"))
    for p in cands:
        if os.path.exists(p):
            return _to_data_uri(p)
    return ("data:image/svg+xml;utf8,"
            "<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'>"
            "<text x='50%' y='60%' font-size='28' text-anchor='middle'>🐾</text>"
            "</svg>")

def current_avatar_uri() -> str:
    char_key = user.get("active_char", "rabbit")
    hat_id = user.get("equipped_hat")
    if hat_id and (hat_id in user.get("owned_hats", [])):
        return get_char_image_uri(char_key, hat_id)
    return get_char_image_uri(char_key)
header_avatar_uri = current_avatar_uri()

def _extract_backend_uid(u: dict) -> str:
    v = u.get("_id")
    if isinstance(v, dict) and "$oid" in v: return v["$oid"]
    if isinstance(v, str) and len(v) == 24: return v
    for k in ("id","user_id","local_user_id","localUserId","provider_id"):
        vv = u.get(k)
        if isinstance(vv, dict) and "$oid" in vv: return vv["$oid"]
        if isinstance(vv, str): return vv
    return ""

USER_KEY = _extract_backend_uid(user)

if not USER_KEY:
    st.error("사용자 식별값이 없습니다. 다시 로그인해 주세요.")
    st.stop()

def fetch_daily(start_d, end_d):
    url = f"{BACKEND_URL}/reports/daily/{USER_KEY}"
    r = requests.get(url, params={"start": start_d.isoformat(), "end": end_d.isoformat()}, timeout=15)
    r.raise_for_status()
    return r.json()

def fetch_focus(day_d):
    url = f"{BACKEND_URL}/reports/focus/{USER_KEY}"
    r = requests.get(url, params={"day": day_d.isoformat()}, timeout=10)
    r.raise_for_status()
    return r.json().get("events", [])

# ================= CSS (폴더 헤더 1:1 + 헤더 밀착 + 드롭다운 겹침 해결) =================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;800;900&display=swap');

html, body {{ background:{bg}; color:{fg}; font-family:'Noto Sans KR', sans-serif; zoom:1.10; margin:0; }}
.stApp {{ background:{bg}; }}
.block-container {{ padding-top:0 !important; }}
header {{ display:none !important; }}

/* 본문 컨테이너: 상단 여백 완전 제거 */
.container {{ max-width:1200px; margin:auto; padding:0 40px 24px; }}

/* 헤더(폴더 페이지와 동일) */
a, a:hover, a:focus, a:visited {{ text-decoration:none !important; }}
.top-nav {{
  display:flex; justify-content:space-between; align-items:center;
  padding:12px 0; margin-top:40px !important; margin-bottom:0 !important;
  background:{nav_bg}; box-shadow:0 2px 4px rgba(0,0,0,.05);
}}
.nav-left {{ display:flex; align-items:center; gap:60px; }}
.top-nav .nav-left > div:first-child a {{ color:#000 !important; font-size:28px; font-weight:900; }}
.nav-menu {{ display:flex; gap:36px; font-size:18px; font-weight:700; }}
.nav-menu div a {{ color:#000 !important; transition:.2s; }}
.nav-menu div:hover a {{ color:#FF9330 !important; }}
.profile-group {{ display:flex; gap:16px; align-items:center; margin-right:12px; }}
.profile-icon {{
  width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#DDEFFF,#F8FBFF);
  overflow:hidden;display:flex;align-items:center;justify-content:center;box-shadow:0 1px 2px rgba(0,0,0,.06);
}}
.profile-icon img {{ width:100%; height:100%; object-fit:contain; }}

/* 헤더 바로 다음 형제 블록들의 상단 여백/패딩 제거 */
.top-nav + * {{ margin-top:0 !important; padding-top:0 !important; }}
.top-nav + [data-testid="stVerticalBlock"],
.top-nav + div [data-testid="stVerticalBlock"] {{
  margin-top:0 !important; padding-top:0 !important;
}}

/* 패널 */
.panel {{
  position: relative;
  background:{panel_bg};
  border-radius:18px;
  box-shadow:0 6px 24px {panel_shadow};
  overflow:visible !important;   /* ▼ 드롭다운이 패널 밖으로 나와도 보이도록 */
  margin-top:0 !important;
}}
.panel-head {{
  background: linear-gradient(90deg,#FF9330,#FF7A00);
  color:white; text-align:center; font-size:34px; font-weight:900; padding:18px 20px;
}}
.panel-body {{ padding:0 36px 20px !important; }}

/* 요약카드 */
.metrics {{
  display:grid; grid-template-columns:repeat(3,1fr);
  gap:10px; margin-top:6px;
}}
.metric {{
  background:{panel_bg}; border-radius:12px; padding:14px;
  box-shadow:0 4px 12px rgba(0,0,0,.06); border:1px solid rgba(0,0,0,.06);
}}
.metric .label {{ font-size:13px; font-weight:900; color:#6B7280; letter-spacing:.02em; margin-bottom:2px; }}
.metric .value {{ font-size:28px; font-weight:900; line-height:1.1; }}

/* 섹션 헤더 */
.section-head {{
  display:flex; align-items:center; gap:8px;
  background:{panel_bg}; border:1px solid rgba(0,0,0,.06);
  border-radius:14px; padding:12px 14px; margin:10px 0 8px;
  box-shadow:0 4px 12px rgba(0,0,0,.06); font-weight:900;
}}
.section-head .chev {{ margin-left:auto; opacity:.5; }}

/* 흰 카드(Plotly 컨테이너) */
[data-testid="stVerticalBlockBorderWrapper"]{{
  background:#FFFFFF; border:1px solid rgba(0,0,0,.06);
  border-radius:14px; box-shadow:0 4px 12px rgba(0,0,0,.06);
  padding:10px 12px;
}}

/* 하루 집중도 박스 */
.focus-guard {{
  border-radius:12px;
  overflow:hidden;
  padding:0;
  overscroll-behavior:contain;
  touch-action: pan-x;
  position:relative;
}}
.focus-guard [data-testid="stPlotlyChart"],
.focus-guard [data-testid="stPlotlyChart"]>div,
.focus-guard .plotly, .focus-guard .js-plotly-plot, .focus-guard .main-svg {{
  width:100% !important; max-width:100% !important; overflow:hidden !important;
}}
.focus-guard .js-plotly-plot .draglayer {{ cursor: grab; }}
.focus-guard .js-plotly-plot .draglayer:active {{ cursor: grabbing; }}

/* 헤딩 앵커 숨김 + 유령 여백 제거 */
[data-testid="stHeading"] a,
[data-testid="stHeading"] svg,
[data-testid="stMarkdownContainer"] h1 a,
[data-testid="stMarkdownContainer"] h2 a,
[data-testid="stMarkdownContainer"] h3 a {{ display:none !important; visibility:hidden !important; pointer-events:none !important; }}
.block-container > div:empty {{ display:none !important; margin:0 !important; padding:0 !important; }}
[data-testid="stMarkdownContainer"] p {{ margin:0 !important; }}

/* ▼ 드롭다운(Selectbox) 겹침/잘림 수정 */
[data-testid="stSelectbox"] {{ position: relative; z-index: 20; }}
[data-testid="stSelectbox"] [role="listbox"],
[data-testid="stSelectbox"] [data-baseweb="menu"],
[data-testid="stSelectbox"] [data-baseweb="popover"] {{
  z-index: 9999 !important;
}}
.section-head, .focus-cage, .focus-card, .clip-shield {{
  position: relative; z-index: 1;
}}
</style>
""", unsafe_allow_html=True)


render_header()

# ================= 본문 =================
st.markdown('<div class="container">', unsafe_allow_html=True)
st.markdown('<div class="panel">', unsafe_allow_html=True)
# 주황색 큰 바는 숨김(폴더 페이지와 달리 panel-head 미출력)
st.markdown('<div class="panel-body">', unsafe_allow_html=True)

# ---------------- 데이터 (API) ----------------
today_date = datetime.today().date()
default_end = today_date
default_start = default_end - timedelta(days=30)

with st.expander("📅 기간 선택", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("시작일", value=default_start, key="start_date")
    with c2:
        end_date = st.date_input("종료일", value=default_end, key="end_date")
    if start_date > end_date:
        st.error("⚠️ 시작일은 종료일보다 빠르거나 같아야 합니다.")
        st.stop()

# 백엔드에서 기간 데이터 가져와서 DF 구성
daily = fetch_daily(start_date, end_date)
df = pd.DataFrame([{
    "날짜": datetime.fromisoformat(d["date"]),
    "날짜_date": datetime.fromisoformat(d["date"]).date(),
    "학습시간": int(d.get("study_minutes", 0)),
    "포인트": int(d.get("points", 0)),
    "출석": int(d.get("attendance", 0)),
} for d in daily.get("days", [])])

# charts에서 쓰는 이름 그대로 유지
filtered_df = df.copy()

# ---------- 요약 카드 ----------
total_days = len(filtered_df)
total_study_time = int(filtered_df["학습시간"].sum()) if total_days else 0
total_point = int(filtered_df["포인트"].sum()) if total_days else 0
total_attendance = int(filtered_df["출석"].sum()) if total_days else 0
rate = round((total_attendance/total_days)*100, 1) if total_days else 0
today_minutes = int(df.loc[df["날짜_date"] == today_date, "학습시간"].sum()) if total_days else 0

st.markdown(f"""
<div class="metrics">
  <div class="metric"><div class="label">총 학습일</div><div class="value">{total_days}일</div></div>
  <div class="metric"><div class="label">총 학습 시간</div><div class="value">{total_study_time}분</div></div>
  <div class="metric"><div class="label">오늘 학습 시간</div><div class="value">{today_minutes}분</div></div>
  <div class="metric"><div class="label">총 포인트</div><div class="value">{total_point}P</div></div>
  <div class="metric"><div class="label">총 출석일</div><div class="value">{total_attendance}일</div></div>
  <div class="metric"><div class="label">출석률</div><div class="value">{rate}%</div></div>
</div>
""", unsafe_allow_html=True)

# ---------- 섹션 헤더 ----------
st.markdown('<div class="section-head"><span>리포트 차트</span><span class="chev">▾</span></div>', unsafe_allow_html=True)

# ===== 리포트 차트 =====
c1_chart, c2_chart, c3_chart = st.columns(3, gap="small")
GAUGE_H = 220
DONUT_H = 220

def center_left(fig, height, right_bias=0.16, mid=0.80):
    left = 1.0 - (mid + right_bias)
    left = max(0.01, left)
    l, m, r = st.columns([left, mid, right_bias])
    fig.update_layout(height=height)
    with m:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# --- 1) 평균 차트 ---
with c1_chart:
    category = st.session_state.get("metric_select", "일 공부 시간 평균")

    with st.container(border=True):
        st.markdown("### 평균 차트")
        has_rows = len(filtered_df) > 0

        if category == "일 공부 시간 평균":
            avg_minutes = float(filtered_df["학습시간"].mean()) if has_rows else 0.0
            gauge_value = int(round(avg_minutes))
            max_range = 24 * 60
            unit = "분"
            h = gauge_value // 60; m = gauge_value % 60
            custom_label = f"{h}시간 {m}분"
        elif category == "일 포인트 평균":
            avg_points = float(filtered_df["포인트"].mean()) if has_rows else 0.0
            gauge_value = round(avg_points, 1)
            max_range = max(100, int(max(1.0, gauge_value * 2)))
            unit = "P"; custom_label = f"{gauge_value} P"
        else:
            gauge_value = 0 if not has_rows else random.randint(60, 100)
            max_range = 100; unit = "%"; custom_label = f"{gauge_value}%"

        val = max(0, min(gauge_value, max_range - 1e-6))
        gauge_fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=val,
            number={'suffix': f" {unit}", 'font': {'size': 20}},
            title={'text': "", 'font': {'size': 14}, 'align': 'center'},
            domain={'x': [0.00, 0.90], 'y': [0.00, 1.00]},
            gauge={
                'axis': {'range': [0, max_range], 'tickfont': {'size': 10}},
                'bar': {'color': "coral"},
                'bgcolor': "white",
                'bordercolor': "black",
                'borderwidth': 2,
                'steps': [
                    {'range': [0, max_range * 0.33], 'color': '#FFE0B2'},
                    {'range': [max_range * 0.33, max_range * 0.66], 'color': '#FFCC80'},
                    {'range': [max_range * 0.66, max_range], 'color': '#FFB74D'},
                ],
                'threshold': {'line': {'color': "red", 'width': 3}, 'thickness': 0.7, 'value': val}
            }
        ))
        gauge_fig.update_layout(margin=dict(l=0, r=0, t=6, b=6),
                                paper_bgcolor='rgba(0,0,0,0)')
        center_left(gauge_fig, GAUGE_H, right_bias=0.18, mid=0.80)

    options = ["일 공부 시간 평균", "일 포인트 평균", "집중도 평균"]
    st.selectbox(" ", options, key="metric_select",
                 index=options.index(category), label_visibility="collapsed")

# --- 2) 출석 차트 ---
with c2_chart:
    with st.container(border=True):
        st.markdown("### 출석 차트")
        days = len(filtered_df)
        present = int(filtered_df["출석"].sum())
        absent = max(0, days - present)
        present_rate = round((present / days) * 100, 1) if days else 0.0

        att_fig = go.Figure(data=[go.Pie(
            labels=["출석", "결석"],
            values=[present, absent] if days else [1, 1],
            hole=.58,
            textinfo='percent+label',
            insidetextorientation='radial',
            sort=False
        )])
        att_fig.update_traces(marker=dict(
            colors=['#FFCC80', '#FFE0B2'],
            line=dict(color='black', width=1.5)
        ))
        att_fig.update_layout(
            margin=dict(l=10, r=10, t=6, b=40),
            showlegend=False, paper_bgcolor='rgba(0,0,0,0)',
            annotations=[]
        )
        center_left(att_fig, DONUT_H, right_bias=0.26, mid=0.78)

# --- 3) 포인트 획득 차트 ---
with c3_chart:
    with st.container(border=True):
        st.markdown("### 포인트 획득 차트")

        by_reason = daily.get("points_by_reason", {}) or {}
        top = sorted(by_reason.items(), key=lambda x: x[1], reverse=True)[:3]
        labels = [k for k, _ in top] or ["QUIZ", "ATTENDANCE", "ETC"]
        vals = [int(v) for _, v in top] or [0, 0, 0]
        total_pts = sum(vals)
        if sum(vals) == 0:
            vals = [1, 1, 1]
        points_data = dict(zip(labels, vals))

        pts_fig = go.Figure(data=[go.Pie(
            labels=list(points_data.keys()),
            values=vals,
            hole=.58,
            textinfo='percent+label',
            textposition='outside',
            insidetextorientation='radial',
            sort=False
        )])
        pts_fig.update_traces(marker=dict(
            colors=['#FFE0B2', '#FFCC80', '#FFB74D'],
            line=dict(color='black', width=1.5)
        ))
        pts_fig.update_layout(
            margin=dict(l=10, r=10, t=6, b=48),
            showlegend=False, paper_bgcolor='rgba(0,0,0,0)',
            annotations=[dict(text=f"{total_pts}P", x=0.5, y=0.5,
                              font=dict(size=18), showarrow=False)]
        )
        center_left(pts_fig, DONUT_H, right_bias=0.26, mid=0.78)

# ======================= 하루 집중도 (오픈월드식 박스 + 팬 모드) =======================
st.markdown("""
<style>
/* 하루 집중도 섹션 전체 폭을 캡(Clamp) */
.focus-wrap{
  width: min(100%, 980px);
  margin: 8px 0 0;
}
.focus-wrap [data-testid="stVerticalBlockBorderWrapper"]{
  max-width: 100% !important;
  margin: 0 !important;
}
.focus-guard{
  overflow:hidden;
  border-radius:12px;
  overscroll-behavior:contain;
  touch-action:pan-x;
}
/* Plotly가 부모 폭을 넘지 않도록 강제 */
.focus-guard [data-testid="stPlotlyChart"],
.focus-guard .js-plotly-plot,
.focus-guard .plot-container,
.focus-guard .svg-container,
.focus-guard .main-svg{
  width:100% !important;
  max-width:100% !important;
  overflow:hidden !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-head"><span>하루 집중도</span><span class="chev">▾</span></div>', unsafe_allow_html=True)

# ▶ 케이지 + 카드 + 클리핑 레이어
st.markdown('<div class="focus-cage"><div class="focus-card"><div class="clip-shield">', unsafe_allow_html=True)

# ─ 백엔드에서 하루 집중도 이벤트 조회
focus_day = st.session_state.get("focus_day", min(end_date, today_date))
base_events = fetch_focus(focus_day)

SESS_LEN = 25
sessions = []
for ev in base_events:
    try:
        s = datetime.combine(focus_day, datetime.strptime(ev["time"], "%H:%M").time())
    except Exception:
        continue
    e = s + timedelta(minutes=SESS_LEN)
    sessions.append({"start": s, "end": e, "length": SESS_LEN,
                     "blinks": int(ev.get("blinks",0)), "yawns": int(ev.get("yawns",0))})
sessions.sort(key=lambda x: x["start"])

# 2시간 단위 집계
day0 = datetime.combine(focus_day, time(0,0))
bar_x = [day0 + timedelta(hours=h) for h in range(0, 24, 2)]

BAR_WIDTH_RATIO = 0.40
width_ms = int(2*60*60*1000*BAR_WIDTH_RATIO)

scores, hover = [], []
for h in range(0, 24, 2):
    h0 = day0 + timedelta(hours=h)
    h1 = h0 + timedelta(hours=2)
    studied_min = 0.0; blink_part = 0.0; yawn_part  = 0.0
    for ses in sessions:
        s, e, L = ses["start"], ses["end"], float(ses["length"])
        inter = max(0.0, (min(e, h1) - max(s, h0)).total_seconds()/60.0)
        if inter <= 0: continue
        studied_min += inter
        blink_part += ses["blinks"] * (inter / L)
        yawn_part  += ses["yawns"]  * (inter / L)
    b = int(round(blink_part)); y = int(round(yawn_part))
    score = 0 if studied_min <= 0 else max(0, min(100, 100 - 5*b - 2*y))
    scores.append(score)
    hover.append([h0.strftime('%H:%M'), h1.strftime('%H:%M'),
                  int(round(studied_min)), b, y, b*5, y*2])

tickvals = [day0 + timedelta(hours=h) for h in range(25)]
ticktext = [f"{h:02d}:00" for h in range(25)]

if dark:
    bar_color = "#FFA149"; grid_col = "rgba(255,147,48,0.18)"; grid_col_y = "rgba(255,255,255,0.10)"
else:
    bar_color = "#FF9330"; grid_col = "rgba(0,0,0,0.08)"; grid_col_y = "rgba(0,0,0,0.06)"

# 라벨
text_fg = [f"{int(val)}%" if val > 0 else "" for val in scores]

# 보기 구간
VIEW_HOURS = 24
x0 = day0 + timedelta(hours=max(0.0, min(24.0 - VIEW_HOURS, 8 - VIEW_HOURS/2)))
x1 = x0 + timedelta(hours=VIEW_HOURS)

fig = go.Figure(go.Bar(
    x=bar_x, y=scores, width=width_ms,
    marker=dict(color=bar_color),
    text=text_fg, textposition="inside", insidetextanchor="middle",
    customdata=hover, cliponaxis=True,
    hovertemplate=("시간대 %{customdata[0]}–%{customdata[1]}<br>"
                   "평균 집중도 %{y:.0f}%<br>"
                   "학습 %{customdata[2]}분<br>"
                   "졸음(깜빡임) %{customdata[3]}회 (−%{customdata[5]}점)<br>"
                   "하품 %{customdata[4]}회 (−%{customdata[6]}점)<extra></extra>")
))

fig.update_layout(
    height=280,
    margin=dict(l=10, r=10, t=6, b=44),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    showlegend=False, bargap=0.42,
    dragmode="pan",
    uirevision="focus_pan_keep",
)

fig.update_xaxes(
    type="date",
    range=[x0, x1],
    fixedrange=False,
    tickmode="array", tickvals=tickvals, ticktext=ticktext,
    ticks="outside", ticklen=3, tickfont=dict(size=11),
    showgrid=True, gridcolor=grid_col, gridwidth=1,
    automargin=True, constrain="domain"
)
fig.update_yaxes(
    title=None, range=[0,100], fixedrange=True,
    tickmode="array", tickvals=[0,25,50,75,100],
    tickfont=dict(size=11),
    showgrid=True, gridcolor=grid_col_y, gridwidth=1,
    zeroline=False
)

st.plotly_chart(fig, use_container_width=True,
                config={"displayModeBar": False, "scrollZoom": False, "doubleClick":"reset"})

st.markdown('</div></div></div>', unsafe_allow_html=True)
