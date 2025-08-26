# pages/mainpage.py
import os, re, base64, requests
import streamlit as st
from components.header import render_header
from components.auth import require_login
import streamlit.components.v1 as components


# -------------------------------
# 3) 스타일 & 헤더
# -------------------------------
bg_color, font_color, card_bg, nav_bg, dark_orange, label_color = \
    "#FAFAFA", "#333", "white", "rgba(255,255,255,0.9)", "#FF9330", "#333"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;800;900&display=swap');

:root{
  --bg:#FAFAFA;
  --text:#333;
  --nav:rgba(255,255,255,0.9);
  --card:#fff;
  --label:#333;
  --accent:#FF9330;
  --border:rgba(0,0,0,0.06);
}

/* 기본 */
html,body{ background:var(--bg); color:var(--text); font-family:'Noto Sans KR',sans-serif; zoom:1.10; margin:0; }
.stApp{ background:var(--bg); }
.block-container{ padding-top:10px !important; }
.container{ max-width:1200px; margin:auto; padding:40px; }
a{ color:var(--text); text-decoration:none !important; }

/* 스트림릿 UI 숨김 */
[data-testid="stSidebar"], [data-testid="stSidebarNav"], [data-testid="stToolbar"]{ display:none !important; }
            
/* 메인 히어로 박스 */
.main-box{
  background:var(--accent);
  border-radius:14px;
  padding:90px 0 140px 0;
  text-align:center;
  color:#fff;
  font-size:36px;
  font-weight:900;
  margin-bottom:16px;
}

/* "공부 시작" 버튼 (switch_page 버튼) */
.main-box .stButton > button{
  margin-top:30px;
  padding:16px 40px;
  background:#fff;
  color:#000 !important;
  font-weight:800;
  border:none;
  border-radius:8px;
  font-size:22px;
  cursor:pointer;
  box-shadow:0 1px 2px rgba(0,0,0,.04);
}
.main-box .stButton > button:hover{ filter:brightness(.98); }

/* st.page_link를 버튼처럼 (전역) */
.container [data-testid="stPageLink"] > a{
  display:inline-block;
  margin-top:30px;
  padding:16px 40px;
  background:#fff;
  color:#000 !important;
  font-weight:800;
  border-radius:8px;
  font-size:22px;
  text-decoration:none !important;
  box-shadow:0 1px 2px rgba(0,0,0,.04);
}
.container [data-testid="stPageLink"] > a:hover{ filter:brightness(.98); }

/* 카드/익스팬더 */
div[data-testid="stExpander"]{
  background:var(--card);
  border-radius:10px;
  border:1px solid #eee;
  box-shadow:0 1px 2px rgba(0,0,0,.04);
  overflow:hidden;
  margin:1px 0 !important;
}

/* 라벨 */
label{ color:var(--label) !important; font-weight:600; }

/* 유틸 */
.right-col-align{ position:relative; top:-4px; }
.tight-stack > * + *{ margin-top:8px; }
header{ display:none !important; }
            
.st-emotion-cache-a0ovpn e1ghu24d0 e1ghu24d0 [data-testid^="stPageLink"],
.st-emotion-cache-a0ovpn e1ghu24d0 e1ghu24d0 [data-testid^="stPageLink"] > a,
.st-emotion-cache-a0ovpn e1ghu24d0 e1ghu24d0 a[data-testid^="stPageLink"]{
  display:block !important;
  background:var(--accent) !important;
  color:#fff !important;
  font-weight:900 !important;
  font-size:36px !important;
  text-align:center !important;
  padding:90px 0 140px 0 !important;
  border-radius:14px !important;
  margin:0 0 16px 0 !important;
  box-shadow:none !important;
  border:none !important;
  text-decoration:none !important;
}

/* 전역 버튼 스타일이 있으면(흰색 사각형) 히어로 안에서는 무력화 */
.hero-link .st-emotion-cache a{
  background:transparent !important;
  box-shadow:none !important;
}

