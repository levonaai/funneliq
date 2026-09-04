"""Supabase email/password auth for the Streamlit dashboard (Pillar 2).

Uses the public anon key only, as the PRD requires - this is frontend
code. The backend (app/auth.py) independently verifies the JWT this
produces and holds the separate service_role key; the two never mix.
"""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

SESSION_KEY = "supabase_session"


@st.cache_resource
def _get_anon_client() -> Client:
    url = os.environ.get("SUPABASE_URL", "")
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "")
    if not url or not anon_key:
        st.error("SUPABASE_URL / SUPABASE_ANON_KEY are not configured (see .env.example).")
        st.stop()
    return create_client(url, anon_key)


def require_login() -> dict:
    """Render a sign-in/sign-up form and halt the page until authenticated.

    Returns `{"access_token": ..., "email": ...}` for the signed-in user.
    Call at the top of every dashboard page (Streamlit session state is
    shared across pages within one browser session, but each page should
    still enforce the check independently against direct navigation).
    """
    if SESSION_KEY in st.session_state:
        return st.session_state[SESSION_KEY]

    st.title("FunnelIQ - Sign in")
    client = _get_anon_client()

    tab_login, tab_signup = st.tabs(["Sign in", "Create account"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Sign in")
        if submitted:
            try:
                result = client.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state[SESSION_KEY] = {
                    "access_token": result.session.access_token,
                    "email": result.user.email,
                }
                st.rerun()
            except Exception as exc:  # noqa: BLE001 - surface any auth failure to the user
                st.error(f"Sign-in failed: {exc}")

    with tab_signup:
        with st.form("signup_form"):
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            signed_up = st.form_submit_button("Create account")
        if signed_up:
            try:
                client.auth.sign_up({"email": new_email, "password": new_password})
                st.success("Account created - check your email to confirm, then sign in.")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Sign-up failed: {exc}")

    st.stop()
    raise AssertionError("unreachable - st.stop() halts execution")


def sign_out() -> None:
    st.session_state.pop(SESSION_KEY, None)
    st.rerun()


def render_account_sidebar(session: dict) -> None:
    with st.sidebar:
        st.write(f"Signed in as **{session['email']}**")
        if st.button("Sign out"):
            sign_out()
