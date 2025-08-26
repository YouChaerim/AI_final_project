# pages/report.py
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta, time
import random
import os, base64, requests
from components.header import render_header
from components.auth import require_login

print(f"✅✅✅ Executing: {__file__} ✅✅✅")
BACKEND_URL = "http://127.0.0.1:8080"
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

# ---- API helpers ----
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

def fetch_summary():
    url = f"{BACKEND_URL}/reports/summary/{USER_KEY}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()

def fetch_focus_hist(start_d, end_d):
    url = f"{BACKEND_URL}/reports/focus_hist/{USER_KEY}"
    r = requests.get(url, params={"start": start_d.isoformat(), "end": end_d.isoformat()}, timeout=15)
    r.raise_for_status()
    return r.json()

# ================= CSS =================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;800;900&display=swap');

html, body {{ background:{bg}; color:{fg}; font-family:'Noto Sans KR', sans-serif; zoom:1.10; margin:0; }}
.stApp {{ background:{bg}; }}

a, a:hover, a:focus, a:visited {{ text-decoration:none !important; }}
.top-nav + * {{ margin-top:0 !important; padding-top:0 !important; }}
.top-nav + [data-testid="stVerticalBlock"],
.top-nav + div [data-testid="stVerticalBlock"] {{ margin-top:0 !important; padding-top:0 !important; }}

