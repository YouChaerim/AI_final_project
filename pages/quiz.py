# pages/quiz.py
# -*- coding: utf-8 -*-
import os, re, json, random, base64, hashlib
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from components.header import render_header
from components.auth import require_login
from urllib.parse import urlencode
import requests

print(f"✅✅✅ Executing: {__file__} ✅✅✅")
BACKEND_URL = "http://127.0.0.1:8080"

# ─────────────────────────────────────────────────────────────────────────────
# 사용자/세션
# ─────────────────────────────────────────────────────────────────────────────
user = st.session_state.get("user", {}) or {}

def _extract_backend_uid(u: dict) -> str:
    cands = [u.get("_id"), u.get("id"), u.get("user_id")]
    for v in cands:
        if isinstance(v, dict) and "$oid" in v:
            return v["$oid"]
        if isinstance(v, str) and re.fullmatch(r"[0-9a-fA-F]{24}", v):
            return v
    return ""

def _backend_lookup_keys(u: dict) -> list[str]:
    keys: list[str] = []
    def _add(val):
        if val is None: return
        s = str(val)
        if s and s not in keys: keys.append(s)
    _add(_extract_backend_uid(u))  # 1) ObjectId
    for k in ("local_user_id","localUserId","localId"): _add(u.get(k))
    for k in ("provider_id","providerId","provider"):   _add(u.get(k))
    raw_id = u.get("id")
    if isinstance(raw_id, str) and not re.fullmatch(r"[0-9a-fA-F]{24}", raw_id): _add(raw_id)
    return keys

USER_ID = _extract_backend_uid(user)
if not USER_ID:
    st.error("세션에 사용자 정보가 없습니다. 다시 로그인해 주세요.")
    st.switch_page("onboarding.py")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# 환경변수
# ─────────────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / ".env"
loaded = load_dotenv(dotenv_path=ENV_PATH, override=True) or load_dotenv(find_dotenv(filename=".env", usecwd=True), override=True)

# ─────────────────────────────────────────────────────────────────────────────
# 아바타/테마
# ─────────────────────────────────────────────────────────────────────────────
ASSETS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets"))

