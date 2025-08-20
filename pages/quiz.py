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
# 스타일
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;800;900&display=swap');
html, body { background:#F5F5F7; color:#2B2B2E; font-family:'Noto Sans KR', sans-serif; zoom:1.10; margin:0; }
.stApp { background:#F5F5F7; }
.block-container { padding-top:0 !important; }
header, [data-testid="stToolbar"] { display:none !important; }

/* 헤더 (랭킹/상점 페이지와 규격 통일) */
.container { max-width:1200px; margin:auto; padding:4px 40px 24px; }
.top-nav {
  display:flex; justify-content:space-between; align-items:center;
  padding:12px 0; margin-top:40px !important; background:rgba(255,255,255,.9);
  box-shadow:0 2px 4px rgba(0,0,0,.05); border-radius:12px;
}
.nav-left { display:flex; align-items:center; gap:60px; }
.top-nav .nav-left > div:first-child a { color:#000 !important; font-size:28px; font-weight:900; text-decoration:none !important; }
.nav-menu { display:flex; gap:36px; font-size:18px; font-weight:700; }
.nav-menu div a { color:#000 !important; transition:.2s; text-decoration:none !important; }
.nav-menu div:hover a { color:#FF9330 !important; }
.profile-group { display:flex; gap:16px; align-items:center; margin-right:12px; }
.profile-icon {
  width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#DDEFFF,#F8FBFF);
  overflow:hidden;display:flex;align-items:center;justify-content:center;box-shadow:0 1px 2px rgba(0,0,0,.06);
}

/* 상단 주황 히어로 (큰 박스) */
.hero {
  background:linear-gradient(90deg,#FF9330,#FF7A00);
  color:#fff; font-weight:900; font-size:38px; text-align:center;
  padding:22px 20px; border-radius:18px; box-shadow:0 6px 24px rgba(0,0,0,.08); margin-top:18px;
}

/* 양쪽 섹션 카드 */
.grid { display:grid; grid-template-columns: 1fr 1fr; gap:22px; margin-top:18px; }
.card { background:#fff; border:1px solid rgba(0,0,0,.06); border-radius:18px; box-shadow:0 12px 30px rgba(17,24,39,.06); padding:18px; }

/* 섹션 타이틀(주황 바) */
.section-title {
  background:linear-gradient(90deg,#FF9330,#FF7A00);
  border-radius:20px; color:#fff; font-weight:900; font-size:20px;
  padding:12px 16px; display:flex; align-items:center; justify-content:space-between;
}
.section-title .right-badge {
  background:rgba(255,255,255,.96); color:#1F2937; font-weight:900; border-radius:999px; padding:6px 12px; box-shadow:0 1px 2px rgba(0,0,0,.08);
}

/* 소제목/인풋 */
.subtle { color:#6B7280; font-weight:800; margin:16px 0 6px; }
.rule { display:flex; align-items:center; gap:10px; margin:6px 0; }
.rule .dot { width:8px;height:8px;border-radius:999px; display:inline-block; }
.dot.green { background:#10B981; } .dot.blue { background:#3B82F6; } .dot.red { background:#EF4444; }

/* 퀴즈 플레이어 */
.quiz-shell{ width:100%; background:#fff; border:2px solid #FFA65A; border-radius:10px; box-shadow:0 8px 24px rgba(17,24,39,.08); overflow:hidden; }
.quiz-body{ padding:22px 24px 26px; }
.quiz-meta{ font-weight:800; color:#FF7A00; margin-bottom:8px; }
.quiz-question{ font-size:20px; font-weight:900; margin:6px 0 14px; }

/* 옵션 버튼 */
.opt2 .stButton>button{ width:100%; border:1.5px solid #EFEFEF; background:#fff; border-radius:12px; padding:14px 16px; text-align:left; font-weight:700; box-shadow:0 1px 2px rgba(0,0,0,0.03); }
.opt2 .stButton>button:hover{ border-color:#FFD2A8; }
.opt2.selected .stButton>button{ border-color:#FFB066; box-shadow:0 0 0 2px rgba(255,138,0,.15) inset; background:linear-gradient(90deg,#FF9330,#FF7A00); color:#fff; }

/* 버튼 (기본/주황) */
.primary-btn .stButton>button{ height:48px; width:100%; padding:0 18px; background:#fff; color:#FF7A00; border:2px solid #FF7A00; border-radius:12px; font-weight:900; }
.primary-btn .stButton>button:disabled{ opacity:.45; cursor:not-allowed; }
.primary-btn.orange .stButton>button{ background:linear-gradient(90deg,#FF9330,#FF7A00); color:#fff; border:0; }

/* 결과 카드 */
.result-wrap{ background:#fff;border:1px solid #F1E6D8;border-radius:18px; box-shadow:0 18px 48px rgba(17,24,39,.06);padding:20px; }
.result-hero{display:flex;flex-direction:column;align-items:center;gap:8px;margin:8px 0 16px;}
.score-ring{width:140px;height:140px;border-radius:999px;background:conic-gradient(#FF9330 calc(var(--pct,0)*1%), #FFE1C2 0);display:flex;align-items:center;justify-content:center; box-shadow:0 6px 18px rgba(255,138,0,.18);}
.score-ring .score{background:#fff;border-radius:999px;padding:14px 20px;font-weight:900;font-size:24px;}
.chip-row{display:flex;gap:12px;justify-content:center;margin:4px 0 12px;}
.chip{display:flex;flex-direction:column;align-items:center;justify-content:center;min-width:110px;padding:10px 12px;border-radius:12px;background:#F6FFFA;border:1px solid #BFEAD4;font-weight:800}
.chip.red{background:#FFF6F6;border-color:#F7C2C2}
.meter{height:10px;border-radius:999px;background:#F2F4F7;overflow:hidden;margin:6px 0 2px;}
.meter>div{height:100%;background:#FF9330;}

.block-container > div:empty { display:none !important; margin:0 !important; padding:0 !important; }
</style>
""", unsafe_allow_html=True)

# =========================
# OpenAI 클라이언트
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
# 공통 유틸/함수 (이름 변경 금지)
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
# 헤더 + 히어로
# =========================
st.markdown('<div class="container">', unsafe_allow_html=True)

st.markdown("""
<div class="top-nav">
  <div class="nav-left">
    <div><a href="/mainpage" target="_self">🐾 딸깍공</a></div>
    <div class="nav-menu">
      <div><a href="/mainpage" target="_self">메인페이지</a></div>
      <div><a href="/main" target="_self">공부 시작</a></div>
      <div><a href="/ocr_paddle" target="_self">PDF 요약</a></div>
      <div><a href="/quiz" target="_self">퀴즈</a></div>
      <div><a href="/report" target="_self">리포트</a></div>
      <div><a href="/ranking" target="_self">랭킹</a></div>
    </div>
  </div>
  <div class="profile-group">
    <div class="profile-icon">🐰</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="hero">퀴즈</div>', unsafe_allow_html=True)

# =========================
# 상태 기본값
# =========================
if "quiz_stage" not in st.session_state:
    st.session_state.quiz_stage = "setup"

# 포인트 지갑 (데이터 연동 전 임시)
if "user_points" not in st.session_state:
    st.session_state.user_points = 100

# =========================
# SETUP UI (두 섹션 + 하단 입력란 분리)
# =========================
if st.session_state.quiz_stage == "setup":
    left, right = st.columns(2, gap="large")

    # ── 왼쪽: 일반 퀴즈 생성
    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">퀴즈 생성</div>', unsafe_allow_html=True)

        st.markdown('<div class="subtle">유형 선택</div>', unsafe_allow_html=True)
        t_obj = st.checkbox("객관식", value=True, key="t_obj")
        t_ox  = st.checkbox("OX", value=True, key="t_ox")
        t_sa  = st.checkbox("단답형", value=True, key="t_sa")
        allowed_left = [t for t, ok in [("객관식", t_obj), ("OX", t_ox), ("단답형", t_sa)] if ok]

        st.markdown('<div class="subtle">문항 수</div>', unsafe_allow_html=True)
        quiz_count = st.number_input("문항 수", min_value=4, max_value=20, value=8, step=1, key="count_input", label_visibility="collapsed")

        st.markdown('<div class="subtle">✍️ (퀴즈 생성) 학습 내용을 입력하세요</div>', unsafe_allow_html=True)
        content_normal = st.text_area("✍️ (퀴즈 생성) 학습 내용을 입력하세요",
                                      value="", height=140, key="quiz_content_input",
                                      label_visibility="collapsed")

        st.markdown('<div class="primary-btn orange">', unsafe_allow_html=True)
        make_btn = st.button("퀴즈 생성하기", key="make_quiz", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if make_btn:
            content_to_use = (st.session_state.get("quiz_content_input","") or "").strip()
            if not content_to_use:
                st.warning("내용을 입력해주세요.")
            else:
                with st.spinner("GPT가 퀴즈를 생성 중입니다..."):
                    st.session_state.summary_log = summarize_content(content_to_use)
                    data = generate_quiz(content_to_use, st.session_state.count_input, allowed_types=set(allowed_left))
                    if not data:
                        st.error("퀴즈 생성에 실패했어요. 내용을 조금 더 길게 입력해보세요.")
                    else:
                        # 공통 플레이 상태
                        st.session_state.quiz_data = data
                        st.session_state.user_answers = {}
                        st.session_state.current_idx = 0
                        st.session_state.graded = False
                        st.session_state.score = 0
                        # 일반 모드
                        st.session_state.is_bet_round = False
                        st.session_state.bet_points = 0
                        st.session_state.quiz_stage = "play"
                        st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)  # /card

    # ── 오른쪽: 배팅 퀴즈 생성 (10문제 고정)
    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f'<div class="section-title">배팅 퀴즈 생성 <span class="right-badge">{st.session_state.user_points} P</span></div>', unsafe_allow_html=True)

        # 고정 규칙 안내
        st.markdown('<div class="subtle">배팅 규칙</div>', unsafe_allow_html=True)
        st.markdown(
            """
<div class="rule"><span class="dot green"></span><b>문항 수</b>는 배팅 퀴즈에서 <b>10문제 고정</b>입니다</div>
<div class="rule"><span class="dot blue"></span>성공 기준: <b>7개 이상 정답</b> → <b>1.25배</b> 지급</div>
<div class="rule"><span class="dot red"></span>실패: 배팅 포인트 <b>전액 소멸</b></div>
""",
            unsafe_allow_html=True
        )

        # 배팅 포인트 입력 (잔액 한도)
        st.markdown('<div class="subtle">배팅 포인트</div>', unsafe_allow_html=True)
        max_bet = max(0, int(st.session_state.user_points))
        bet_points_input = st.number_input("배팅 포인트",
                                           min_value=0, max_value=max_bet,
                                           value=min(100, max_bet), step=10,
                                           key="bet_points_input", label_visibility="collapsed")

        # 배팅 전용 학습 내용 입력
        st.markdown('<div class="subtle">✍️ (배팅 퀴즈) 학습 내용을 입력하세요</div>', unsafe_allow_html=True)
        content_bet = st.text_area("✍️ (배팅 퀴즈) 학습 내용을 입력하세요",
                                   value="", height=140, key="quiz_content_input_bet",
                                   label_visibility="collapsed")

        # (선택) 배팅에서도 유형 고를 수 있게 미니 옵션 유지
        c1, c2, c3 = st.columns(3)
        with c1: bet_ox  = st.checkbox("OX", value=True, key="bet_t_ox")
        with c2: bet_obj = st.checkbox("객관식", value=True, key="bet_t_obj")
        with c3: bet_sa  = st.checkbox("단답형", value=True, key="bet_t_sa")
        allowed_bet = [t for t, ok in [("객관식", bet_obj), ("OX", bet_ox), ("단답형", bet_sa)] if ok]

        st.markdown('<div class="primary-btn orange">', unsafe_allow_html=True)
        bet_btn_disabled = (max_bet <= 0)
        bet_btn = st.button("배팅 퀴즈 생성하기", key="make_quiz_bet", use_container_width=True, disabled=bet_btn_disabled)
        st.markdown('</div>', unsafe_allow_html=True)

        if bet_btn:
            if max_bet <= 0:
                st.error("포인트가 없습니다. 배팅할 수 없어요.")
            else:
                content_to_use = (st.session_state.get("quiz_content_input_bet","") or "").strip()
                if not content_to_use:
                    st.warning("배팅용 학습 내용을 입력해주세요.")
                else:
                    if bet_points_input <= 0:
                        st.warning("배팅 포인트를 1 이상 입력해주세요.")
                    elif bet_points_input > st.session_state.user_points:
                        st.error("잔액이 부족합니다.")
                    else:
                        with st.spinner("GPT가 배팅용 퀴즈(10문제)를 생성 중입니다..."):
                            # 10문제 고정
                            data = generate_quiz(content_to_use, 10, allowed_types=set(allowed_bet))
                            if not data or len(data) < 10:
                                st.error("퀴즈 생성에 실패했어요. 내용을 조금 더 길게 입력해보세요.")
                            else:
                                st.session_state.quiz_data = data[:10]
                                st.session_state.user_answers = {}
                                st.session_state.current_idx = 0
                                st.session_state.graded = False
                                st.session_state.score = 0
                                # 배팅 모드
                                st.session_state.is_bet_round = True
                                st.session_state.bet_points = int(bet_points_input)
                                st.session_state.bet_settled = False
                                st.session_state.quiz_stage = "play"
                                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)  # /card

# ─────────────────────────────────────────────────────────────────────────────
# PLAY
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.quiz_stage == "play":
    if not st.session_state.get("quiz_data"):
        st.session_state.quiz_stage = "setup"
        st.rerun()

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

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">퀴즈 풀기</div>', unsafe_allow_html=True)
        st.markdown('<div class="quiz-shell">', unsafe_allow_html=True)
        st.markdown('<div class="quiz-body">', unsafe_allow_html=True)

        st.markdown(f'<div class="quiz-meta">{idx+1}/{total}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="quiz-question">{q.get("question","-")}</div>', unsafe_allow_html=True)

        if qtype in ["객관식","OX"]:
            options = q.get("options", []) or (["O","X"] if qtype=="OX" else [])
            labels = [f"{i+1}." for i in range(len(options))]
            if idx not in st.session_state.user_answers:
                st.session_state.user_answers[idx] = None

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
                        sel = (st.session_state.user_answers[idx] == opt)
                        if tile(opt, labels[r], f"nopt_{idx}_{r}", sel):
                            st.session_state.user_answers[idx] = opt
                with g2:
                    if r+1 < len(options):
                        opt = options[r+1]
                        sel = (st.session_state.user_answers[idx] == opt)
                        if tile(opt, labels[r+1], f"nopt_{idx}_{r+1}", sel):
                            st.session_state.user_answers[idx] = opt
        else:
            key = f"sa_{idx}"
            val = st.text_input("정답을 입력하세요", key=key)
            st.session_state.user_answers[idx] = val

        st.markdown('<div class="action-row">', unsafe_allow_html=True)
        cprev, cnext = st.columns([1,1], gap="small")
        with cprev:
            if st.button("이전", key=f"prev_{idx}") and st.session_state.current_idx > 0:
                st.session_state.current_idx -= 1
                st.rerun()
        with cnext:
            if idx < total-1:
                if st.button("다음", key=f"next_{idx}")                :
                    st.session_state.current_idx += 1
                    st.rerun()
            else:
                if st.button("제출/채점", key="submit_all"):
                    score = 0
                    for i, qq in enumerate(qlist):
                        user = st.session_state.user_answers.get(i, "")
                        if _is_correct(user, qq.get("answer","")):
                            score += 1
                    st.session_state.score = score
                    st.session_state.graded = True
                    st.session_state.quiz_stage = "result"
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    _render_player()

# ─────────────────────────────────────────────────────────────────────────────
# RESULT (+ 배팅 정산)
# ─────────────────────────────────────────────────────────────────────────────
elif st.session_state.quiz_stage == "result":
    if not st.session_state.get("quiz_data"):
        st.session_state.quiz_stage = "setup"
        st.rerun()

    qlist = st.session_state.quiz_data
    total = len(qlist)
    score = st.session_state.get("score", 0)
    ratio = (score / total) if total else 0.0

    # 유형별 통계
    by_tot = {"객관식":0, "OX":0, "단답형":0}
    by_ok  = {"객관식":0, "OX":0, "단답형":0}

    def _normalize(s):
        if isinstance(s, (list, tuple)): return [str(x).strip().lower() for x in s]
        return str(s).strip().lower()
    def _is_correct(user, answer):
        u_ = _normalize(user); a_ = _normalize(answer)
        if isinstance(a_, list): return u_ in a_
        return u_ == a_

    for i, qq in enumerate(qlist):
        t = (qq.get("type") or "").strip()
        if t not in by_tot: by_tot[t] = 0
        if t not in by_ok:  by_ok[t]  = 0
        by_tot[t] += 1
        user = st.session_state.user_answers.get(i, "")
        if _is_correct(user, qq.get("answer","")):
            by_ok[t] += 1

    # 배팅 정산 (한 번만)
    bet_note = ""
    if st.session_state.get("is_bet_round"):
        if not st.session_state.get("bet_settled", False):
            bet = int(st.session_state.get("bet_points", 0) or 0)
            if bet > 0:
                if score >= 7:  # 성공 기준
                    gain = int(round(bet * 1.25))
                    st.session_state.user_points += gain
                    bet_note = f"✅ 배팅 성공! +{gain}P 지급 (7/10 이상 정답)"
                else:
                    st.session_state.user_points -= bet
                    if st.session_state.user_points < 0: st.session_state.user_points = 0
                    bet_note = f"❌ 배팅 실패… -{bet}P 차감 (6/10 이하 정답)"
            st.session_state.bet_settled = True

    # 결과 카드
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">퀴즈 결과</div>', unsafe_allow_html=True)

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
    if bet_note:
        st.success(f"{bet_note}  |  현재 잔액: {st.session_state.user_points}P")

    # 오답 해설
    wrongs = []
    for i, q in enumerate(st.session_state.quiz_data):
        user = st.session_state.user_answers.get(i, "")
        if not _is_correct(user, q.get("answer","")):
            wrongs.append((i, q, user))

    if wrongs:
        st.markdown('<div class="subtle">오답 해설</div>', unsafe_allow_html=True)
        for i, q, user in wrongs:
            with st.expander(f"문제 {i+1} | 내 답: {user} / 정답: {q.get('answer','')}"):
                try:
                    why = ask_gpt_about_wrong(q, user)
                except Exception:
                    why = q.get("explanation","")
                st.write(why)

    # 하단: 새로고침
    st.markdown("<hr style='border:none; border-top:1px dashed rgba(0,0,0,.08); margin: 16px 0 8px;'>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:right;'>", unsafe_allow_html=True)
    if st.button("🔃새로고침", key="refresh_all"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)  # /card

# 컨테이너 닫기
st.markdown("</div>", unsafe_allow_html=True)