.panel {{ position: relative; background:{panel_bg}; border-radius:18px; box-shadow:0 6px 24px {panel_shadow}; overflow:visible !important; margin-top:0 !important; }}
.panel-head {{ background: linear-gradient(90deg,#FF9330,#FF7A00); color:white; text-align:center; font-size:34px; font-weight:900; padding:18px 20px; }}
.panel-body {{ padding:0 36px 20px !important; }}

.metrics {{ display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-top:6px; }}
.metric {{ background:{panel_bg}; border-radius:12px; padding:14px; box-shadow:0 4px 12px rgba(0,0,0,.06); border:1px solid rgba(0,0,0,.06); }}
.metric .label {{ font-size:13px; font-weight:900; color:#6B7280; letter-spacing:.02em; margin-bottom:2px; }}
.metric .value {{ font-size:28px; font-weight:900; line-height:1.1; }}

.section-head {{ display:flex; align-items:center; gap:8px; background:{panel_bg}; border:1px solid rgba(0,0,0,.06); border-radius:14px; padding:12px 14px; margin:10px 0 8px; box-shadow:0 4px 12px rgba(0,0,0,.06); font-weight:900; }}
.section-head .chev {{ margin-left:auto; opacity:.5; }}

[data-testid="stVerticalBlockBorderWrapper"]{{ background:#FFFFFF; border:1px solid rgba(0,0,0,.06); border-radius:14px; box-shadow:0 4px 12px rgba(0,0,0,.06); padding:10px 12px; }}

.focus-guard{{ border-radius:12px; overflow:hidden; padding:0; overscroll-behavior:contain; touch-action:pan-x; position:relative; }}
.focus-guard [data-testid="stPlotlyChart"],
.focus-guard .js-plotly-plot, .focus-guard .plot-container, .focus-guard .svg-container, .focus-guard .main-svg{{ width:100% !important; max-width:100% !important; overflow:hidden !important; }}

[data-testid="stHeading"] a, [data-testid="stHeading"] svg, [data-testid="stMarkdownContainer"] h1 a, [data-testid="stMarkdownContainer"] h2 a, [data-testid="stMarkdownContainer"] h3 a {{ display:none !important; visibility:hidden !important; pointer-events:none !important; }}
.block-container > div:empty {{ display:none !important; margin:0 !important; padding:0 !important; }}
[data-testid="stMarkdownContainer"] p {{ margin:0 !important; }}

[data-testid="stSelectbox"] {{ position: relative; z-index: 20; }}
[data-testid="stSelectbox"] [role="listbox"],
[data-testid="stSelectbox"] [data-baseweb="menu"],
[data-testid="stSelectbox"] [data-baseweb="popover"] {{ z-index: 9999 !important; }}
.section-head, .focus-cage, .focus-card, .clip-shield {{ position: relative; z-index: 1; }}
</style>
""", unsafe_allow_html=True)

render_header()

# ================= 본문 =================
st.markdown('<div class="container">', unsafe_allow_html=True)
st.markdown('<div class="panel">', unsafe_allow_html=True)
st.markdown('<div class="panel-body">', unsafe_allow_html=True)

# --- helper: 빈 days여도 안전한 DF ---
def make_df(days):
    cols = ["날짜", "날짜_date", "학습시간", "포인트", "출석"]
    if not days:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame([{
        "날짜": datetime.fromisoformat(d["date"]),
        "날짜_date": datetime.fromisoformat(d["date"]).date(),
        "학습시간": int(d.get("study_minutes", 0)),
        "포인트": int(d.get("points", 0)),
        "출석": int(d.get("attendance", 0)),
    } for d in days])

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

# (1) 선택 기간 데이터
daily = fetch_daily(start_date, end_date)
df = make_df(daily.get("days", []))
filtered_df = df.copy()

# (2) 요약/전체기간 데이터
summary = fetch_summary()
overall_learning_days = int(summary.get("total_learning_days", 0))
streak_days = int(summary.get("streak_days", 0))
overall_points = int(summary.get("total_points", 0))

global_start = datetime.fromisoformat(summary["created_at"]).date()
global_end   = datetime.today().date()
daily_all = fetch_daily(global_start, global_end)
df_all = make_df(daily_all.get("days", []))

# 기간 요약(선택구간 기준)
total_days = len(filtered_df)
total_study_time = int(filtered_df["학습시간"].sum()) if total_days else 0
today_minutes = int(df.loc[df["날짜_date"] == today_date, "학습시간"].sum()) if total_days else 0
present_days = int(filtered_df["출석"].sum()) if total_days else 0
rate = round((present_days/total_days)*100, 1) if total_days else 0.0

st.markdown(f"""
<div class="metrics">
  <div class="metric"><div class="label">총 학습일</div><div class="value">{overall_learning_days}일</div></div>
  <div class="metric"><div class="label">총 학습 시간</div><div class="value">{total_study_time}분</div></div>
  <div class="metric"><div class="label">오늘 학습 시간</div><div class="value">{today_minutes}분</div></div>
  <div class="metric"><div class="label">총 포인트</div><div class="value">{overall_points}P</div></div>
  <div class="metric"><div class="label">연속 출석일</div><div class="value">{streak_days}일</div></div>
  <div class="metric"><div class="label">출석률</div><div class="value">{rate}%</div></div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

# ===== 리포트 차트 =====
c1_chart, c2_chart, c3_chart = st.columns(3, gap="small")
GAUGE_H = 200
DONUT_H = 300

def center_left(fig, height, right_bias=0.16, mid=0.80):
    left = 1.0 - (mid + right_bias)
    left = max(0.01, left)
    l, m, r = st.columns([left, mid, right_bias])
    fig.update_layout(height=height)
    with m:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# --- 1) 평균 차트(선택기간 기준) ---
with c1_chart:
    category = st.session_state.get("metric_select", "일 공부 시간 평균")
    with st.container(border=True):
        st.markdown("### 평균 차트")
        has_rows = len(filtered_df) > 0

        max_range = 100
        unit = ""
        caption_text = None

        if category == "일 공부 시간 평균":
            avg_minutes = float(filtered_df["학습시간"].mean()) if has_rows else 0.0
            max_day_minutes = int(filtered_df["학습시간"].max()) if has_rows else 0
            gauge_value = int(round(avg_minutes))
            max_range = 24 * 60
            unit = "분"
            caption_text = f"게이지 최대치: 1440분"
        elif category == "일 포인트 평균":
            avg_points = float(filtered_df["포인트"].mean()) if has_rows else 0.0
            gauge_value = round(avg_points, 1)
            max_range = max(100, int(max(1.0, gauge_value * 2)))
            unit = "P"
        else:  # 집중도 평균(임시)
            gauge_value = 0 if not has_rows else random.randint(60, 100)
            max_range = 100
            unit = "%"

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
        gauge_fig.update_layout(margin=dict(l=0, r=0, t=6, b=6), paper_bgcolor='rgba(0,0,0,0)')
        center_left(gauge_fig, GAUGE_H, right_bias=0.18, mid=0.80)
        if caption_text:
            st.caption(caption_text)

    options = ["일 공부 시간 평균", "일 포인트 평균", "집중도 평균"]
    st.selectbox(" ", options, key="metric_select",
                 index=options.index(category), label_visibility="collapsed")

# --- 2) 출석 차트(전체기간) ---
with c2_chart:
    with st.container(border=True):
        st.markdown("### 출석 차트")
        days_all = len(df_all)
        present_all = int(df_all["출석"].sum()) if days_all else 0
        absent_all = max(0, days_all - present_all)

        att_fig = go.Figure(data=[go.Pie(
            labels=["출석", "결석"],
            values=[present_all, absent_all] if days_all else [1, 1],
            hole=.58, textinfo='percent+label', insidetextorientation='radial',
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

# --- 3) 포인트 획득 차트(전체기간) ---
with c3_chart:
    with st.container(border=True):
        st.markdown("### 포인트 획득 차트")

        raw = daily_all.get("points_by_reason", {}) or {}

        # ✅ QUIZ 최우선 매핑, 잡음(reason) 제거, 배팅은 보상만(BET_START 등 차감 제외)
        def to_cat(reason: str):
            if not reason:
                return None
            s = str(reason).strip().upper()
            s_norm = s.replace("_", "").replace("-", "")

            # 잡음/결측 reason 무시(예: 'nonedl', 'unknown', 'null' 등)
            noisy = ("NONE", "UNKNOWN", "NULL", "N/A", "NONEDL", "NOREASON", "NOREASONDL", "NA")
            if any(tok in s_norm for tok in noisy):
                return None

            if "QUIZ" in s:                             # ← 퀴즈 관련이면 무조건 '퀴즈'
                return "QUIZ"
            if "ATTEND" in s or "CHECK" in s:
                return "ATTEND"
            if "FOCUS" in s or "CONCENTR" in s:
                return "FOCUS"
            if "BET" in s and "START" not in s and "CANCEL" not in s and "REFUND" not in s:
                return "BET"                           # 보상류만 포함
            return None

        agg = {"QUIZ": 0, "ATTEND": 0, "FOCUS": 0, "BET": 0}
        for k, v in raw.items():
            cat = to_cat(k)
            if cat:
                agg[cat] += int(v or 0)

        order = ["QUIZ", "ATTEND", "FOCUS", "BET"]
        labels_kr = {"QUIZ": "퀴즈", "ATTEND": "출석", "FOCUS": "집중도", "BET": "배팅"}

        values_raw = [agg[o] for o in order]
        pos_total = sum(values_raw)            # 양수만 합산(시각화 비율용)
        net_total = overall_points             # ✅ 순합계(=총 보유 포인트)
        diff = net_total - pos_total           # 참고용(음수/기타 포함 차이)

        plot_vals = values_raw if pos_total > 0 else [1, 1, 1, 1]

        pts_fig = go.Figure(data=[go.Pie(
            labels=[labels_kr[o] for o in order],
            values=plot_vals,
            hole=.58,
            textinfo='percent+label',
            textposition='outside',
            insidetextorientation='radial',
            sort=False
        )])

        pts_fig.update_traces(marker=dict(
            colors=['#FFB74D', '#FFCC80', '#FFE0B2', '#FFD180'],  # 퀴즈/출석/집중도/배팅
            line=dict(color='black', width=1.5)
        ))
        pts_fig.update_layout(
            margin=dict(l=10, r=10, t=6, b=48),
            showlegend=False, paper_bgcolor='rgba(0,0,0,0)',
            # ✅ 도넛 중앙에 '순합계(총 보유)' 표시
            annotations=[dict(
                text=f"{net_total}P<br><span style='font-size:12px'></span>",
                x=0.5, y=0.5, showarrow=False, font=dict(size=18)
            )]
        )
        center_left(pts_fig, DONUT_H, right_bias=0.26, mid=0.78)


# ======================= 시간대별 집중도 히스토그램 =======================
st.markdown("""
<style>
.focus-wrap{ width: min(100%, 980px); margin: 8px 0 0; }
.focus-wrap [data-testid="stVerticalBlockBorderWrapper"]{ max-width: 100% !important; margin: 0 !important; }
.focus-guard{ overflow:hidden; border-radius:12px; overscroll-behavior:contain; touch-action:pan-x; }
.focus-guard [data-testid="stPlotlyChart"],
.focus-guard .js-plotly-plot, .focus-guard .plot-container,
.focus-guard .svg-container, .focus-guard .main-svg{ width:100% !important; max-width:100% !important; overflow:hidden !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-head"><span>오늘의 집중도 그래프</span><span class="chev">▾</span></div>', unsafe_allow_html=True)

hist = fetch_focus_hist(start_date, end_date)
hourly = hist.get("hourly", [0]*24)

bar_x = [f"{h:02d}:00" for h in range(24)]
bar_color = "#FF9330" if not dark else "#FFA149"

fig = go.Figure(go.Bar(
    x=bar_x, y=hourly,
    marker=dict(color=bar_color),
    text=[f"{v:.0f}%" if v>0 else "" for v in hourly],
    textangle=0,
    textposition="inside", insidetextanchor="middle"
))
fig.update_layout(height=280, margin=dict(l=10,r=10,t=6,b=44),
                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                  showlegend=False, bargap=0.35)
fig.update_yaxes(range=[0,100], tickvals=[0,25,50,75,100])

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# 닫기 태그
st.markdown('</div></div>', unsafe_allow_html=True)