</style>
""", unsafe_allow_html=True)


render_header()

# -------------------------------
# 4) 본문
# -------------------------------
st.markdown('<div class="container">', unsafe_allow_html=True)

left, right = st.columns([2.5, 1])
with left:
    # 스타일 적용
    today_study_css = """
    <style>
    #today-study{
        
    }
    #today-study a{
        background:#FF9330; border-radius:14px; padding:90px 0 140px 0; text-align:center; color:#fff; font-size:36px; font-weight:900; margin-bottom:16px;
    }
    </style>
    """
    
    # 1) 목적지 div를 먼저 그립니다.
    st.markdown('<div id="today-study"></div>', unsafe_allow_html=True)

    # 2) page_link는 평소처럼
    st.page_link("pages/main.py", label="오늘 공부 시작하기")

    # 3) 렌더 후 page_link를 today-study 안으로 이동
    components.html("""
    <script>
    (function(){
      const HOST = '#today-study';                  // 넣고 싶은 div
      const TARGET_TEXT = '오늘 공부 시작하기';   // page_link 라벨

      const norm = s => (s||'').replace(/\\u00A0/g,' ').replace(/\\s+/g,' ').trim();

      function move(){
        const host = parent.document.querySelector(HOST);
        if(!host) return false;

        // div[data-testid="stPageLink"] 내부의 a 중 라벨 텍스트로 찾기
        const a = Array.from(parent.document.querySelectorAll("div[data-testid='stPageLink'] a"))
                       .find(el => {
                          const t = norm(el.textContent);
                          const aria = el.getAttribute('aria-label') || '';
                          return t === TARGET_TEXT || aria === TARGET_TEXT || t.includes(TARGET_TEXT);
                        });
        if(!a) return false;

        // 래퍼(위젯 컨테이너)째로 이동
        const wrapper = a.closest("div[data-testid='stPageLink']") || a;
        host.appendChild(wrapper);
        return true;
      }

      // 초기 시도 + 재렌더 대응
      if (!move()){
        const mo = new MutationObserver(() => { if (move()) mo.disconnect(); });
        mo.observe(parent.document.body, {childList:true, subtree:true});
      }
    })();
    </script>
    """, height=0)

    # 4) 이제 today-study 내부로 들어갔으니, 범위 지정해서 스타일링 가능
    st.markdown(today_study_css, unsafe_allow_html=True)

with right:
    st.markdown('<div class="right-col-align tight-stack">', unsafe_allow_html=True)

    # # 보기 모드
    # if not st.session_state.edit_mode:
    #     with st.expander("📌 오늘 할 일", expanded=True):
    #         todos = ud.get("todo_items", [])
    #         if not todos:
    #             st.caption("오늘 등록된 할 일이 없습니다.")
    #         for i, item in enumerate(todos):
    #             checked = st.checkbox(item["text"], value=item["done"], key=f"todo_view_{item['id']}")
    #             if checked != item["done"]:
    #                 toggle_todo(item["id"], i, checked)
    #                 st.rerun()

    #     with st.expander("🗓 빠른 메모", expanded=True):
    #         st.write(ud.get("memo", ""))

    #     with st.expander("⏰ 오늘 공부시간", expanded=True):
    #         st.write(f"{ud.get('study_hour', 0)}시간 {ud.get('study_minute', 0)}분")

    #     if st.button("✏️ 변경하기", use_container_width=True):
    #         st.session_state.edit_mode = True
    #         st.rerun()

    # # 편집 모드
    # else:
    #     # 4-1) 새 항목 추가
    #     with st.expander("➕ 새 항목 추가 (한 줄에 하나씩)", expanded=True):
    #         st.text_area(
    #             "새 할 일",
    #             key="new_todos_draft",
    #             placeholder="예) 영어 단어 30개\n수학 문제 5개",
    #             height=140
    #         )
    #         st.button(
    #             "추가하기",
    #             use_container_width=True,
    #             on_click=_on_click_add_new_todos,   # ← 여기서 처리
    #         )

    #     # 4-2) 기존 항목 수정
    #     with st.expander("✍️ 기존 항목 수정", expanded=True):
    #         todos = ud.get("todo_items", [])
    #         if not todos:
    #             st.caption("오늘 등록된 할 일이 없습니다.")
    #         for item in todos:
    #             with st.form(key=f"form_edit_{item['id']}"):
    #                 new_text = st.text_input("내용", value=item["text"], key=f"edit_{item['id']}")
    #                 cols = st.columns([1, 3])
    #                 with cols[0]:
    #                     submitted = st.form_submit_button("저장")
    #                 with cols[1]:
    #                     st.caption("수정 후 저장을 누르면 바로 반영됩니다.")
    #                 if submitted and new_text != item["text"]:
    #                     update_todo_text(item["id"], new_text)
    #                     st.rerun()

    #     # 4-3) 메모 수정
    #     with st.expander("🗓 빠른 메모 수정", expanded=True):
    #         memo_text = st.text_area("메모", value=ud.get("memo", ""), height=120, key="edit_memo_text")
    #         if st.button("메모 저장", use_container_width=True):
    #             save_memo(memo_text)
    #             st.rerun()

    #     # 4-4) 편집 종료
    #     if st.button("✅ 편집 완료", use_container_width=True):
    #         st.session_state.edit_mode = False
    #         st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
