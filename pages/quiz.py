# pages/quiz_only.py
# -*- coding: utf-8 -*-
import os, re, json, random, base64
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# ─────────────────────────────────────────────────────────────────────────────
# 환경변수 로드
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv(dotenv_path="C:/Users/user/Desktop/main_project/.env", override=True)

# =========================
# 페이지 기본 설정
# =========================
st.set_page_config(page_title="🧩 퀴즈", layout="wide", initial_sidebar_state="collapsed")

# =========================
# (추가) 헤더 구현을 위한 유저/에셋 로딩 — 랭킹 페이지와 동일 규격
# =========================
USER_JSON_PATH = "user_data.json"
ASSETS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))

_HDR_DEFAULTS = {
    "dark_mode": False,
    "nickname": "-",
    "coins": 500,
    "mode": "ranking",
    "active_char": "rabbit",
    "owned_hats": [],
    "equipped_hat": None,
}

def _hdr_load_user():
    data = {}
    if os.path.exists(USER_JSON_PATH):
        try:
            with open(USER_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    for k, v in _HDR_DEFAULTS.items():
        if k not in data: data[k] = v
    return data

def _hdr_to_data_uri(abs_path: str) -> str:
    with open(abs_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return "data:image/png;base64," + b64

def _hdr_get_char_image_uri(char_key: str, hat_id: str | None = None) -> str:
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
        if os.path.exists(p): return _hdr_to_data_uri(p)
    return "data:image/svg+xml;utf8," \
           "<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'><text x='50%' y='60%' font-size='28' text-anchor='middle'>🐾</text></svg>"

_hdr_user = _hdr_load_user()
_hdr_hat = _hdr_user.get("equipped_hat")
_hdr_avatar_uri = _hdr_get_char_image_uri(
    _hdr_user.get("active_char","rabbit"),
    _hdr_hat if (_hdr_hat in _hdr_user.get("owned_hats", [])) else None
)

# 테마 변수 (랭킹 페이지와 동일 로직)
dark = bool(_hdr_user.get("dark_mode", False))
if dark:
    bg_color = "#1C1C1E"; font_color = "#F2F2F2"
    card_bg = "#2C2C2E"; nav_bg = "#2C2C2E"; nav_link = "#F2F2F2"
    sub_text = "#CFCFCF"
else:
    bg_color = "#F5F5F7"; font_color = "#2B2B2E"
    card_bg = "#FFFFFF"; nav_bg = "rgba(255,255,255,.9)"; nav_link = "#000"
    sub_text = "#6B7280"

# 패널 배경/그림자 (랭킹 페이지 동일)
panel_bg     = "#1F1F22" if dark else "#FFFFFF"
panel_shadow = "rgba(0,0,0,.35)" if dark else "rgba(0,0,0,.08)"

# =========================
# 스타일 (헤더/패널 규격은 랭킹 페이지와 동일하게)
# =========================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;800;900&display=swap');

html, body {{ background:{bg_color}; color:{font_color}; font-family:'Noto Sans KR', sans-serif; zoom:1.10; margin:0; }}
.stApp {{ background:{bg_color}; }}
.block-container {{ padding-top:0 !important; }}
header, [data-testid="stSidebar"], [data-testid="stToolbar"] {{ display:none !important; }}
::selection {{ background:#FF9330; color:white; }}

/* ===== 헤더(고정 규격) ===== */
.container {{ max-width:1200px; margin:auto; padding:4px 40px 24px; }}
.container.tight-top {{ padding:4px 40px 24px; }}
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

/* ===== 주황 타이틀 패널(고정 규격) ===== */
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

/* ── 기존 퀴즈 카드 UI 유지 ────────────────────────────────── */
.section-wrap {{
  background:#fff; border:1px solid #F1E6D8; border-radius:18px;
  box-shadow:0 18px 48px rgba(17,24,39,.06);
  padding:0;                 /* 상단 패딩 0 → 하얀 띠 제거 */
  overflow:hidden;           /* 모서리 라운드 정확히 */
}}
.section-head{{
  display:flex; align-items:center; justify-content:space-between;
  background:linear-gradient(90deg,#FF9330,#FF7A00);
  color:#fff; font-weight:900; font-size:22px;
  padding:14px 18px; margin:0 0 14px 0; border-radius:18px 18px 0 0;
}}
.card-body {{ padding:16px 18px 0; }}
.subtle {{ color:#6B7280; font-size:14px; }}

label {{ font-weight:700; }}

.primary-btn .stButton>button{{
  height:48px; width:100%; padding:0 18px;
  background:linear-gradient(90deg,#FF9330,#FF7A00);
  color:#fff; border:0; border-radius:12px; font-weight:900;
}}
.primary-btn .stButton>button:disabled{{ opacity:.45; cursor:not-allowed; }}

.opt2 .stButton>button{{ width:100%; border:1.5px solid #EFEFEF; background:#fff; border-radius:12px; padding:14px 16px; text-align:left; font-weight:700; box-shadow:0 1px 2px rgba(0,0,0,0.03); }}
.opt2 .stButton>button:hover{{ border-color:#FFD2A8; }}
.opt2.selected .stButton>button{{ border-color:#FFB066; box-shadow:0 0 0 2px rgba(255,138,0,.15) inset; background:linear-gradient(90deg,#FF9330,#FF7A00); color:#fff; }}

.quiz-shell{{ width:100%; background:#fff; border:2px solid #FFA65A; border-radius:10px; box-shadow:0 8px 24px rgba(17,24,39,.08); overflow:hidden; }}
.quiz-body{{ padding:22px 24px 26px; }}
.quiz-meta{{ font-weight:800; color:#FF7A00; margin-bottom:8px; }}
.quiz-question{{ font-size:20px; font-weight:900; margin:6px 0 14px; }}

.result-wrap{{ background:#fff;border:1px solid #F1E6D8;border-radius:18px; box-shadow:0 18px 48px rgba(17,24,39,.06);padding:20px; }}
.result-hero{{display:flex;flex-direction:column;align-items:center;gap:8px;margin:8px 0 16px;}}
.score-ring{{width:140px;height:140px;border-radius:999px;background:conic-gradient(#FF9330 calc(var(--pct,0)*1%), #FFE1C2 0);display:flex;align-items:center;justify-content:center; box-shadow:0 6px 18px rgba(255,138,0,.18);}}
.score-ring .score{{background:#fff;border-radius:999px;padding:14px 20px;font-weight:900;font-size:24px;}}
.chip-row{{display:flex;gap:12px;justify-content:center;margin:4px 0 12px;}}
.chip{{display:flex;flex-direction:column;align-items:center;justify-content:center;min-width:110px;padding:10px 12px;border-radius:12px;background:#F6FFFA;border:1px solid #BFEAD4;font-weight:800}}
.chip.red{{background:#FFF6F6;border-color:#F7C2C2}}
.meter{{height:10px;border-radius:999px;background:#F2F4F7;overflow:hidden;margin:6px 0 2px;}}
.meter>div{{height:100%;background:#FF9330;}}
.block-container > div:empty {{ display:none !important; margin:0 !important; padding:0 !important; }}
.pill {{ background:#fff; color:#1f2937; font-weight:900; padding:8px 14px; border-radius:999px; }}
</style>
""", unsafe_allow_html=True)

# ===== 랭킹페이지와 동일한 헤더 마크업 =====
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
    <div class="profile-icon" title="내 캐릭터"><img src="{_hdr_avatar_uri}" alt="avatar"/></div>
  </div>
</div>
""", unsafe_allow_html=True)

# =========================
# OpenAI 클라이언트 (기존 이름 유지)
# =========================
@st.cache_resource
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ .env 파일에서 OpenAI API 키(OPENAI_API_KEY)를 찾을 수 없습니다.")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()
MODEL_SUMMARY = "gpt-4o-mini"

# =========================
# 유틸/생성 함수 (기존 이름 유지)
# =========================
def gpt_chat(messages, model=MODEL_SUMMARY, temperature=0.2, max_tokens=None):
    resp = client.chat.completions.create(
        model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
    )
    return resp.choices[0].message.content.strip()

def summarize_content(content: str):
    if not content or not content.strip():
        return "요약할 내용이 없습니다."
    sys = "아래 내용을 6~8줄로 핵심만 요약해줘. 숫자/고유명사 유지."
    return gpt_chat([{"role":"system","content":sys},{"role":"user","content":content}])

def _safe_json_parse(s: str):
    s = s.strip()
    m = re.search(r"\[.*\]", s, flags=re.S)
    if m: s = m.group(0)
    try:
        import json5
        return json5.loads(s)
    except Exception:
        return json.loads(s)

def generate_quiz(content: str, count: int = 8, allowed_types: set = None):
    if not content.strip(): return []
    if not allowed_types:
        allowed_types = {"객관식","OX","단답형"}

    system = "너는 한국어 학습용 퀴즈 출제 도우미야. 항상 JSON만 출력해."
    user = f"""
다음 학습 내용을 바탕으로 퀴즈 {count}문제를 생성해.
허용 유형: {sorted(list(allowed_types))}
- 각 문제: {{"type":"객관식|OX|단답형","question":"문제","options":["보기1",...],"answer":"정답 또는 [정답들]","explanation":"간단 해설"}}
- 객관식 ≥ 4지선다, OX는 ["O","X"] 고정, 단답형은 options 빈 리스트 허용.
- JSON 배열만 출력.
내용:
\"\"\"{content[:20000]}\"\"\""""
    try:
        raw = gpt_chat(
            [{"role":"system","content":system},{"role":"user","content":user}],
            model=MODEL_SUMMARY, temperature=0.2, max_tokens=2000
        )
        data = _safe_json_parse(raw)
        if not isinstance(data, list): return []
        norm = []
        for item in data:
            qtype = (item.get("type","") or "").strip()
            if qtype not in {"객관식","OX","단답형"}: continue
            q = {
                "type": qtype,
                "question": item.get("question","").strip(),
                "options": item.get("options", []) or ([] if qtype=="단답형" else (["O","X"] if qtype=="OX" else [])),
                "answer": item.get("answer", ""),
                "explanation": item.get("explanation", "")
            }
            if qtype == "OX": q["options"] = ["O","X"]
            norm.append(q)
        if len(norm) > count: norm = norm[:count]
        return norm
    except Exception:
        return []

def ask_gpt_about_wrong(qobj: dict, user_answer: str) -> str:
    question = qobj.get("question","")
    answer   = qobj.get("answer","")
    expl     = qobj.get("explanation","")
    opts     = qobj.get("options", [])
    system = "너는 한국어 교사야. 학생의 오답을 짧고 명확히 설명해."
    user = f"""문제: {question}
선택지: {opts}
학생의 답: {user_answer}
정답: {answer}
기존 해설: {expl}
요청: 3~5문장 설명 + 핵심 키워드 1~2개."""
    try:
        return gpt_chat([{"role":"system","content":system},{"role":"user","content":user}], model=MODEL_SUMMARY, temperature=0.2, max_tokens=500)
    except Exception:
        return expl or "해설 생성에 실패했습니다."

# =========================
# 배팅 퀴즈 전용 생성기(추가)
# 구성: 객관식 3 + OX 3 + 단답형 4 (난이도: 중~상)
# =========================
def _enforce_composition(qlist, comp):
    out, need = [], {k:v for k,v in comp.items()}
    for t, n in comp.items():
        picked = [q for q in qlist if (q.get("type") or "").strip()==t][:n]
        out.extend(picked)
        need[t] = max(0, n - len(picked))
    remain = [q for q in qlist if q not in out]
    for t, n in need.items():
        for _ in range(n):
            if remain:
                q = dict(remain.pop(0))
            else:
                q = {"question":"빈칸을 채우세요.","type":"단답형","options":[],"answer":"","explanation":""}
            q["type"] = t
            if t == "OX": q["options"] = ["O","X"]
            elif t == "단답형": q["options"] = []
            out.append(q)
    total_need = sum(comp.values())
    if len(out) > total_need: out = out[:total_need]
    return out

def generate_quiz_betting(content: str):
    """배팅 전용 10문제 생성 (객관식3, OX3, 단답형4 · 난이도 중~상)"""
    if not content.strip(): return []
    system = "너는 한국어 학습용 퀴즈 출제 도우미야. 항상 JSON만 출력해."
    user = f"""
아래 학습 내용을 바탕으로 난이도 '중~상' 퀴즈를 정확히 10문제 생성해.
구성은 반드시 다음을 만족:
- 객관식 3문제, OX 3문제, 단답형 4문제 (총 10문제)
- 각 문제 형식: {{"type":"객관식|OX|단답형","question":"문제","options":["보기1",...],"answer":"정답 또는 [정답들]","explanation":"간단 해설"}}
- 객관식은 4지선다 이상, OX는 options를 ["O","X"]로 고정, 단답형은 options 빈 리스트.
- JSON 배열만 출력.

내용:
\"\"\"{content[:20000]}\"\"\""""
    try:
        raw = gpt_chat(
            [{"role":"system","content":system},{"role":"user","content":user}],
            model=MODEL_SUMMARY, temperature=0.3, max_tokens=2200
        )
        data = _safe_json_parse(raw)
        if not isinstance(data, list): return []
        norm=[]
        for item in data:
            qtype = (item.get("type","") or "").strip()
            if qtype not in {"객관식","OX","단답형"}: continue
            q = {
                "type": qtype,
                "question": item.get("question","").strip(),
                "options": item.get("options", []) or ([] if qtype=="단답형" else (["O","X"] if qtype=="OX" else [])),
                "answer": item.get("answer", ""),
                "explanation": item.get("explanation", "")
            }
            if qtype == "OX": q["options"] = ["O","X"]
            norm.append(q)
        norm = _enforce_composition(norm, {"객관식":3, "OX":3, "단답형":4})
        return norm
    except Exception:
        return []

# =========================
# 상태 초기화 + 상단 타이틀 패널(주황색 박스)
# =========================
st.markdown('<div class="container">', unsafe_allow_html=True)
st.markdown('<div class="panel"><div class="panel-head">퀴즈</div><div class="panel-body">', unsafe_allow_html=True)

# 최초 포인트 (가정 100P)
if "user_points" not in st.session_state:
    st.session_state.user_points = 100

# 분리된 단계: 일반 퀴즈 / 배팅 퀴즈
if "quiz_stage" not in st.session_state: st.session_state.quiz_stage = "setup"
if "bet_stage"  not in st.session_state: st.session_state.bet_stage  = "setup"

# ─────────────────────────────────────────────────────────────────────────────
# 상단 좌·우 섹션(동일 규격 헤더 바)
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.quiz_stage == "setup" and st.session_state.bet_stage == "setup":
    L, R = st.columns(2, gap="large")

    with L:
        st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
        st.markdown('<div class="section-head"><div>퀴즈 생성</div><div style="width:1px;"></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="card-body">', unsafe_allow_html=True)

        # 유형 선택 + 문항 수
        st.markdown("**유형 선택**")
        t_obj = st.checkbox("객관식", value=True, key="t_obj")
        t_ox  = st.checkbox("OX", value=True, key="t_ox")
        t_sa  = st.checkbox("단답형", value=True, key="t_sa")
        allowed_types = [t for t, ok in [("객관식", t_obj), ("OX", t_ox), ("단답형", t_sa)] if ok]

        quiz_count = st.number_input("문항 수", min_value=4, max_value=20, value=8, step=1, key="count_input")
        content_input = st.text_area("✍️ (퀴즈 생성) 학습 내용을 입력하세요", value="", height=140, key="quiz_content_input")

        st.markdown('<div class="primary-btn" style="margin-top:8px;">', unsafe_allow_html=True)
        make_btn = st.button("퀴즈 생성하기", key="make_quiz", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if make_btn:
            content_to_use = (st.session_state.get("quiz_content_input","") or "").strip()
            if not content_to_use:
                st.warning("내용을 입력해주세요.")
            else:
                with st.spinner("GPT가 퀴즈를 생성 중입니다..."):
                    st.session_state.summary_log = summarize_content(content_to_use)
                    data = generate_quiz(content_to_use, quiz_count, allowed_types=set(allowed_types or {"객관식","OX","단답형"}))
                    if not data:
                        st.error("퀴즈 생성에 실패했어요. 내용을 조금 더 길게 입력해보세요.")
                    else:
                        st.session_state.quiz_data = data
                        st.session_state.user_answers = {}
                        st.session_state.current_idx = 0
                        st.session_state.graded = False
                        st.session_state.score = 0
                        st.session_state.quiz_stage = "play"
                        st.rerun()

        st.markdown('</div></div>', unsafe_allow_html=True)

    with R:
        st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-head"><div>배팅 퀴즈 생성</div><div class="pill">{st.session_state.user_points} P</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="card-body">', unsafe_allow_html=True)

        bet_points = st.number_input("배팅 포인트", min_value=0, max_value=max(0, st.session_state.user_points),
                                     value=min(100, st.session_state.user_points), step=5, key="bet_points_input")

        st.markdown("""
        <div class='subtle' style='margin:8px 0 4px;'>
          • 문항 수는 <b>항상 10문항</b><br>
          • 성공 기준: <b>7개 이상 정답</b> 시 <b>1.25배</b> 지급<br>
          • 실패: 배팅 포인트 <b>전액 소멸</b>
        </div>
        """, unsafe_allow_html=True)

        content_input_bet = st.text_area("✍️ (포인트 배팅) 학습 내용을 입력하세요", value="", height=140, key="bet_content_input")
        can_bet = (st.session_state.user_points > 0) and (bet_points > 0) and (bet_points <= st.session_state.user_points)

        st.markdown('<div class="primary-btn" style="margin-top:8px;">', unsafe_allow_html=True)
        bet_btn = st.button("배팅 퀴즈 생성하기", key="make_bet_quiz", use_container_width=True, disabled=not can_bet)
        st.markdown('</div>', unsafe_allow_html=True)

        if bet_btn:
            content_to_use = (st.session_state.get("bet_content_input","") or "").strip()
            if not content_to_use:
                st.warning("배팅 퀴즈용 내용을 입력해주세요.")
            else:
                with st.spinner("GPT가 배팅 퀴즈를 생성 중입니다... (10문제/중~상)"):
                    data = generate_quiz_betting(content_to_use)
                    if not data or len(data) != 10:
                        st.error("배팅 퀴즈 생성에 실패했어요. 내용을 조금 더 길게 입력해보세요.")
                    else:
                        st.session_state.bet_quiz_data    = data
                        st.session_state.bet_user_answers = {}
                        st.session_state.bet_current_idx  = 0
                        st.session_state.bet_score        = 0
                        st.session_state.bet_goal         = 7
                        st.session_state.bet_points_at_stake = int(bet_points)
                        st.session_state.bet_stage = "play"
                        st.rerun()

        st.markdown('</div></div>', unsafe_allow_html=True)

# 요약(선택)
if st.session_state.get("summary_log") and st.session_state.quiz_stage == "setup":
    st.info(f"📚 내용 요약:\n\n{st.session_state.summary_log}")

# ─────────────────────────────────────────────────────────────────────────────
# 공통 정규화 함수(기존 이름 유지)
# ─────────────────────────────────────────────────────────────────────────────
def _normalize(s):
    if isinstance(s, (list, tuple)): return [str(x).strip().lower() for x in s]
    return str(s).strip().lower()

def _is_correct(user, answer):
    u_ = _normalize(user); a_ = _normalize(answer)
    if isinstance(a_, list): return u_ in a_
    return u_ == a_

# ─────────────────────────────────────────────────────────────────────────────
# 플레이 렌더러 (동일 페이지 내 '다음 페이지'처럼 전환)
# ─────────────────────────────────────────────────────────────────────────────
def _render_player_generic(kind="normal"):
    # kind: "normal" | "bet"
    if kind == "normal":
        qlist = st.session_state.get("quiz_data")
        if not qlist: return
        idx   = st.session_state.get("current_idx", 0)
        ans_store = "user_answers"
        title = "퀴즈 풀기"
    else:
        qlist = st.session_state.get("bet_quiz_data")
        if not qlist: return
        idx   = st.session_state.get("bet_current_idx", 0)
        ans_store = "bet_user_answers"
        title = "배팅 퀴즈"

    total = len(qlist)
    q = qlist[idx]
    qtype = (q.get("type","") or "").strip()

    st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
    st.markdown(f'<div class="section-head"><div>{title}</div><div style="width:1px;"></div></div>', unsafe_allow_html=True)

    st.markdown('<div class="quiz-shell"><div class="quiz-body">', unsafe_allow_html=True)
    st.markdown(f'<div class="quiz-meta">{idx+1}/{total}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="quiz-question">{q.get("question","-")}</div>', unsafe_allow_html=True)

    # 선택/입력
    if qtype in ["객관식","OX"]:
        options = q.get("options", []) or (["O","X"] if qtype=="OX" else [])
        labels = [f"{i+1}." for i in range(len(options))]
        if ans_store not in st.session_state: st.session_state[ans_store] = {}
        if idx not in st.session_state[ans_store]:
            st.session_state[ans_store][idx] = None

        def tile(opt_text, label, k, selected):
            st.markdown(f"<div class='opt2{' selected' if selected else ''}'>", unsafe_allow_html=True)
            clicked = st.button(f"{label}  {opt_text}", key=k, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            return clicked

        for r in range(0, len(options), 2):
            g1, g2 = st.columns(2, gap="small")
            with g1:
                if r < len(options):
                    opt = options[r]
                    sel = (st.session_state[ans_store][idx] == opt)
                    if tile(opt, labels[r], f"{kind}_nopt_{idx}_{r}", sel):
                        st.session_state[ans_store][idx] = opt
            with g2:
                if r+1 < len(options):
                    opt = options[r+1]
                    sel = (st.session_state[ans_store][idx] == opt)
                    if tile(opt, labels[r+1], f"{kind}_nopt_{idx}_{r+1}", sel):
                        st.session_state[ans_store][idx] = opt
    else:
        key = f"{kind}_sa_{idx}"
        val = st.text_input("정답을 입력하세요", key=key, value=st.session_state.get(ans_store, {}).get(idx) or "")
        if ans_store not in st.session_state: st.session_state[ans_store] = {}
        st.session_state[ans_store][idx] = val

    # 이동/제출
    cprev, cnext = st.columns([1,1], gap="small")
    with cprev:
        if idx > 0 and st.button("이전", key=f"{kind}_prev_{idx}"):
            if kind=="normal":
                st.session_state.current_idx -= 1
            else:
                st.session_state.bet_current_idx -= 1
            st.rerun()

    with cnext:
        if idx < total-1:
            if st.button("다음", key=f"{kind}_next_{idx}"):
                if kind=="normal":
                    st.session_state.current_idx += 1
                else:
                    st.session_state.bet_current_idx += 1
                st.rerun()
        else:
            label = "제출/채점" if kind=="normal" else "제출/채점 (배팅)"
            if st.button(label, key=f"{kind}_submit_all"):
                score = 0
                answers = st.session_state.get(ans_store, {})
                for i, qq in enumerate(qlist):
                    user = answers.get(i, "")
                    if _is_correct(user, qq.get("answer","")):
                        score += 1
                if kind=="normal":
                    st.session_state.score  = score
                    st.session_state.graded = True
                    st.session_state.quiz_stage = "result"
                else:
                    st.session_state.bet_score = score
                    st.session_state.bet_stage = "result"
                st.rerun()

    st.markdown('</div></div>', unsafe_allow_html=True)  # quiz-body, quiz-shell
    st.markdown('</div>', unsafe_allow_html=True)  # section-wrap

# ─────────────────────────────────────────────────────────────────────────────
# 분기: 일반 퀴즈 플레이/결과 (단일 페이지 내 전환)
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.quiz_stage == "play":
    _render_player_generic("normal")

elif st.session_state.quiz_stage == "result":
    qlist = st.session_state.get("quiz_data", [])
    total = len(qlist)
    score = st.session_state.get("score", 0)
    ratio = (score / total) if total else 0.0

    by_tot = {"객관식":0, "OX":0, "단답형":0}
    by_ok  = {"객관식":0, "OX":0, "단답형":0}
    wrong_list = []

    # 집계 + 오답 수집
    for i, qq in enumerate(qlist):
        t = (qq.get("type") or "").strip()
        by_tot[t] = by_tot.get(t,0) + 1
        user = st.session_state.user_answers.get(i, "")
        if _is_correct(user, qq.get("answer","")):
            by_ok[t] = by_ok.get(t,0) + 1
        else:
            wrong_list.append((i, qq, user))

    st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div>퀴즈 결과</div><div style="width:1px;"></div></div>', unsafe_allow_html=True)

    pct = int(ratio * 100)
    st.markdown(
        f"""
        <div class="result-wrap">
          <div class="result-hero" style="--pct:{pct};">
            <div class="score-ring"><span class="score">{score} / {total}</span></div>
          </div>
          <div class="chip-row">
            <div class="chip">OX<br><span>{by_ok.get('OX',0)} / {by_tot.get('OX',0)}</span></div>
            <div class="chip">객관식<br><span>{by_ok.get('객관식',0)} / {by_tot.get('객관식',0)}</span></div>
            <div class="chip red">단답형<br><span>{by_ok.get('단답형',0)} / {by_tot.get('단답형',0)}</span></div>
          </div>
          <div class="meter"><div style="width:{pct}%"></div></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 해설 섹션
    st.markdown('<div class="section-wrap" style="margin-top:14px;">', unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div>해설</div><div style="width:1px;"></div></div>', unsafe_allow_html=True)
    if not wrong_list:
        st.markdown('<div class="card-body">👏 모두 정답입니다!</div>', unsafe_allow_html=True)
    else:
        for i, qq, ua in wrong_list:
            with st.expander(f"#{i+1} 틀린 문제 보기"):
                st.markdown(f"**문제:** {qq.get('question','-')}")
                if qq.get("options"):
                    st.markdown(f"**보기:** {qq.get('options')}")
                st.markdown(f"**내 답:** {ua}")
                st.markdown(f"**정답:** {qq.get('answer')}")
                explain = ask_gpt_about_wrong(qq, ua)
                st.markdown("---")
                st.markdown(f"**해설:**\n\n{explain}")
    st.markdown('</div>', unsafe_allow_html=True)

    # GPT 자유 질문
    st.markdown('<div class="section-wrap" style="margin-top:14px;">', unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div>GPT에게 질문하기</div><div style="width:1px;"></div></div>', unsafe_allow_html=True)
    free_q = st.text_area("시험 개념/오답 이유 등 무엇이든 질문해 보세요.", height=120, key="free_q_input_normal")
    if st.button("질문 보내기", key="free_q_send_normal", use_container_width=True):
        if not free_q.strip():
            st.warning("질문을 입력해 주세요.")
        else:
            context = {"kind":"normal","score":score,"total":total,"wrong_count":len(wrong_list)}
            sys = "너는 한국어 학습 도우미야. 학생의 질문에 간결하고 정확하게 답하고, 필요하면 작은 예시와 함께 설명해."
            usr = f"퀴즈 맥락: {context}\n질문: {free_q.strip()}"
            ans = gpt_chat([{"role":"system","content":sys},{"role":"user","content":usr}], max_tokens=700)
            st.success("답변을 가져왔어요.")
            st.markdown(ans)
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 분기: 배팅 퀴즈 플레이/결과 (단일 페이지 내 전환)
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.bet_stage == "play":
    _render_player_generic("bet")

elif st.session_state.bet_stage == "result":
    qlist = st.session_state.get("bet_quiz_data", [])
    total = len(qlist)
    score = st.session_state.get("bet_score", 0)
    ratio = (score / total) if total else 0.0
    goal  = st.session_state.get("bet_goal", 7)
    stake = int(st.session_state.get("bet_points_at_stake", 0))

    # 포인트 반영(중복 방지)
    won = score >= goal
    delta = int(round(stake * 1.25)) if won else -stake
    if "bet_result_applied" not in st.session_state:
        st.session_state.user_points = max(0, st.session_state.user_points + delta)
        st.session_state.bet_result_applied = True

    st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div>배팅 퀴즈 결과</div><div class="pill">{:d} P</div></div>'.format(st.session_state.user_points), unsafe_allow_html=True)

    by_tot = {"객관식":0, "OX":0, "단답형":0}
    by_ok  = {"객관식":0, "OX":0, "단답형":0}
    answers = st.session_state.get("bet_user_answers", {})
    for i, qq in enumerate(qlist):
        t = (qq.get("type") or "").strip()
        by_tot[t] = by_tot.get(t,0) + 1
        if _is_correct(answers.get(i,""), qq.get("answer","")):
            by_ok[t] = by_ok.get(t,0) + 1

    banner = f"🎉 성공! +{delta}P" if won else f"😢 실패… {abs(delta)}P 소멸"
    pct = int(ratio * 100)
    st.markdown(
        f"""
        <div class="result-wrap">
          <div class="result-hero" style="--pct:{pct};">
            <div class="score-ring"><span class="score">{score} / {total}</span></div>
            <div class="comment" style="font-weight:900;">{banner} (목표 {goal}개)</div>
          </div>
          <div class="chip-row">
            <div class="chip">OX<br><span>{by_ok.get('OX',0)} / {by_tot.get('OX',0)}</span></div>
            <div class="chip">객관식<br><span>{by_ok.get('객관식',0)} / {by_tot.get('객관식',0)}</span></div>
            <div class="chip red">단답형<br><span>{by_ok.get('단답형',0)} / {by_tot.get('단답형',0)}</span></div>
          </div>
          <div class="meter"><div style="width:{pct}%"></div></div>
          <div class="subtle" style="text-align:center;margin-top:8px;">다음 배팅을 위해 상단 카드에서 포인트와 내용을 입력하세요.</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # 해설 섹션
    wrong_list = []
    for i, qq in enumerate(qlist):
        if not _is_correct(answers.get(i,""), qq.get("answer","")):
            wrong_list.append((i, qq, answers.get(i,"")))
    st.markdown('<div class="section-wrap" style="margin-top:14px;">', unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div>해설</div><div style="width:1px;"></div></div>', unsafe_allow_html=True)
    if not wrong_list:
        st.markdown('<div class="card-body">👏 모두 정답입니다!</div>', unsafe_allow_html=True)
    else:
        for i, qq, ua in wrong_list:
            with st.expander(f"#{i+1} 틀린 문제 보기"):
                st.markdown(f"**문제:** {qq.get('question','-')}")
                if qq.get("options"):
                    st.markdown(f"**보기:** {qq.get('options')}")
                st.markdown(f"**내 답:** {ua}")
                st.markdown(f"**정답:** {qq.get('answer')}")
                explain = ask_gpt_about_wrong(qq, ua)
                st.markdown("---")
                st.markdown(f"**해설:**\n\n{explain}")
    st.markdown('</div>', unsafe_allow_html=True)

    # GPT 자유 질문
    st.markdown('<div class="section-wrap" style="margin-top:14px;">', unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div>GPT에게 질문하기</div><div style="width:1px;"></div></div>', unsafe_allow_html=True)
    free_q_bet = st.text_area("시험 개념/오답 이유 등 무엇이든 질문해 보세요.", height=120, key="free_q_input_bet")
    if st.button("질문 보내기", key="free_q_send_bet", use_container_width=True):
        if not free_q_bet.strip():
            st.warning("질문을 입력해 주세요.")
        else:
            context = {"kind":"bet","score":score,"total":total,"goal":goal,"stake":stake}
            sys = "너는 한국어 학습 도우미야. 학생의 질문에 간결하고 정확하게 답하고, 필요하면 작은 예시와 함께 설명해."
            usr = f"퀴즈 맥락: {context}\n질문: {free_q_bet.strip()}"
            ans = gpt_chat([{"role":"system","content":sys},{"role":"user","content":usr}], max_tokens=700)
            st.success("답변을 가져왔어요.")
            st.markdown(ans)
    st.markdown('</div>', unsafe_allow_html=True)

# =========================
# 하단: 새로고침
# =========================
st.markdown("<hr style='border:none; border-top:1px dashed rgba(0,0,0,.08); margin: 16px 0 8px;'>", unsafe_allow_html=True)
st.markdown("<div style='text-align:right;'>", unsafe_allow_html=True)
if st.button("🔃새로고침", key="refresh_all"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

# 패널/컨테이너 닫기
st.markdown('</div></div>', unsafe_allow_html=True)  # panel-body, panel
st.markdown("</div>", unsafe_allow_html=True)        # container

# =========================
# ★ 랭킹과 동일하게: 타이틀 바 '각진 네모' 오버라이드 (마지막에 선언해야 적용)
# =========================
st.markdown("""
<style>
.panel{ background: transparent !important; border-radius: 0 !important; box-shadow: none !important; }
.panel-head{ border-radius: 0 !important; }
</style>
""", unsafe_allow_html=True)