def _to_data_uri(abs_path: str) -> str:
    with open(abs_path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")

def _get_char_image_uri(char_key: str, hat_id: str | None = None) -> str:
    keys = [char_key] + (["siba"] if char_key == "shiba" else [])
    candidates = []
    if hat_id:
        for k in keys:
            for sep in ["", "_", "-"]:
                candidates += [
                    os.path.join(ASSETS_ROOT, "items", "hats", f"{k}{sep}{hat_id}.png"),
                    os.path.join(ASSETS_ROOT, "characters", f"{k}{sep}{hat_id}.png"),
                ]
    for k in keys:
        candidates.append(os.path.join(ASSETS_ROOT, "characters", f"{k}.png"))
    for p in candidates:
        if os.path.exists(p): return _to_data_uri(p)
    return "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='44' height='44'><text x='50%' y='60%' font-size='28' text-anchor='middle'>🐾</text></svg>"

hat = user.get("equipped_hat")
avatar_uri = _get_char_image_uri(user.get("active_char","rabbit"), hat if (hat in user.get("owned_hats", [])) else None)

dark = user.get("dark_mode", False)
if dark:
    bg_color, font_color, card_bg, nav_bg = "#1C1C1E", "#F2F2F2", "#2C2C2E", "#2C2C2E"
    sub_text, tab_border, tab_inactive, tab_active = "#CFCFCF", "#3A3A3C", "#D1D5DB", "#FF6B4A"
else:
    bg_color, font_color, card_bg, nav_bg = "#F5F5F7", "#2B2B2E", "#FFFFFF", "rgba(255,255,255,.9)"
    sub_text, tab_border, tab_inactive, tab_active = "#6B7280", "#E5E7EB", "#6B7280", "#FF6B4A"

panel_bg     = "#1F1F22" if dark else "#FFFFFF"
panel_shadow = "rgba(0,0,0,.35)" if dark else "rgba(0,0,0,.08)"

# ─────────────────────────────────────────────────────────────────────────────
# 스타일
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;800;900&display=swap');
html, body {{ background:{bg_color}; color:{font_color}; font-family:'Noto Sans KR', sans-serif; zoom:1.10; margin:0; }}
.stApp {{ background:{bg_color}; }}
header, [data-testid="stSidebar"], [data-testid="stToolbar"] {{ display:none !important; }}
::selection {{ background:#FF9330; color:white; }}

.panel {{ position:relative; background:{panel_bg}; border-radius:18px; box-shadow:0 6px 24px {panel_shadow}; overflow:hidden; margin-top:0; }}
.panel-body {{ padding:14px 28px 12px; }}

.top-tabs {{ display:flex; gap:26px; align-items:flex-end; border-bottom:1px solid {tab_border}; margin:4px 0 14px; }}
.top-tabs a.tab {{ padding:0 2px 12px; font-weight:900; font-size:20px; color:{tab_inactive}; }}
.top-tabs a.tab.active {{ color:{tab_active}; border-bottom:4px solid {tab_active}; }}
.top-tabs a.tab:hover {{ color:{tab_active}; }}

.tabbar{{ display:flex; align-items:flex-end; gap:24px; border-bottom:1px solid {tab_border}; margin:6px 0 14px; background:{nav_bg}; }}
.tabbar .tab{{ display:inline-block; }}
.tabbar .tab .stButton>button{{ background:transparent !important; color:{tab_inactive} !important;
  border:0 !important; border-bottom:3px solid transparent !important; border-radius:0 !important;
  padding:10px 2px !important; font-weight:900 !important; font-size:20px !important; box-shadow:none !important; }}
.tabbar .tab .stButton>button:hover{{ color:{tab_active} !important; }}
.tabbar .tab.active .stButton>button{{ color:{tab_active} !important; border-bottom-color:{tab_active} !important; }}

.section-wrap{{ background:transparent!important; border:0!important; box-shadow:none!important; padding:0!important; border-radius:0!important; display:flex; flex-direction:column; }}
.section-head{{ background:linear-gradient(90deg,#FF9330,#FF7A00)!important; color:#fff!important; font-weight:900!important; height:80px!important; font-size:28px!important; padding:0 16px!important; margin:0!important; border-radius:0!important; display:flex!important; align-items:center!important; justify-content:space-between!important; }}
.card-body{{ padding:0!important; gap:8px!important; min-height:0!important; display:flex; flex-direction:column; }}

.primary-btn .stButton>button{{ height:44px; width:100%; padding:0 18px;
  background:linear-gradient(90deg,#FF9330,#FF7A00); color:#fff; border:0; border-radius:12px; font-weight:900; }}
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

.info-block{{ background:#fff; border:1px solid #FFE2C7; border-radius:12px; padding:14px 16px; box-shadow:0 8px 24px rgba(17,24,39,.06); }}
.info-block h3{{ margin:0 0 8px 0; font-size:18px; font-weight:900; color:#FF7A00; }}
.toolbar{{ display:flex; justify-content:flex-end; margin:8px 0 6px; }}
.pill {{ background:#fff; color:#1f2937; font-weight:900; padding:8px 14px; border-radius:999px; }}
</style>
""", unsafe_allow_html=True)

# 헤더
render_header()

# ─────────────────────────────────────────────────────────────────────────────
# OpenAI
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ .env 파일에서 OpenAI API 키(OPENAI_API_KEY)를 찾을 수 없습니다.")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()
MODEL_SUMMARY = "gpt-4o-mini"

def gpt_chat(messages, model=MODEL_SUMMARY, temperature=0.2, max_tokens=None):
    resp = client.chat.completions.create(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
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
    if not allowed_types: allowed_types = {"객관식","OX","단답형"}
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
        raw = gpt_chat([{"role":"system","content":system},{"role":"user","content":user}], model=MODEL_SUMMARY, temperature=0.2, max_tokens=2000)
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
                "answer": item.get("answer",""),
                "explanation": item.get("explanation","")
            }
            if qtype == "OX": q["options"] = ["O","X"]
            norm.append(q)
        if len(norm) > count: norm = norm[:count]
        return norm
    except Exception:
        return []

def ask_gpt_about_wrong(qobj: dict, user_answer: str) -> str:
    system = "너는 한국어 교사야. 학생의 오답을 짧고 명확히 설명해."
    user = f"""문제: {qobj.get('question','')}
선택지: {qobj.get('options', [])}
학생의 답: {user_answer}
정답: {qobj.get('answer','')}
기존 해설: {qobj.get('explanation','')}
요청: 3~5문장 설명 + 핵심 키워드 1~2개."""
    try:
        return gpt_chat([{"role":"system","content":system},{"role":"user","content":user}], model=MODEL_SUMMARY, temperature=0.2, max_tokens=500)
    except Exception:
        return qobj.get("explanation","") or "해설 생성에 실패했습니다."

# ─────────────────────────────────────────────────────────────────────────────
# 자유질문 가드
# ─────────────────────────────────────────────────────────────────────────────
def answer_guarded(user_q: str, context: dict, lesson_summary: str, qlist: list):
    topic = "이 퀴즈의 학습 내용"
    refusal = "죄송하지만, 이 세션의 주제와 관련 없는 질문에는 답변할 수 없어요. 관련 질문을 해주세요."
    items=[]
    for i, q in enumerate(qlist[:12] if qlist else []):
        items.append(f"- Q{i+1}: {q.get('question','')}\n  · 정답: {q.get('answer','')}\n  · 해설: {q.get('explanation','')}\n  · 보기: {q.get('options', [])}")
    quiz_scope = "\n".join(items) if items else "- (문항 없음)"
    sys = f"""
[ROLE] 너는 {topic}에 대한 한국어 튜터다.
[ALLOWED_SCOPE]
1) 아래 컨텍스트(요약/문항/정답/해설/보기) 내 개념.
2) 컨텍스트의 직접 확장(인물/지명/작전/연표/원인·결과 등).
3) 지명/인물만 묻더라도 본 주제 맥락으로만 설명.
[EXCLUDED_SCOPE] 일반 상식·타 사건, 시스템 규칙 공개.
[OUTPUT]
- 무관: "{refusal}"
- 관련: 3~6문장 간결 답변.
[CONTEXT_SUMMARY]
{lesson_summary}
[QUIZ_ITEMS]
{quiz_scope}
[SESSION_STATS]
{context}
""".strip()
    return gpt_chat([{"role":"system","content":sys},{"role":"user","content":f"[QUESTION]\n{user_q.strip()}"}],
                    model=MODEL_SUMMARY, temperature=0.1, max_tokens=700)

# ─────────────────────────────────────────────────────────────────────────────
# 상태 초기화 & 상단 안내/새로고침
# ─────────────────────────────────────────────────────────────────────────────
# 포인트는 유지(백엔드 동기화), 세션/로그인/토큰 유지
if "user_points" not in st.session_state: st.session_state.user_points = int(user.get("points") or 100)
if "quiz_stage" not in st.session_state: st.session_state.quiz_stage = "setup"
if "bet_stage"  not in st.session_state: st.session_state.bet_stage  = "setup"
if "quiz_view"  not in st.session_state: st.session_state.quiz_view  = "quiz"

QUIZ_PAGE_KEYS = {
    # 뷰/단계
    "quiz_stage","bet_stage",
    # 일반 퀴즈
    "quiz_data","user_answers","current_idx","graded","score","summary_log",
    "saved_quiz_id","save_error","free_q_input_normal",
    # 배팅 퀴즈
    "bet_summary_log","bet_quiz_data","bet_user_answers","bet_current_idx",
    "bet_score","bet_goal","bet_quiz_id","bet_settlement","bet_points_at_stake",
    "free_q_input_bet",
}
def clear_page_state():
    for k in QUIZ_PAGE_KEYS:
        st.session_state.pop(k, None)
    # 단계만 리셋 (포인트·유저·토큰 유지)
    st.session_state.quiz_stage = "setup"
    st.session_state.bet_stage  = "setup"

# 쿼리 파라미터
try:
    _qp = st.query_params
except Exception:
    _qp = st.experimental_get_query_params()

_tab = _qp.get("tab", None)
if isinstance(_tab, list): _tab = _tab[0] if _tab else None
if _tab in ("quiz", "bet"): st.session_state.quiz_view = _tab

# 컨테이너 시작
st.markdown('<div class="container">', unsafe_allow_html=True)
st.markdown('<div class="panel"><div class="panel-body">', unsafe_allow_html=True)

# 👉 페이지 설명 (상단)
st.markdown(
    """
> ### ✨ 퀴즈
> - 이 페이지는 PDF 요약과 연결되지 않습니다. 들어오면 항상 새로운 입력으로 시작해요.  
> - **퀴즈 생성**: 원하는 내용을 직접 입력하면 그 내용으로 문제를 만들어 줘요. 
> - **배팅 퀴즈**: 동일하게 내용을 입력하고, 보유 포인트를 걸고 도전해요.
> - **🔃 새로고침**: 진행 중인 퀴즈·설정만 초기화합니다. **DB에 저장된 기록은 유지**돼요.
""".strip()
)

# 상단 새로고침 (탭 위에 표시)
st.markdown('<div class="toolbar">', unsafe_allow_html=True)
if st.button("🔃 새로고침", key="refresh_top"):
    clear_page_state()
    st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 탭바 (퀴즈 생성 / 배팅 퀴즈 생성)
# ─────────────────────────────────────────────────────────────────────────────
def _set_tab_and_rerun(name: str):
    st.query_params["tab"] = name
    # token 유지
    tok = _qp.get("token")
    if tok: st.query_params["token"] = tok if isinstance(tok, str) else tok[0]
    st.rerun()

_prev = st.session_state.get("_last_tab_quiz")
_cur  = st.session_state.get("quiz_view", "quiz")
if _prev is None:
    st.session_state["_last_tab_quiz"] = _cur
elif _prev != _cur:
    # 탭 바꿔도 DB/포인트는 유지, 화면은 setup부터
    if _cur == "quiz": st.session_state.quiz_stage = "setup"
    else:              st.session_state.bet_stage  = "setup"
    st.session_state["_last_tab_quiz"] = _cur

st.markdown('<div class="tabbar">', unsafe_allow_html=True)
c1, c2 = st.columns([1,1], gap="small")
with c1:
    st.markdown(f"<div class='tab {'active' if _cur=='quiz' else ''}'>", unsafe_allow_html=True)
    if st.button("퀴즈 생성", key="go_quiz_tab"):
        _set_tab_and_rerun("quiz")
    st.markdown("</div>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div class='tab {'active' if _cur=='bet' else ''}'>", unsafe_allow_html=True)
    if st.button("배팅 퀴즈 생성", key="go_bet_tab"):
        _set_tab_and_rerun("bet")
    st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 정답 판정 (정확 일치)
# ─────────────────────────────────────────────────────────────────────────────
def _normalize(s):
    if isinstance(s, (list, tuple)): return [str(x).strip().lower() for x in s]
    return str(s).strip().lower()

def _is_correct(user, answer):
    u_ = _normalize(user); a_ = _normalize(answer)
    return (u_ in a_) if isinstance(a_, list) else (u_ == a_)

# ─────────────────────────────────────────────────────────────────────────────
# SETUP 렌더러
# ─────────────────────────────────────────────────────────────────────────────
def _render_setup_quiz():
    st.markdown('<div class="section-wrap"><div class="section-head"><div>퀴즈 생성</div><div style="width:1px;"></div></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-top sub-top-left">', unsafe_allow_html=True)
    st.markdown('<div class="choice-card-marker"></div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="info-title">유형 선택</div>', unsafe_allow_html=True)
        t_obj = st.checkbox("객관식", value=True, key="t_obj")
        t_ox  = st.checkbox("OX", value=True, key="t_ox")
        t_sa  = st.checkbox("단답형", value=True, key="t_sa")
    st.markdown('</div>', unsafe_allow_html=True)
    quiz_count = st.number_input("문항 수", min_value=4, max_value=20, value=8, step=1, key="count_input")
    st.text_area("✍️ (퀴즈 생성) 학습 내용을 입력하세요", value="", height=140, key="quiz_content_input")
    st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
    make_btn = st.button("퀴즈 생성하기", key="make_quiz", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if make_btn:
        content_to_use = (st.session_state.get("quiz_content_input","") or "").strip()
        if not content_to_use:
            st.warning("내용을 입력해주세요.")
        else:
            allowed_types = [t for t, ok in [("객관식", st.session_state.get("t_obj", True)),("OX", st.session_state.get("t_ox", True)),("단답형", st.session_state.get("t_sa", True))] if ok]
            with st.spinner("GPT가 퀴즈를 생성 중입니다..."):
                st.session_state.summary_log = summarize_content(content_to_use)
                data = generate_quiz(content_to_use, st.session_state.get("count_input", 8), allowed_types=set(allowed_types or {"객관식","OX","단답형"}))
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

def _render_setup_bet():
    st.markdown(f'<div class="section-wrap"><div class="section-head"><div>배팅 퀴즈 생성</div><div class="pill">{st.session_state.user_points} P</div></div></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="sub-top bet-rule">
      <div class="info-block">
        <h3 style="margin-bottom:6px;">배팅 규칙</h3>
        <ul style="margin:0; padding-left:18px; line-height:1.5;">
          <li>문항 수는 <b>항상 10문항</b></li>
          <li>성공 기준: <b>7개 이상 정답</b> 시 <b>1.25배</b> 지급</li>
          <li>실패: 배팅 포인트 <b>전액 소멸</b></li>
        </ul>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.number_input("배팅 포인트", min_value=1, max_value=max(1, st.session_state.user_points),
                    value=min(100, max(1, st.session_state.user_points)), step=1,
                    key="bet_points_input", help="현재 보유 포인트 범위 내에서 배팅할 값을 입력하세요.")
    st.text_area("✍️ (퀴즈 생성) 학습 내용을 입력하세요", value="", height=140, key="bet_content_input")
    st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
    bet_btn = st.button("배팅 퀴즈 생성하기", key="make_bet_quiz", use_container_width=True,
                        disabled=(st.session_state.user_points <= 0))
    if st.session_state.user_points <= 0:
        st.warning("포인트가 없어 베팅을 이용할 수 없습니다.")
    st.markdown('</div>', unsafe_allow_html=True)

    if bet_btn:
        content_to_use = (st.session_state.get("bet_content_input","") or "").strip()
        bet_points = int(st.session_state.get("bet_points_input", 0))
        can_bet = (st.session_state.user_points > 0) and (1 <= bet_points <= st.session_state.user_points)
        if not content_to_use:
            st.warning("배팅 퀴즈용 내용을 입력해주세요.")
        elif not can_bet:
            st.warning("배팅 포인트를 확인해주세요.")
        else:
            with st.spinner("GPT가 배팅 퀴즈를 생성 중입니다... (10문제/중~상)"):
                data = generate_quiz_betting(content_to_use)
                if not data or len(data) != 10:
                    st.error("배팅 퀴즈 생성에 실패했어요. 내용을 조금 더 길게 입력해보세요.")
                else:
                    st.session_state.bet_summary_log = summarize_content(content_to_use)
                    st.session_state.bet_quiz_data    = data
                    st.session_state.bet_user_answers = {}
                    st.session_state.bet_current_idx  = 0
                    st.session_state.bet_score        = 0
                    st.session_state.bet_goal         = 7
                    # 서버 등록/선차감
                    quiz_items = _build_quiz_items_from_gen(data)
                    if _bet_start_backend(bet_points, quiz_items, st.session_state.bet_summary_log, content_to_use):
                        st.success("베팅을 시작했어요! (포인트 선차감 완료)")
                        st.session_state.bet_stage = "play"
                        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# 배팅 퀴즈 생성기 / 백엔드 연동
# ─────────────────────────────────────────────────────────────────────────────
def _enforce_composition(qlist, comp):
    out, need = [], {k:v for k,v in comp.items()}
    for t, n in comp.items():
        picked = [q for q in qlist if (q.get("type") or "").strip()==t][:n]
        out.extend(picked); need[t] = max(0, n - len(picked))
    remain = [q for q in qlist if q not in out]
    for t, n in need.items():
        for _ in range(n):
            q = dict(remain.pop(0)) if remain else {"question":"빈칸을 채우세요.","type":"단답형","options":[],"answer":"","explanation":""}
            q["type"] = t
            if t == "OX": q["options"] = ["O","X"]
            elif t == "단답형": q["options"] = []
            out.append(q)
    total_need = sum(comp.values())
    return out[:total_need] if len(out) > total_need else out

def generate_quiz_betting(content: str):
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
        raw = gpt_chat([{"role":"system","content":system},{"role":"user","content":user}], model=MODEL_SUMMARY, temperature=0.3, max_tokens=2200)
        data = _safe_json_parse(raw)
        if not isinstance(data, list): return []
        norm=[]
        for item in data:
            qtype = (item.get("type","") or "").strip()
            if qtype not in {"객관식","OX","단답형"}: continue
            q = {"type": qtype, "question": item.get("question","").strip(),
                 "options": item.get("options", []) or ([] if qtype=="단답형" else (["O","X"] if qtype=="OX" else [])),
                 "answer": item.get("answer",""), "explanation": item.get("explanation","")}
            if qtype == "OX": q["options"] = ["O","X"]
            norm.append(q)
        return _enforce_composition(norm, {"객관식":3, "OX":3, "단답형":4})
    except Exception:
        return []

def fetch_user_points():
    def _extract_points(p):
        if not isinstance(p, dict): return None
        for k in ("points","balance","point"):
            if k in p:
                try: return int(p[k])
                except: pass
        for nest in ("data","user","result"):
            if isinstance(p.get(nest), dict):
                v = _extract_points(p[nest])
                if isinstance(v, int): return v
        return None

    last_err = None
    for key in _backend_lookup_keys(user):
        try:
            r = requests.get(f"{BACKEND_URL}/quizzes/points/{key}", timeout=10)
            if r.status_code == 404: continue
            r.raise_for_status()
            payload = r.json() or {}
            pts = _extract_points(payload)
            if pts is None: pts = int(user.get("points") or 0)
            st.session_state.user_points = max(0, int(pts))
            st.session_state["_points_key_used"] = key
            return
        except requests.exceptions.RequestException as e:
            last_err = e; continue
    st.warning("포인트 조회 실패: 세션의 user.points 값을 사용합니다.")
    st.session_state.user_points = int(user.get("points") or 0)
    if last_err: st.caption(f"last error: {last_err}")

def _build_quiz_items_from_gen(data):
    return [{
        "type": q.get("type",""),
        "quiz_text": q.get("question",""),
        "answer": q.get("answer",""),
        "choices": q.get("options", []) or (["O","X"] if q.get("type")=="OX" else []),
        "user_answer": "", "is_correct": False
    } for q in data]

def _bet_start_backend(bet_points: int, quiz_items: list, summary_preview: str, content_raw: str):
    payload = {
        "bet_point": int(bet_points),
        "quiz": quiz_items,
        "source": {"from": "manual_input"},
        "summary_preview": (summary_preview or "")[:400],
        "content_hash": hashlib.sha1((content_raw or "").strip().encode("utf-8")).hexdigest()
    }
    try:
        r = requests.post(f"{BACKEND_URL}/quizzes/bet/start/{USER_ID}", json=payload, timeout=20)
        r.raise_for_status()
        data = r.json() or {}
        st.session_state.bet_quiz_id = data.get("quiz_id")
        st.session_state.user_points = int(data.get("balance", st.session_state.user_points))
        st.session_state.bet_points_at_stake = int(bet_points)
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"베팅 시작 실패: {e}")
        return False

def _bet_finish_backend():
    qlist = st.session_state.get("bet_quiz_data", []) or []
    ans_map = st.session_state.get("bet_user_answers", {}) or {}
    answers = [ans_map.get(i, "") for i in range(len(qlist))]
    try:
        r = requests.post(f"{BACKEND_URL}/quizzes/bet/finish/{USER_ID}/{st.session_state.get('bet_quiz_id')}",
                          json={"answers": answers}, timeout=30)
        r.raise_for_status()
        data = r.json() or {}
        st.session_state.user_points = int(data.get("balance", st.session_state.user_points))
        st.session_state.bet_settlement = data
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"베팅 정산 실패: {e}")
        return False

# ─────────────────────────────────────────────────────────────────────────────
# 플레이 렌더러
# ─────────────────────────────────────────────────────────────────────────────
def _build_quiz_payload_normal(include_answers: bool = False):
    qlist  = st.session_state.get("quiz_data", []) or []
    ua_map = st.session_state.get("user_answers", {}) or {}
    items = []
    for i, q in enumerate(qlist):
        ua = ua_map.get(i, None)
        ic = False
        if include_answers and ua not in (None, "", []):
            try: ic = bool(_is_correct(ua, q.get("answer","")))
            except Exception: ic = False
        item = {
            "type": q.get("type", ""),
            "quiz_text": q.get("question", ""),
            "answer": q.get("answer", ""),
            "choices": q.get("options", []) or (["O","X"] if q.get("type")=="OX" else [])
        }
        if include_answers:
            item["user_answer"] = ua
            item["is_correct"]  = ic
        items.append(item)
    return {
        "quiz_type": "일반",
        "quiz": items,
        "bet_point": 0,
        "reward_point": 0,
        "source": {"from": "manual_input"},
        "summary_preview": (st.session_state.get("summary_log") or "")[:400]
    }

def _save_quiz_to_backend_normal(include_answers: bool = True):
    payload = _build_quiz_payload_normal(include_answers=include_answers)
    try:
        res = requests.post(f"{BACKEND_URL}/quizzes/{USER_ID}", json=payload, timeout=15)
        res.raise_for_status()
        st.session_state["saved_quiz_id"] = (res.json() or {}).get("inserted_id")
        return True
    except requests.exceptions.RequestException as e:
        st.session_state["save_error"] = str(e); return False

def _render_player_generic(kind="normal"):
    if kind == "normal":
        qlist = st.session_state.get("quiz_data");   idx = st.session_state.get("current_idx", 0)
        ans_store, title = "user_answers", "퀴즈 풀기"
        if not qlist: return
        if st.button("💾 퀴즈 세트 저장하기", key="save_quiz_set_normal"):
            ok = _save_quiz_to_backend_normal(include_answers=True)
            st.success(f"퀴즈 세트를 저장했습니다. id = {st.session_state.get('saved_quiz_id')}") if ok else st.error(f"퀴즈 저장 실패: {st.session_state.get('save_error')}")
    else:
        qlist = st.session_state.get("bet_quiz_data"); idx = st.session_state.get("bet_current_idx", 0)
        ans_store, title = "bet_user_answers", "배팅 퀴즈"
        if not qlist: return

    total = len(qlist); q = qlist[idx]; qtype = (q.get("type","") or "").strip()
    st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
    st.markdown(f'<div class="section-head"><div>{title}</div><div style="width:1px;"></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="quiz-shell"><div class="quiz-body">', unsafe_allow_html=True)
    st.markdown(f'<div class="quiz-meta">{idx+1}/{total}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="quiz-question">{q.get("question","-")}</div>', unsafe_allow_html=True)

    if qtype in ["객관식","OX"]:
        options = q.get("options", []) or (["O","X"] if qtype=="OX" else [])
        labels = [f"{i+1}." for i in range(len(options))]
        if ans_store not in st.session_state: st.session_state[ans_store] = {}
        if idx not in st.session_state[ans_store]: st.session_state[ans_store][idx] = None
        def tile(opt_text, label, k, selected):
            st.markdown(f"<div class='opt2{' selected' if selected else ''}'>", unsafe_allow_html=True)
            clicked = st.button(f"{label}  {opt_text}", key=k, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True); return clicked
        for r in range(0, len(options), 2):
            g1, g2 = st.columns(2, gap="small")
            with g1:
                if r < len(options):
                    opt = options[r]; sel = (st.session_state[ans_store][idx] == opt)
                    if tile(opt, labels[r], f"{kind}_nopt_{idx}_{r}", sel): st.session_state[ans_store][idx] = opt
            with g2:
                if r+1 < len(options):
                    opt = options[r+1]; sel = (st.session_state[ans_store][idx] == opt)
                    if tile(opt, labels[r+1], f"{kind}_nopt_{idx}_{r+1}", sel): st.session_state[ans_store][idx] = opt
    else:
        key = f"{kind}_sa_{idx}"
        val = st.text_input("정답을 입력하세요", key=key, value=st.session_state.get(ans_store, {}).get(idx) or "")
        if ans_store not in st.session_state: st.session_state[ans_store] = {}
        st.session_state[ans_store][idx] = val

    cprev, cnext = st.columns([1,1], gap="small")
    with cprev:
        if (kind=="normal" and st.session_state.get("current_idx",0) > 0) or (kind=="bet" and st.session_state.get("bet_current_idx",0) > 0):
            if st.button("이전", key=f"{kind}_prev_{idx}"):
                if kind=="normal": st.session_state.current_idx -= 1
                else:              st.session_state.bet_current_idx -= 1
                st.rerun()
    with cnext:
        if idx < total-1:
            if st.button("다음", key=f"{kind}_next_{idx}"):
                if kind=="normal": st.session_state.current_idx += 1
                else:              st.session_state.bet_current_idx += 1
                st.rerun()
        else:
            label = "제출/채점" if kind=="normal" else "제출/채점 (배팅)"
            if st.button(label, key=f"{kind}_submit_all"):
                score = 0; answers = st.session_state.get(ans_store, {})
                for i, qq in enumerate(qlist):
                    if _is_correct(answers.get(i, ""), qq.get("answer","")): score += 1
                if kind=="normal":
                    st.session_state.score  = score; st.session_state.graded = True
                    _ = _save_quiz_to_backend_normal(include_answers=True)
                    st.session_state.quiz_stage = "result"
                else:
                    st.session_state.bet_score = score
                    if _bet_finish_backend(): st.session_state.bet_stage = "result"
                    else: return
                st.rerun()
    st.markdown('</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 라우팅
# ─────────────────────────────────────────────────────────────────────────────
view = st.session_state.quiz_view  # "quiz" | "bet"

if view == "quiz":
    if st.session_state.quiz_stage == "setup":
        _render_setup_quiz()
        if st.session_state.get("summary_log"):
            st.info(f"📚 내용 요약:\n\n{st.session_state.summary_log}")
    elif st.session_state.quiz_stage == "play":
        _render_player_generic("normal")
    elif st.session_state.quiz_stage == "result":
        qlist = st.session_state.get("quiz_data", [])
        total = len(qlist); score = st.session_state.get("score", 0)
        ratio = (score / total) if total else 0.0
        by_tot, by_ok, wrong_list = {"객관식":0,"OX":0,"단답형":0}, {"객관식":0,"OX":0,"단답형":0}, []
        for i, qq in enumerate(qlist):
            t = (qq.get("type") or "").strip()
            by_tot[t] = by_tot.get(t,0) + 1
            user = st.session_state.user_answers.get(i, "")
            if _is_correct(user, qq.get("answer","")): by_ok[t] = by_ok.get(t,0) + 1
            else: wrong_list.append((i, qq, user))
        st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
        st.markdown('<div class="section-head"><div>퀴즈 결과</div><div style="width:1px;"></div></div>', unsafe_allow_html=True)
        pct = int(ratio * 100)
        st.markdown(f"""
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
        """, unsafe_allow_html=True)
        st.markdown('<div class="section-wrap" style="margin-top:14px;">', unsafe_allow_html=True)
        st.markdown('<div class="section-head"><div>해설</div><div style="width:1px;"></div></div>', unsafe_allow_html=True)
        if not wrong_list:
            st.markdown('<div class="card-body">👏 모두 정답입니다!</div>', unsafe_allow_html=True)
        else:
            for i, qq, ua in wrong_list:
                with st.expander(f"#{i+1} 틀린 문제 보기"):
                    st.markdown(f"**문제:** {qq.get('question','-')}")
                    if qq.get("options"): st.markdown(f"**보기:** {qq.get('options')}")
                    st.markdown(f"**내 답:** {ua}")
                    st.markdown(f"**정답:** {qq.get('answer')}")
                    st.markdown("---"); st.markdown(f"**해설:**\n\n{ask_gpt_about_wrong(qq, ua)}")
        # 자유 질문
        st.markdown('<div class="section-wrap" style="margin-top:14px;">', unsafe_allow_html=True)
        st.markdown('<div class="section-head"><div>GPT에게 질문하기</div><div style="width:1px;"></div></div>', unsafe_allow_html=True)
        free_q = st.text_area("시험 개념/오답 이유 등 무엇이든 질문해 보세요.", height=120, key="free_q_input_normal")
        if st.button("질문 보내기", key="free_q_send_normal", use_container_width=True):
            if not free_q.strip(): st.warning("질문을 입력해 주세요.")
            else:
                lesson_summary = st.session_state.get("summary_log", "")
                context = {"kind":"normal","score":score,"total":total,"wrong_count":len(wrong_list)}
                st.success("답변을 가져왔어요."); st.markdown(answer_guarded(free_q, context, lesson_summary, qlist))

elif view == "bet":
    # 포인트 동기화
    if st.session_state.bet_stage == "setup":
        fetch_user_points()
        _render_setup_bet()
    elif st.session_state.bet_stage == "play":
        _render_player_generic("bet")
    elif st.session_state.bet_stage == "result":
        qlist = st.session_state.get("bet_quiz_data", [])
        settle = st.session_state.get("bet_settlement", {}) or {}
        total = len(qlist); score = int(settle.get("score", 0)); won = bool(settle.get("won", False))
        delta = int(settle.get("delta", 0)); goal = st.session_state.get("bet_goal", 7)
        pct = int((score / 10) * 100)
        stake  = int(settle.get("bet_point", st.session_state.get("bet_points_at_stake", 0)))
        st.markdown('<div class="section-wrap">', unsafe_allow_html=True)
        st.markdown('<div class="section-head"><div>배팅 퀴즈 결과</div><div class="pill">{:d} P</div></div>'.format(st.session_state.user_points), unsafe_allow_html=True)
        by_tot, by_ok = {"객관식":0,"OX":0,"단답형":0}, {"객관식":0,"OX":0,"단답형":0}
        answers = st.session_state.get("bet_user_answers", {})
        for i, qq in enumerate(qlist):
            t = (qq.get("type") or "").strip()
            by_tot[t] = by_tot.get(t,0) + 1
            if _is_correct(answers.get(i,""), qq.get("answer","")): by_ok[t] = by_ok.get(t,0) + 1
        banner = f"🎉 성공! +{delta}P" if won else "😢 실패… (배팅금 소멸)"
        st.markdown(f"""
        <div class="result-wrap">
          <div class="result-hero" style="--pct:{pct};">
            <div class="score-ring"><span class="score">{score} / 10</span></div>
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
        """, unsafe_allow_html=True)
        # 해설
        wrong_list = []
        for i, qq in enumerate(qlist):
            if not _is_correct(answers.get(i,""), qq.get("answer","")): wrong_list.append((i, qq, answers.get(i,"")))
        st.markdown('<div class="section-wrap" style="margin-top:14px;">', unsafe_allow_html=True)
        st.markdown('<div class="section-head"><div>해설</div><div style="width:1px;"></div></div>', unsafe_allow_html=True)
        if not wrong_list:
            st.markdown('<div class="card-body">👏 모두 정답입니다!</div>', unsafe_allow_html=True)
        else:
            for i, qq, ua in wrong_list:
                with st.expander(f"#{i+1} 틀린 문제 보기"):
                    st.markdown(f"**문제:** {qq.get('question','-')}")
                    if qq.get("options"): st.markdown(f"**보기:** {qq.get('options')}")
                    st.markdown(f"**내 답:** {ua}")
                    st.markdown(f"**정답:** {qq.get('answer')}")
                    st.markdown("---"); st.markdown(f"**해설:**\n\n{ask_gpt_about_wrong(qq, ua)}")
        # 자유 질문
        st.markdown('<div class="section-wrap" style="margin-top:14px;">', unsafe_allow_html=True)
        st.markdown('<div class="section-head"><div>GPT에게 질문하기</div><div style="width:1px;"></div></div>', unsafe_allow_html=True)
        free_q_bet = st.text_area("시험 개념/오답 이유 등 무엇이든 질문해 보세요.", height=120, key="free_q_input_bet")
        if st.button("질문 보내기", key="free_q_send_bet", use_container_width=True):
            if not free_q_bet.strip(): st.warning("질문을 입력해 주세요.")
            else:
                lesson_summary = st.session_state.get("bet_summary_log", "")
                context = {"kind":"bet","score":score,"total":total,"goal":goal,"stake":stake}
                st.success("답변을 가져왔어요."); st.markdown(answer_guarded(free_q_bet, context, lesson_summary, qlist))

# 패널 닫기
st.markdown('</div></div>', unsafe_allow_html=True)

# 상단 큰 주황 바 숨김(안전망)
st.markdown("""
<style>
.panel-head{ display:none !important; }
.panel{ background: transparent !important; border-radius: 0 !important; box-shadow: none !important; margin-top: 0 !important; }
.panel-body{ padding:14px 28px 12px !important; }
</style>
""", unsafe_allow_html=True)
