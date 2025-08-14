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
  overflow:hidden; margin-top:0px;
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

/* 카드 안에서 plotly 잘림 방지 */
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stPlotlyChart"] div{{ overflow: visible !important; }}
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

# ─── 본문 기능 ───
st.title("📄 PDF 인식 및 요약")

uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])
if uploaded_file:
    tmp_path = "temp.pdf"
    with open(tmp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    ocr_model = PaddleOCR(
    lang="korean",        # 한국어 모델
    use_angle_cls=True    # (예전 cls=True 역할은 생성자에서 설정)
)


    ocr_results = ocr_model.ocr(tmp_path)  # ⛔ cls 인자 넣지 않음
    extracted_text = "\n".join([line[1][0] for page in ocr_results for line in page])

    st.subheader("🔍 인식된 텍스트")
    st.markdown(f"""
    <textarea rows="10" style="
        width: 100%;
        background-color: {'#2C2C2E' if dark_mode else 'white'};
        color: {'white' if dark_mode else 'black'};
        border: 1px solid #555;
        border-radius: 10px;
        padding: 10px;
    " readonly>{extracted_text}</textarea>
    """, unsafe_allow_html=True)

# ---------- 섹션 헤더 ----------
st.markdown('<div class="section-head"><span>리포트 차트</span><span class="chev">▾</span></div>', unsafe_allow_html=True)

# ===== 리포트 차트 =====
c1_chart, c2_chart, c3_chart = st.columns(3, gap="small")
GAUGE_H = 220
DONUT_H = 220

# 중앙 정렬(약간 왼쪽 보정) — 안전 클램프
def center_left(fig, height, right_bias=0.16, mid=0.80):
    left = 1.0 - (mid + right_bias)
    left = max(0.01, left)  # 음수/0 방지
    l, m, r = st.columns([left, mid, right_bias])
    fig.update_layout(height=height)
    with m:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# 팔레트(평균 차트 기준) + 테두리 색
ORANGE_DARK  = "#FFB74D"
ORANGE_MID   = "#FFCC80"
ORANGE_LIGHT = "#FFE0B2"
ORANGE_BAR   = "#FFA726"
BORDER_BLACK = "#2B2B2E"

# 도넛에 ‘연속된’ 바깥/안쪽(홀) 테두리 추가
def add_donut_border(fig: go.Figure, hole: float = 0.58, color: str = BORDER_BLACK, width: float = 3.0):
    # 바깥 원
    fig.add_shape(type="circle",
                  xref="paper", yref="paper",
                  x0=0.03, y0=0.03, x1=0.97, y1=0.97,
                  line=dict(color=color, width=width),
                  fillcolor="rgba(0,0,0,0)")
    # 안쪽(홀) 원
    r = hole / 2.0
    x0 = 0.5 - r; y0 = 0.5 - r; x1 = 0.5 + r; y1 = 0.5 + r
    fig.add_shape(type="circle",
                  xref="paper", yref="paper",
                  x0=x0, y0=y0, x1=x1, y1=y1,
                  line=dict(color=color, width=width),
                  fillcolor="rgba(0,0,0,0)")

# --- 1) 평균 차트(게이지) ---
with c1_chart:
    category = st.session_state.get("metric_select", "일 공부 시간 평균")

    with st.container(border=True):
        st.markdown("### 평균 차트")

        if category == "일 공부 시간 평균":
            avg_minutes = float(filtered_df["학습시간"].mean() or 0.0)
            gauge_value = int(round(avg_minutes))     # 중앙 숫자: 분
            max_range = 24 * 60                       # 0~1440분
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
                'bar': {'color': ORANGE_BAR},
                'bgcolor': "white",
                'bordercolor': BORDER_BLACK,      # 검은 외곽선
                'borderwidth': 2,
                'steps': [
                    {'range': [0, max_range * 0.33],                 'color': ORANGE_LIGHT},
                    {'range': [max_range * 0.33, max_range * 0.66],  'color': ORANGE_MID},
                    {'range': [max_range * 0.66, max_range],         'color': ORANGE_DARK},
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

# --- 2) 출석 차트 (오렌지 팔레트 + 연속 테두리) ---
with c2_chart:
    with st.container(border=True):
        st.markdown("### 출석 차트")
        days = len(filtered_df)
        present = int(filtered_df["출석"].sum())
        absent = max(0, days - present)
        present_rate = round((present / days) * 100, 1) if days else 0.0

        HOLE = 0.58
        att_fig = go.Figure(data=[
            go.Pie(
                labels=["출석", "결석"],
                values=[present, absent] if days else [1, 1],
                hole=HOLE,
                textinfo="percent+label",
                insidetextorientation="radial",
                sort=False,
                marker=dict(
                    colors=[ORANGE_DARK, ORANGE_LIGHT],           # 평균 차트 팔레트
                    line=dict(color=BORDER_BLACK, width=3)        # 슬라이스 경계선
                )
            )
        ])
        add_donut_border(att_fig, hole=HOLE, color=BORDER_BLACK, width=3.2)  # 연속 외곽선

        att_fig.update_layout(
            margin=dict(l=10, r=10, t=6, b=44),
            showlegend=False, paper_bgcolor='rgba(0,0,0,0)',
            annotations=[dict(text=f"{present_rate:.1f}% 출석", x=0.5, y=0.5,
                              font=dict(size=18, color="#4B5563"), showarrow=False)]
        )
        center_left(att_fig, DONUT_H, right_bias=0.26, mid=0.78)

# --- 3) 포인트 획득 차트 (오렌지 팔레트 + 연속 테두리) ---
with c3_chart:
    with st.container(border=True):
        st.markdown("### 포인트 획득 차트")

        total_pts = int(filtered_df["포인트"].sum())
        weights = {"퀴즈": 0.40, "출석": 0.35, "집중도": 0.25}
        pdata = {k: round(total_pts * w) for k, w in weights.items()} if total_pts > 0 else {k: 0 for k in weights}
        vals = list(pdata.values())
        if sum(vals) == 0:
            vals = [1, 1, 1]

        HOLE = 0.58
        pts_fig = go.Figure(data=[
            go.Pie(
                labels=list(pdata.keys()),
                values=vals,
                hole=HOLE,
                textinfo="percent+label",
                insidetextorientation="radial",
                sort=False,
                marker=dict(
                    colors=[ORANGE_DARK, ORANGE_MID, ORANGE_LIGHT],  # 평균 차트 팔레트
                    line=dict(color=BORDER_BLACK, width=3)           # 슬라이스 경계선
                )
            )
        ])
        add_donut_border(pts_fig, hole=HOLE, color=BORDER_BLACK, width=3.2)  # 연속 외곽선

        pts_fig.update_layout(
            margin=dict(l=10, r=10, t=6, b=48),
            showlegend=False, paper_bgcolor='rgba(0,0,0,0)',
            annotations=[dict(text=f"{total_pts}P", x=0.5, y=0.5,
                              font=dict(size=18, color="#4B5563"), showarrow=False)]
        )
        center_left(pts_fig, DONUT_H, right_bias=0.26, mid=0.78)

# 종료
st.markdown("</div>", unsafe_allow_html=True)  # /panel-body
st.markdown("</div>", unsafe_allow_html=True)  # /panel
st.markdown("</div>", unsafe_allow_html=True)  # /container
