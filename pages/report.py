# pages/report.py
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
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

/* 기간선택 여백 */
.panel-body [data-testid="stExpander"] {{ margin-top:0 !important; }}
.panel-body [data-testid="stExpander"] details summary {{ padding-top:6px !important; padding-bottom:6px !important; }}

/* 요약카드 */
.metrics {{
  display:grid; grid-template-columns:repeat(3,1fr);
  gap:10px; margin-top:6px;
}}
.metric {{
  background:{panel_bg}; border-radius:12px; padding:14px;
  box-shadow:0 4px 12px {card_border}; border:1px solid {card_border};
}}
.metric .label {{ font-size:13px; font-weight:900; color:{text_muted}; letter-spacing:.02em; margin-bottom:2px; }}
.metric .value {{ font-size:28px; font-weight:900; line-height:1.1; margin-top:2px; }}

/* 섹션 헤더 */
.section-head {{
  display:flex; align-items:center; gap:8px;
  background:{panel_bg}; border:1px solid {card_border};
  border-radius:14px; padding:12px 14px; margin:10px 0 8px;
  box-shadow:0 4px 12px {card_border}; font-weight:900;
}}
.section-head .chev {{ margin-left:auto; opacity:.5; }}

/* 하얀 카드 */
[data-testid="stVerticalBlockBorderWrapper"]{{
  background:#FFFFFF; border:1px solid rgba(0,0,0,.06);
  border-radius:14px; box-shadow:0 4px 12px rgba(0,0,0,.06);
  padding:10px 12px;
}}
/* 라벨 잘림 방지: visible */
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stPlotlyChart"] div{{ overflow: visible !important; }}

/* 드롭다운을 '가능하면 위로' 띄우기 */
div[data-testid="stSelectbox"] div[data-baseweb="select"] div[role="listbox"] {{
  top: auto !important;
  bottom: 100% !important;
  margin-bottom: 8px !important;
}}
</style>
""", unsafe_allow_html=True)

# ================= 공통 헤더 =================
st.markdown(f"""
<div class="top-nav">
  <div class="nav-left">
    <div><a href="/" target="_self">🐾 딸깍공</a></div>
    <div class="nav-menu">
      <div><a href="/"            target="_self">메인페이지</a></div>
      <div><a href="/main"        target="_self">공부 시작</a></div>
      <div><a href="/ocr_paddle"  target="_self">PDF 요약</a></div>
      <div><a href="/folder_page" target="_self">저장폴더</a></div>
      <div><a href="/quiz"        target="_self">퀴즈</a></div>
      <div><a href="/report"      target="_self">리포트</a></div>
      <div><a href="/ranking"     target="_self">랭킹</a></div>
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

# 오늘 학습 시간(분)
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

# 중앙 정렬(약간 왼쪽 보정) 도우미 — 안전 클램프 적용
def center_left(fig, height, right_bias=0.16, mid=0.80):
    """
    카드 안에서 차트를 시각적 중앙으로 보이게 하는 헬퍼.
    right_bias: 오른쪽 여백 비율(높을수록 차트가 왼쪽으로 이동)
    mid: 차트를 넣는 중앙 영역 비율
    """
    left = 1.0 - (mid + right_bias)
    left = max(0.01, left)  # <-- 음수/제로 방지
    l, m, r = st.columns([left, mid, right_bias])
    fig.update_layout(height=height)
    with m:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# --- 1) 평균 차트(게이지, 주황계열 유지) ---
with c1_chart:
    category = st.session_state.get("metric_select", "일 공부 시간 평균")

    with st.container(border=True):
        st.markdown("### 평균 차트")

        if category == "일 공부 시간 평균":
            avg_minutes = float(filtered_df["학습시간"].mean() or 0.0)
            gauge_value = int(round(avg_minutes))  # 중앙 숫자: 분
            max_range = 24 * 60                   # 축: 0~1440분
            unit = "분"
            h = gauge_value // 60; m = gauge_value % 60
            custom_label = f"{h}시간 {m}분"

        elif category == "일 포인트 평균":
            avg_points = float(filtered_df["포인트"].mean() or 0.0)
            gauge_value = round(avg_points, 1)
            max_range = max(100, int(max(1.0, gauge_value * 2)))
            unit = "P"; custom_label = f"{gauge_value} P"

        else:  # 집중도 평균(예시)
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
                'bar': {'color': "coral"},  # 주황 바
                'bgcolor': "white",
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

# --- 2) 출석 차트 (기간 내 출석률/결석률) ---
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
        att_fig.update_traces(marker=dict(colors=['#A0E7CF', '#FFCDD2']))  # 녹색/핑크
        att_fig.update_layout(
            margin=dict(l=10, r=10, t=6, b=40),  # 하단 여백 확보
            showlegend=False, paper_bgcolor='rgba(0,0,0,0)',
            annotations=[dict(text=f"{present_rate:.1f}% 출석", x=0.5, y=0.5,
                              font=dict(size=18), showarrow=False)]
        )
        # 중앙 보정(왼쪽으로 더)
        center_left(att_fig, DONUT_H, right_bias=0.26, mid=0.78)

# --- 3) 포인트 획득 차트 (출석/집중도/퀴즈) ---
with c3_chart:
    with st.container(border=True):
        st.markdown("### 포인트 획득 차트")

        total_pts = int(filtered_df["포인트"].sum())
        # 실제 경로별 포인트 컬럼이 있다면 그 합계를 사용하세요.
        weights = {"퀴즈": 0.40, "출석": 0.35, "집중도": 0.25}
        points_data = {k: round(total_pts * w) for k, w in weights.items()} if total_pts > 0 else {k: 0 for k in weights}
        vals = list(points_data.values()); 
        if sum(vals) == 0: vals = [1, 1, 1]  # 파이 안전값

        pts_fig = go.Figure(data=[go.Pie(
            labels=list(points_data.keys()),
            values=vals,
            hole=.58,
            textinfo='percent+label',
            insidetextorientation='radial',
            sort=False
        )])
        pts_fig.update_traces(marker=dict(colors=['#6BCBFF', '#A0E7CF', '#7FB3FF']))  # 파랑/녹색 톤
        pts_fig.update_layout(
            margin=dict(l=10, r=10, t=6, b=48),  # 하단 여백 더 확보
            showlegend=False, paper_bgcolor='rgba(0,0,0,0)',
            annotations=[dict(text=f"{total_pts}P", x=0.5, y=0.5,
                              font=dict(size=18), showarrow=False)]
        )
        # 중앙 보정(왼쪽으로 더)
        center_left(pts_fig, DONUT_H, right_bias=0.26, mid=0.78)

# 종료
st.markdown("</div>", unsafe_allow_html=True)  # /panel-body
st.markdown("</div>", unsafe_allow_html=True)  # /panel
st.markdown("</div>", unsafe_allow_html=True)  # /container
