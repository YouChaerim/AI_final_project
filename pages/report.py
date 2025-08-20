# pages/report.py
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta, time
import random
import os, json, base64

# ================= 기본 설정 =================
st.set_page_config(page_title="📊 학습 리포트 대시보드", layout="wide", initial_sidebar_state="collapsed")

# ---- user_data 불러오기 (다크모드/아바타) ----
if "user_data" not in st.session_state:
    if os.path.exists("user_data.json"):
        with open("user_data.json", "r", encoding="utf-8") as f:
            st.session_state.user_data = json.load(f)
    else:
        st.session_state.user_data = {"dark_mode": False}

ud = st.session_state.user_data
ud.setdefault("dark_mode", False)
ud.setdefault("active_char", "rabbit")
ud.setdefault("owned_hats", [])
ud.setdefault("equipped_hat", None)
dark = ud.get("dark_mode", False)

# ---- 컬러 ----
if dark:
    bg = "#1C1C1E"; fg = "#F2F2F2"; nav_bg = "#2C2C2E"
    panel_bg = "#1F1F22"; panel_shadow = "rgba(0,0,0,.35)"
    nav_link = "#F2F2F2"; card_border = "rgba(255,255,255,.08)"; text_muted = "#C7C7CC"
else:
    bg = "#F5F5F7"; fg = "#2B2B2E"; nav_bg = "rgba(255,255,255,.9)"
    panel_bg = "#FFFFFF"; panel_shadow = "rgba(0,0,0,.08)"
    nav_link = "#000000"; card_border = "rgba(0,0,0,.06)"; text_muted = "#6B7280"

# ---- 아바타 ----
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
    char_key = ud.get("active_char", "rabbit")
    hat_id = ud.get("equipped_hat")
    if hat_id and (hat_id in ud.get("owned_hats", [])):
        return get_char_image_uri(char_key, hat_id)
    return get_char_image_uri(char_key)

header_avatar_uri = current_avatar_uri()

# ================= CSS =================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;800;900&display=swap');

html, body, .stApp {{
  background:{bg};
  color:{fg};
  font-family:'Noto Sans KR', sans-serif;
  zoom:1.10; margin:0;
  overflow-x:hidden;
}}
.block-container {{ padding-top:0 !important; }}
header, [data-testid="stToolbar"], #MainMenu, [data-testid="stSidebar"] {{ display:none !important; }}

/* 본문 컨테이너 */
.container {{ max-width:1200px; margin:auto; padding:4px 40px 24px; }}

/* 공통 헤더 */
a {{ text-decoration:none !important; }}
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
.profile-group {{ display:flex; gap:16px; align-items:center; margin-right:12px; }}
.profile-icon {{ width:36px; height:36px; border-radius:50%; overflow:hidden; }}

/* 패널 */
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
.panel-body {{ padding:8px 36px 20px; }}

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

/* 하얀 카드 */
[data-testid="stVerticalBlockBorderWrapper"]{{
  background:#FFFFFF; border:1px solid rgba(0,0,0,.06);
  border-radius:14px; box-shadow:0 4px 12px rgba(0,0,0,.06);
  padding:10px 12px;
}}

/* 🔒 하루집중도: 차트가 박스 밖으로 절대 못 나가게 강제 클리핑 */
.focus-guard {{
  border-radius:12px;
  overflow:hidden;          /* 핵심: 밖으로 나가는 모든 요소를 자름 */
  padding:0;                /* 내부 여백 0, 대신 Plotly 마진으로 조절 */
}}
.focus-guard [data-testid="stPlotlyChart"],
.focus-guard [data-testid="stPlotlyChart"]>div,
.focus-guard .plotly, .focus-guard .js-plotly-plot, .focus-guard .main-svg {{
  width:100% !important; max-width:100% !important; overflow:hidden !important;
}}

