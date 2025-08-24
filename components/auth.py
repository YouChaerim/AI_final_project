# components/auth.py
import streamlit as st
import requests

AUTH_KEYS = {"logged_in", "user", "user_data", "auth_token", "dark_mode"}

def _get_qp():
    try:
        return st.query_params
    except Exception:
        return st.experimental_get_query_params()

def remember_login(user: dict, token: str, profile: dict | None = None, set_qp: bool = True):
    st.session_state["logged_in"] = True
    st.session_state["user"] = user or {}
    st.session_state["user_data"] = profile or {}
    st.session_state["auth_token"] = token or ""
    if set_qp and token:
        # 새 세션에서도 복구되도록 URL에 토큰 유지(옵션)
        try:
            st.query_params.update({"token": token})
        except Exception:
            pass

def require_login(backend_url: str) -> bool:
    # 0) 이미 로그인 상태면 통과
    if st.session_state.get("logged_in") and st.session_state.get("user"):
        return True

    # 1) 토큰 확보(쿼리파라미터 > 세션)
    qp = _get_qp()
    token = qp.get("token")
    if isinstance(token, list):
        token = token[0]
    token = token or st.session_state.get("auth_token")

    # 2) 토큰 검증으로 세션 복구
    if token:
        try:
            r = requests.get(
                f"{backend_url}/auth/verify",   # ← 백엔드에 맞게 수정
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
            if r.ok:
                data = r.json()
                remember_login(
                    user=data.get("user", {}),
                    token=token,
                    profile=data.get("profile", {}),
                    set_qp=False,
                )
                return True
        except Exception:
            pass

    # 3) 복구 실패 → 온보딩
    st.switch_page("onboarding.py")
    st.stop()

def logout(clear_qp: bool = True):
    for k in ("logged_in", "user", "user_data", "auth_token"):
        st.session_state.pop(k, None)
    if clear_qp:
        try:
            qp = _get_qp()
            if qp.get("token"):
                # URL token 제거
                st.query_params.update({k:v for k,v in qp.items() if k != "token"})
        except Exception:
            pass
    st.switch_page("onboarding.py")
    st.stop()
