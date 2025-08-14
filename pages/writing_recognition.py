# pages/ocr_quiz.py
# -*- coding: utf-8 -*-
import streamlit as st
import os, json, base64, io, json5
from openai import OpenAI
from PyPDF2 import PdfReader
from dotenv import load_dotenv

# ---- optional: PaddleOCR
try:
    from paddleocr import PaddleOCR
except Exception:
    PaddleOCR = None

st.set_page_config(page_title="PDF 요약 & 퀴즈", layout="wide", initial_sidebar_state="collapsed")
load_dotenv(dotenv_path="C:/Users/user/Desktop/최종파일/AI_final_project/.env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

USER_JSON_PATH = "user_data.json"
ASSETS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))
PLACEHOLDER_IMAGE_PATH = os.path.join(ASSETS_ROOT, "ui", "pdf_placeholder.png")

if "file_key" not in st.session_state:
    st.session_state.file_key = "uploader_1"

def _to_data_uri(p: str) -> str:
    with open(p, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")

def _load_user_data():
    data = {}
    if os.path.exists(USER_JSON_PATH):
        try:
            with open(USER_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = {}
    data.setdefault("dark_mode", False)
    data.setdefault("active_char", "rabbit")
    data.setdefault("owned_hats", [])
    data.setdefault("equipped_hat", None)
    return data

if "user_data" not in st.session_state:
    st.session_state.user_data = _load_user_data()

u = st.session_state.user_data
dark = u.get("dark_mode", False)
avatar_uri = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'><text x='50%' y='60%' font-size='28' text-anchor='middle'>🐾</text></svg>"
char_path = os.path.join(ASSETS_ROOT, "characters", f"{u.get('active_char','rabbit')}.png")
if os.path.exists(char_path):
    avatar_uri = _to_data_uri(char_path)

# ============ STYLE (헤더 유지) ============
if dark:
    bg_color = "#1C1C1E"; font_color = "#F2F2F2"; card_bg = "#2C2C2E"; nav_bg = "#2C2C2E"; nav_link = "#F2F2F2"
else:
    bg_color = "#FAFAFA"; font_color = "#333"; card_bg = "white"; nav_bg = "rgba(255,255,255,0.9)"; nav_link = "#000"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;800;900&display=swap');
html, body {{ background-color:{bg_color}; color:{font_color}; font-family:'Noto Sans KR', sans-serif; zoom:1.10; margin:0; }}
.stApp {{ background-color:{bg_color}; }}
.block-container {{ padding-top:0 !important; }}
a {{ text-decoration:none !important; color:{font_color}; }}
header, [data-testid="stSidebar"], [data-testid="stToolbar"] {{ display:none !important; }}
::selection {{ background:#FF9330; color:white; }}

.container {{ max-width:1200px; margin:auto; padding:8px 40px 40px !important; }}

.top-nav {{ display:flex; justify-content:space-between; align-items:center; padding:12px 0; margin-top:40px !important; background-color:{nav_bg}; box-shadow:0 2px 4px rgba(0,0,0,0.05); }}
.nav-left {{ display:flex; align-items:center; gap:60px; }}
.top-nav .nav-left > div:first-child a {{ color:#000 !important; font-size:28px; font-weight:bold; }}
.nav-menu {{ display:flex; gap:36px; font-size:18px; font-weight:600; }}
.nav-menu div a {{ color:{nav_link} !important; transition:.2s; }}
.nav-menu div:hover a {{ color:#FF9330 !important; }}
.nav-menu .active a {{ color:#FF8A00 !important; }}
.profile-group {{ display:flex; gap:16px; align-items:center; margin-right:12px; }}
.profile-icon {{ width:36px; height:36px; border-radius:50%; background:linear-gradient(135deg,#DDEFFF,#F8FBFF);
  overflow:hidden; display:flex; align-items:center; justify-content:center; box-shadow:0 1px 2px rgba(0,0,0,0.06); }}
.profile-icon img {{ width:100%; height:100%; object-fit:contain; }}

/* 상단 섹션 배너(퀴즈 생성기/ PDF요약 공통) */
.section{{ width:100%; background:{card_bg}; border:1px solid #F2D4B6; border-radius:14px; box-shadow:0 6px 18px rgba(17,24,39,0.06); overflow:hidden; margin:10px 0 22px 0; }}
.section-header{{ background:linear-gradient(90deg,#FF7A00,#FFA74D); color:#fff; text-align:center; font-weight:900; font-size:40px; padding:18px 0; }}
.section-body{{ padding:18px; }}

/* PDF 카드 */
.capture-card {{ width:100%; background:#fff; border:1px solid #F1E6D8; border-radius:18px;
  box-shadow:0 18px 48px rgba(17,24,39,.06); padding:26px 26px 22px; margin-top:6px; }}
.cam-wrap {{ display:flex; align-items:flex-start; gap:32px; }}
.cam-square {{ width:340px; height:340px; border-radius:18px; background:linear-gradient(180deg,#F6F9FF 0%,#EEF2F7 100%);
  border:1px solid #E9EEF6; box-shadow:0 1px 0 #FFFFFF inset, 0 10px 26px rgba(17,24,39,.06); display:flex; align-items:center; justify-content:center; }}
.cam-square .inner{{ display:flex; flex-direction:column; align-items:center; gap:16px; color:#8A94A6; }}
.cam-square .label{{ font-weight:800; font-size:18px; color:#6B7280; }}
.right-col .title {{ font-size:44px; font-weight:900; margin-top:6px; margin-bottom:8px; }}
.right-col .desc  {{ font-size:20px; color:#4B5563; margin-bottom:16px; }}
.btn-row {{ display:flex; gap:12px; align-items:center; margin:6px 0 8px; }}
div[data-testid="stFileUploader"]{{ width:210px; }}
div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"],
div[data-testid="stFileUploader"] div[data-testid="stFileUploaderDropzone"]{{ padding:0 !important; border:none !important; height:52px; width:210px; border-radius:12px;
  background:linear-gradient(90deg,#FF8A00,#FF7A00); box-shadow:0 8px 18px rgba(255,138,0,.18); cursor:pointer; }}
div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] *,
div[data-testid="stFileUploader"] div[data-testid="stFileUploaderDropzone"] * {{ display:none !important; }}
div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"]::after,
div[data-testid="stFileUploader"] div[data-testid="stFileUploaderDropzone"]::after{{ content:"파일 업로드"; display:flex; align-items:center; justify-content:center; height:52px; width:210px; color:#fff; font-weight:900; letter-spacing:.2px; }}
div[data-testid="stFileUploader"] label {{ display:none !important; }}
.ghost-btn .stButton>button{{ height:52px; padding:0 22px; background:#fff; color:#334155; border:1.5px solid #E5E7EB; border-radius:12px; font-weight:900; }}
.ghost-btn .stButton>button:hover{{ border-color:#FFB066; color:#FF7A00; }}
.small-note{{ color:#9AA3AF; margin-top:8px; }}

/* 퀴즈 플레이어 */
.quiz-shell{{ width:100%; background:#fff; border:2px solid #FFA65A; border-radius:10px; box-shadow:0 8px 24px rgba(17,24,39,.08); overflow:hidden; }}
.quiz-header{{ background:linear-gradient(90deg,#FF7A00,#FFA74D); color:#fff; text-align:center; font-weight:900; font-size:36px; padding:14px 0; border-bottom:1px solid #EFD0B2; }}
.quiz-body{{ padding:22px 24px 26px; }}
.quiz-meta{{ text-align:center; color:#111827; font-weight:800; margin-bottom:8px; }}
.quiz-question{{ text-align:center; font-size:22px; margin:6px 0 18px; }}
.opt2 .stButton>button{{ width:100%; border:1.5px solid #EFEFEF; background:#fff; border-radius:12px; padding:14px 16px; text-align:left; font-weight:700; box-shadow:0 1px 2px rgba(0,0,0,0.03); }}
.opt2 .stButton>button:hover{{ border-color:#FFD2A8; }}
.opt2.selected .stButton>button{{ border-color:#FFB066; box-shadow:0 0 0 2px rgba(255,138,0,.15) inset; }}
.action-row{{ display:flex; justify-content:center; gap:12px; margin-top:10px; }}
.action-row .stButton>button{{ height:56px; padding:0 36px; border-radius:12px; font-weight:900; border:0; }}
.next-btn .stButton>button{{ background:#FF8A00; color:#fff; }}
.prev-btn .stButton>button{{ background:#fff; color:#334155; border:1.5px solid #E5E7EB; }}
.score-pill{{ display:inline-block; padding:6px 12px; background:#FFF7ED; border:1px solid #FCD9BD; border-radius:999px; font-weight:800; color:#9A3412; }}
.result-good{{ color:#0E7C3F; font-weight:900; }}
.result-bad{{ color:#B91C1C; font-weight:900; }}
</style>
""", unsafe_allow_html=True)

# 헤더(그대로)
st.markdown(f"""
<div class="top-nav">
  <div class="nav-left">
    <div style="font-size:28px; font-weight:bold;">
      <a href="/" target="_self">🐾 딸깍공</a>
    </div>
    <div class="nav-menu">
      <div><a href="/"             target="_self">메인페이지</a></div>
      <div><a href="/main"         target="_self">공부 시작</a></div>
      <div class="active"><a href="/ocr_paddle"   target="_self">PDF 요약</a></div>
      <div><a href="/folder_page"  target="_self">저장폴더</a></div>
      <div><a href="/quiz"         target="_self">퀴즈</a></div>
      <div><a href="/report"       target="_self">리포트</a></div>
      <div><a href="/ranking"      target="_self">랭킹</a></div>
    </div>
  </div>
  <div class="profile-group">
    <div class="profile-icon" title="내 캐릭터">
      <img src="{avatar_uri}" alt="avatar"/>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ========= OpenAI / OCR helpers =========
@st.cache_resource
def get_openai_client():
    if not OPENAI_API_KEY:
        st.error("❌ .env에서 OPENAI_API_KEY를 불러올 수 없습니다.")
        st.stop()
    return OpenAI(api_key=OPENAI_API_KEY)
client = get_openai_client()

@st.cache_resource
def get_ocr():
    if PaddleOCR is None:
        return None
    return PaddleOCR(
        use_textline_orientation=True,
        lang='korean',
        text_det_box_thresh=0.2,
        text_det_unclip_ratio=2.0,
        ocr_version='PP-OCRv3'
    )
ocr = get_ocr()

def extract_pdf_text_if_possible(pdf_bytes: bytes):
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        return "\n".join([page.extract_text() or "" for page in reader.pages])
    except:
        return ""

def safe_load_json5(text):
    try:
        return json5.loads(text)
    except Exception as e:
        st.error(f"❌ JSON 파싱 실패: {e}")
        st.code(text)
        return []

def generate_quiz(content, quiz_count=8, allowed_types=None):
    type_hint = ""
    if allowed_types:
        type_hint = f"반드시 다음 유형만 사용: {', '.join(allowed_types)}. "
    prompt = f"""
너는 똑똑한 교육용 선생님이야. 아래 내용을 바탕으로 퀴즈를 JSON 리스트로 만들어줘.
예시:[{{"type":"객관식","question":"예시","options":["A","B","C","D"],"answer":"A","explanation":"해설"}}]
- {type_hint}문제마다 'type','question','answer','explanation' 포함
- 'options'는 객관식/OX에서만 포함
- JSON 리스트만 출력
- 총 {quiz_count}문제
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":prompt},{"role":"user","content":content}]
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.strip("`").lstrip("json").strip()
        parsed = safe_load_json5(raw)
        if isinstance(parsed, list) and allowed_types:
            filtered = [q for q in parsed if (q.get("type") or "").strip() in allowed_types]
            if len(filtered) >= 1:
                return filtered[:quiz_count]
        return parsed[:quiz_count] if isinstance(parsed, list) else []
    except Exception as e:
        st.error(f"❌ 퀴즈 생성 실패: {e}")
        return []

def summarize_content(content):
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"아래 내용을 3~5줄로 핵심만 요약해줘."},
                {"role":"user","content":content}
            ]
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"❌ 요약 실패: {e}")
        return "요약 실패"

def ask_gpt_about_wrong(problem, user_answer):
    prompt = f"문제: {problem['question']}\n정답: {problem['answer']}\n내 오답: {user_answer}\n왜 틀렸는지 쉽게 설명해줘."
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":"너는 친절한 선생님이야."},
            {"role":"user","content":prompt}
        ]
    )
    return resp.choices[0].message.content.strip()

def summarize_answer(answer):
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"아래 내용을 최대 2문장으로 요약."},
                {"role":"user","content":answer}
            ]
=======
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
        return resp.choices[0].message.content.strip()
    except:
        return "요약 실패"

# ============ MAIN ============
st.markdown('<div class="container">', unsafe_allow_html=True)
tab1, tab2 = st.tabs(["📄 PDF 요약", "🧠 퀴즈 생성기"])

# ---------- TAB 1 ----------
with tab1:
    st.markdown('<div class="section"><div class="section-header">PDF 요약</div><div class="section-body" style="height:36px;"></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="capture-card">', unsafe_allow_html=True)
    st.markdown('<div class="cam-wrap">', unsafe_allow_html=True)

    left, right = st.columns([1.1, 1.9], gap="large")
    with left:
        if os.path.exists(PLACEHOLDER_IMAGE_PATH):
            ph_uri = _to_data_uri(PLACEHOLDER_IMAGE_PATH)
            cam_svg = f'<img src="{ph_uri}" alt="placeholder" style="width:96px;height:96px;opacity:.9" />'
        else:
            cam_svg = """
            <svg width="96" height="96" viewBox="0 0 24 24" fill="none" stroke="#A3AEC2" xmlns="http://www.w3.org/2000/svg">
              <rect x="3" y="6.5" width="18" height="12" rx="2.5" stroke-width="1.6"/>
              <path d="M9.2 6.5l1.3-2h3l1.3 2" stroke-width="1.6"/>
              <circle cx="12" cy="12.5" r="3.2" stroke-width="1.6"/>
            </svg>
            """
        st.markdown(
            f"""
            <div class="cam-square">
              <div class="inner">
                {cam_svg}
                <div class="label">촬영화면</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with right:
        st.markdown('<div class="right-col">', unsafe_allow_html=True)
        st.markdown('<div class="title">PDF 인식</div>', unsafe_allow_html=True)
        st.markdown('<div class="desc">PDF 내용을 텍스트로 변환합니다.</div>', unsafe_allow_html=True)

        st.markdown('<div class="btn-row">', unsafe_allow_html=True)
        uploaded_raw = st.file_uploader(" ", type=["pdf"], key=st.session_state.file_key, label_visibility="collapsed")
        st.markdown('<div class="ghost-btn">', unsafe_allow_html=True)
        clicked_summary_top = st.button("요약하기", key="btn_summary_top")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="small-note">PDF를 업로드하면 요약 가능합니다.</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)     # cam-wrap
    st.markdown('</div>', unsafe_allow_html=True)     # capture-card

    if uploaded_raw is not None:
        st.session_state.pdf_bytes = uploaded_raw.getvalue()

    clean_text = ""
    if st.session_state.get("pdf_bytes"):
        text = extract_pdf_text_if_possible(st.session_state.pdf_bytes)
        if text.strip():
            clean_text = text
            st.success("✅ PDF에서 텍스트 추출 성공")
        else:
            st.error("❌ 텍스트 없는 PDF입니다.")

    if clean_text.strip():
        st.text_area("📝 인식된 텍스트", clean_text, height=220, key="ocr_result_text")

    if clicked_summary_top:
        if clean_text.strip():
            with st.spinner("요약 중..."):
                summary = summarize_content(clean_text)
                st.session_state.summary = summary
                st.text_area("📌 요약 결과", summary, height=150, key="summary_text")
        else:
            st.warning("요약할 텍스트가 없습니다. PDF를 업로드하거나 텍스트가 포함된 PDF인지 확인해주세요.")

# ---------- TAB 2 ----------
with tab2:
    # 화면 전환 상태값 (setup | play)
    if "quiz_stage" not in st.session_state:
        st.session_state.quiz_stage = "setup"

    # ========== SETUP 화면 ==========
    if st.session_state.quiz_stage == "setup":
        st.markdown('<div class="section"><div class="section-header">퀴즈 생성기</div><div class="section-body">', unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1,2,2], gap="large")
        with c1:
            quiz_count = st.number_input("문항 수", min_value=4, max_value=20, value=8, step=1, key="count_input")
            shuffle = st.checkbox("선택지 섞기", value=True, key="shuffle_input")
        with c2:
            st.markdown("**유형 선택**")
            t_obj = st.checkbox("객관식", value=True, key="t_obj")
            t_ox  = st.checkbox("OX", value=True, key="t_ox")
            t_sa  = st.checkbox("단답형", value=True, key="t_sa")
            allowed_types = [t for t, ok in [("객관식", t_obj), ("OX", t_ox), ("단답형", t_sa)] if ok]
        with c3:
            content_input = st.text_area("✍️ 학습 내용을 입력하거나 PDF 요약 결과를 사용하세요",
                                         value=st.session_state.get("quiz_content_input", ""),
                                         height=120, key="quiz_content_input")
            st.caption("✅ PDF 요약 결과가 있으면 자동으로 사용됩니다.")

        if st.button("🧠 퀴즈 생성하기", key="make_quiz"):
            content_to_use = st.session_state.get("summary", "").strip() or content_input.strip()
            if not content_to_use:
                st.warning("내용을 입력하거나 요약 결과를 생성해주세요.")
            else:
                with st.spinner("GPT가 퀴즈를 생성 중입니다..."):
                    st.session_state.summary_log = summarize_content(content_to_use)
                    data = generate_quiz(content_to_use, st.session_state.count_input, allowed_types=set(allowed_types))
                    if not data:
                        st.error("퀴즈 생성에 실패했어요. 내용을 조금 더 길게 입력해보세요.")
                    else:
                        if st.session_state.shuffle_input:
                            import random
                            for q in data:
                                if (q.get("type") in ["객관식","OX"]) and isinstance(q.get("options"), list):
                                    random.shuffle(q["options"])
                        st.session_state.quiz_data = data
                        st.session_state.user_answers = {}
                        st.session_state.current_idx = 0
                        st.session_state.graded = False
                        st.session_state.score = 0
                        st.session_state.quiz_stage = "play"
                        # 화면 전환
                        if hasattr(st, "rerun"):
                            st.rerun()
                        else:
                            st.experimental_rerun()

        if st.session_state.get("summary_log"):
            st.info(f"📚 학습 요약:\n\n{st.session_state.summary_log}")

        st.markdown('</div></div>', unsafe_allow_html=True)  # section-body/section 닫기

    # ========== PLAY 화면 ==========
    elif st.session_state.quiz_stage == "play":
        # 안전가드: 데이터 없으면 다시 setup
        if not st.session_state.get("quiz_data"):
            st.session_state.quiz_stage = "setup"
            if hasattr(st, "rerun"):
                st.rerun()
            else:
                st.experimental_rerun()

        # 상단: 뒤로가기
        back_col, _ = st.columns([1,5])
        with back_col:
            if st.button("← 다시 생성", key="back_setup"):
                # 초기화 후 설정화면으로
                for k in ["quiz_data","user_answers","current_idx","graded","score","summary_log"]:
                    if k in st.session_state: del st.session_state[k]
                st.session_state.quiz_stage = "setup"
                if hasattr(st, "rerun"):
                    st.rerun()
                else:
                    st.experimental_rerun()

        # 플레이어 본문
        def _normalize(s):
            if isinstance(s, (list, tuple)): return [str(x).strip().lower() for x in s]
            return str(s).strip().lower()

        def _is_correct(user, answer):
            u_ = _normalize(user); a_ = _normalize(answer)
            if isinstance(a_, list): return u_ in a_
            return u_ == a_

        def _render_player():
            qlist = st.session_state.quiz_data
            idx = st.session_state.current_idx
            total = len(qlist)
            q = qlist[idx]
            qtype = (q.get("type","") or "").strip()

            st.markdown('<div class="quiz-shell">', unsafe_allow_html=True)
            st.markdown('<div class="quiz-header">퀴즈 풀기</div>', unsafe_allow_html=True)
            st.markdown('<div class="quiz-body">', unsafe_allow_html=True)

            st.markdown(f'<div class="quiz-meta">{idx+1}/{total}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="quiz-question">{q.get("question","-")}</div>', unsafe_allow_html=True)

            if qtype in ["객관식","OX"]:
                options = q.get("options", []) or (["O","X"] if qtype=="OX" else [])
                letters = ["A","B","C","D","E","F"]
                if idx not in st.session_state.user_answers:
                    st.session_state.user_answers[idx] = None

                def tile(opt_text, letter, k, selected):
                    st.markdown(f"<div class='opt2{' selected' if selected else ''}'>", unsafe_allow_html=True)
                    clicked = st.button(f"{letter}  {opt_text}", key=k, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    return clicked

                for r in range(0, len(options), 2):
                    g1, g2 = st.columns(2, gap="small")
                    with g1:
                        if r < len(options):
                            opt = options[r]
                            sel = (st.session_state.user_answers[idx] == opt)
                            if tile(opt, letters[r], f"nopt_{idx}_{r}", sel):
                                st.session_state.user_answers[idx] = opt
                    with g2:
                        if r+1 < len(options):
                            opt = options[r+1]
                            sel = (st.session_state.user_answers[idx] == opt)
                            if tile(opt, letters[r+1], f"nopt_{idx}_{r+1}", sel):
                                st.session_state.user_answers[idx] = opt
            else:
                key = f"sa_{idx}"
                val = st.text_input("정답을 입력하세요", key=key)
                st.session_state.user_answers[idx] = val

            # 네비게이션
            st.markdown('<div class="action-row">', unsafe_allow_html=True)
            cprev, cnext = st.columns([1,1], gap="small")
            with cprev:
                st.markdown('<div class="prev-btn">', unsafe_allow_html=True)
                if st.button("이전", key=f"prev_{idx}") and st.session_state.current_idx > 0:
                    st.session_state.current_idx -= 1
                st.markdown('</div>', unsafe_allow_html=True)
            with cnext:
                st.markdown('<div class="next-btn">', unsafe_allow_html=True)
                if idx < total-1:
                    if st.button("다음", key=f"next_{idx}"):
                        st.session_state.current_idx += 1
                else:
                    if st.button("제출/채점", key="submit_all"):
                        score = 0
                        for i, qq in enumerate(qlist):
                            user = st.session_state.user_answers.get(i, "")
                            if _is_correct(user, qq.get("answer","")):
                                score += 1
                        st.session_state.score = score
                        st.session_state.graded = True
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)  # action-row
            st.markdown('</div>', unsafe_allow_html=True)  # quiz-body
            st.markdown('</div>', unsafe_allow_html=True)  # quiz-shell

        if st.session_state.get("quiz_data"):
            _render_player()

        if st.session_state.get("graded"):
            total = len(st.session_state.quiz_data)
            score = st.session_state.get("score", 0)
            st.markdown(f"<span class='score-pill'>점수: {score} / {total}</span>", unsafe_allow_html=True)
            ratio = score/total if total else 0
            st.markdown(f"{'🎉 <span class=\"result-good\">잘했어요!</span>' if ratio>=0.6 else '💪 <span class=\"result-bad\">조금만 더!</span>'}", unsafe_allow_html=True)

            wrongs = []
            for i, q in enumerate(st.session_state.quiz_data):
                user = st.session_state.user_answers.get(i, "")
                if not _is_correct(user, q.get("answer","")):
                    wrongs.append((i, q, user))
            if wrongs:
                st.markdown("---")
                st.markdown("#### 오답 해설")
                for i, q, user in wrongs:
                    with st.expander(f"문제 {i+1} - 내 답: {user} / 정답: {q.get('answer','')}", expanded=False):
                        try:
                            why = ask_gpt_about_wrong(q, user)
                        except Exception:
                            why = q.get("explanation","")
                        st.write(why)