/* 헤딩 앵커 숨김 */
[data-testid="stHeading"] a,
[data-testid="stHeading"] svg,
[data-testid="stMarkdownContainer"] h1 a,
[data-testid="stMarkdownContainer"] h2 a,
[data-testid="stMarkdownContainer"] h3 a {{ display:none !important; visibility:hidden !important; pointer-events:none !important; }}
</style>
""", unsafe_allow_html=True)

# ================= 공통 헤더 =================
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

# ================= 본문 =================
st.markdown('<div class="container">', unsafe_allow_html=True)
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-head">리포트</div>', unsafe_allow_html=True)
st.markdown('<div class="panel-body">', unsafe_allow_html=True)

# ---------------- 데이터 (예시) ----------------
date_range = pd.date_range(start="2025-01-01", end="2025-12-31", freq="D")
df = pd.DataFrame({
    "날짜": date_range,
    "학습시간": (pd.Series(range(len(date_range))) % 5 + 1) * 10,   # 분
    "포인트": (pd.Series(range(len(date_range))) % 4 + 1) * 15,
    "출석": [1 if i % 2 == 0 else 0 for i in range(len(date_range))],
})
df["날짜_date"] = df["날짜"].dt.date

today_date = datetime.today().date()
data_start = df["날짜_date"].min()
data_end = df["날짜_date"].max()
default_end = min(today_date, data_end)
default_start = max(data_start, default_end - timedelta(days=30))

with st.expander("📅 기간 선택", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        start_date = st.date_input("시작일", value=default_start, min_value=data_start, max_value=data_end, key="start_date")
    with c2:
        end_date = st.date_input("종료일", value=default_end, min_value=data_start, max_value=data_end, key="end_date")
    if start_date > end_date:
        st.error("⚠️ 시작일은 종료일보다 빠르거나 같아야 합니다.")
        st.stop()

mask = (df["날짜_date"] >= start_date) & (df["날짜_date"] <= end_date)
filtered_df = df.loc[mask].reset_index(drop=True)

# ---------- 요약 카드 ----------
total_days = len(filtered_df)
total_study_time = int(filtered_df["학습시간"].sum())        # 분
total_point = int(filtered_df["포인트"].sum())
total_attendance = int(filtered_df["출석"].sum())
rate = round((total_attendance/total_days)*100, 1) if total_days else 0
today_minutes = int(df.loc[df["날짜_date"] == today_date, "학습시간"].sum())

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

        if category == "일 공부 시간 평균":
            avg_minutes = float(filtered_df["학습시간"].mean() or 0.0)
            gauge_value = int(round(avg_minutes))
            max_range = 24 * 60
            unit = "분"
            h = gauge_value // 60; m = gauge_value % 60
            custom_label = f"{h}시간 {m}분"
        elif category == "일 포인트 평균":
            avg_points = float(filtered_df["포인트"].mean() or 0.0)
            gauge_value = round(avg_points, 1)
            max_range = max(100, int(max(1.0, gauge_value * 2)))
            unit = "P"; custom_label = f"{gauge_value} P"
        else:
            gauge_value = random.randint(60, 100)
            max_range = 100; unit = "%"; custom_label = f"{gauge_value}%"

        val = max(0, min(gauge_value, max_range - 1e-6))
        gauge_fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=val,
            number={'suffix': f" {unit}", 'font': {'size': 20}},
            title={'text': custom_label, 'font': {'size': 14}, 'align': 'center'},
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
            annotations=[dict(text=f"{present_rate:.1f}% 출석", x=0.5, y=0.5,
                              font=dict(size=18), showarrow=False)]
        )
        center_left(att_fig, DONUT_H, right_bias=0.26, mid=0.78)

# --- 3) 포인트 획득 차트 ---
with c3_chart:
    with st.container(border=True):
        st.markdown("### 포인트 획득 차트")

        total_pts = int(filtered_df["포인트"].sum())
        weights = {"퀴즈": 0.40, "출석": 0.35, "집중도": 0.25}
        points_data = {k: round(total_pts * w) for k, w in weights.items()} if total_pts > 0 else {k: 0 for k in weights}
        vals = list(points_data.values())
        if sum(vals) == 0:
            vals = [1, 1, 1]

        pts_fig = go.Figure(data=[go.Pie(
            labels=list(points_data.keys()),
            values=vals,
            hole=.58,
            textinfo='percent+label',
            textposition='outside',  # ✅ 라벨을 바깥에 표시
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


# ======================= 하루 집중도 (클리핑 + 중앙 정렬 + 00~24 표기) =======================
st.markdown('<div class="section-head"><span>하루 집중도</span><span class="chev">▾</span></div>', unsafe_allow_html=True)

with st.container(border=True):
    # 차트를 박스 내부에 강제 클리핑
    st.markdown('<div class="focus-guard">', unsafe_allow_html=True)

    focus_day = st.session_state.get("focus_day", default_end)

    # 데모 세션
    if "focus_events" in st.session_state:
        base_events = st.session_state["focus_events"]
    else:
        rnd = random.Random(13)
        base_events = [
            {"time":"09:00","blinks":2,"yawns":1},
            {"time":"09:30","blinks":3,"yawns":0},
            {"time":"10:00","blinks":4,"yawns":2},
        ]
        for ev in base_events:
            ev["blinks"] = max(0, ev["blinks"] + rnd.randint(-1,1))
            ev["yawns"]  = max(0, ev["yawns"]  + rnd.randint(-1,1))

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
    bin_starts = [day0 + timedelta(hours=h) for h in range(0, 24, 2)]
    bar_x = bin_starts

    BAR_WIDTH_RATIO = 0.40
    width_ms = int(2*60*60*1000*BAR_WIDTH_RATIO)

    scores, hover = [], []
    for h in range(0, 24, 2):
        h0 = day0 + timedelta(hours=h)
        h1 = h0 + timedelta(hours=2)
        studied_min = 0.0; blink_part = 0.0; yawn_part = 0.0
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

    # 00:00~24:00 강제 표기 + 경계선 라벨 여유
    tickvals = [day0 + timedelta(hours=h) for h in range(25)]
    ticktext = [f"{h:02d}:00" for h in range(25)]

    if dark:
        bar_color = "#FFA149"; grid_col = "rgba(255,147,48,0.18)"; hover_bd = "#FFCC80"; grid_col_y = "rgba(255,255,255,0.10)"
    else:
        bar_color = "#FF9330"; grid_col = "rgba(0,0,0,0.08)"; hover_bd = "#FF9330"; grid_col_y = "rgba(0,0,0,0.06)"

    text_fg = [f"{int(v)}%" if v > 0 else "" for v in scores]

    fig = go.Figure(go.Bar(
        x=bar_x, y=scores, width=width_ms,
        marker=dict(color=bar_color),
        text=text_fg, textposition="inside", insidetextanchor="middle",
        customdata=hover, cliponaxis=True,
        hovertemplate=("시간대 %{customdata[0]}–%{customdata[1]}<br>"
                       "평균 집중도 %{y:.0f}%<br>"
                       "학습 %{customdata[2]}분<br>"
                       "졸음(깜빡임) %{customdata[3]}회 (−%{customdata[5]}점)<br>"
                       "하품 %{customdata[4]}회 (−%{customdata[6]}점)"
                       "<extra></extra>")
    ))

    # ⚙️ 레이아웃: 오른쪽/왼쪽 경계선 100% 내부에 머물도록 마진 + 범위 여유
    fig.update_layout(
        height=280,
        margin=dict(l=10, r=14, t=6, b=44),  # r 살짝 확보 → 라벨/그리드가 경계선과 접촉 방지
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        bargap=0.42,
        dragmode=False,
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=hover_bd,
                        font_size=12, align="left", namelength=-1)
    )
    fig.update_xaxes(
        type="date",
        range=[day0 - timedelta(minutes=8), day0 + timedelta(hours=24, minutes=8)],
        tickmode="array", tickvals=tickvals, ticktext=ticktext,
        ticks="outside", ticklen=3, tickfont=dict(size=11),
        showgrid=True, gridcolor=grid_col, gridwidth=1,
        fixedrange=True, automargin=True, constrain="domain"
    )
    fig.update_yaxes(
        title=None,
        range=[0, 100], fixedrange=True,
        tickmode="array", tickvals=[0, 25, 50, 75, 100],
        tickfont=dict(size=11),
        showgrid=True, gridcolor=grid_col_y, gridwidth=1,
        zeroline=False
    )

    st.plotly_chart(fig, use_container_width=True,
                    config={"displayModeBar": False, "scrollZoom": False})

    st.markdown('</div>', unsafe_allow_html=True)

# 종료
st.markdown("</div>", unsafe_allow_html=True)  # /panel-body
st.markdown("</div>", unsafe_allow_html=True)  # /panel
st.markdown("</div>", unsafe_allow_html=True)  # /container
