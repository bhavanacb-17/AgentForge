import streamlit as st
import hashlib

from database.connection import get_connection


def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def authenticate_user(email, password):

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id, name, email, password
            FROM users
            WHERE email = ?
            """,
            (email.strip().lower(),)
        )

        user = cursor.fetchone()

        if not user:
            return None

        hashed_password = hash_password(password)

        if user["password"] == hashed_password:
            return {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            }

        return None

    finally:
        connection.close()


def show_login_page():

    st.title("🤖 Welcome Back")

    st.write("Login to continue to AgentForge.")

    email = st.text_input(
        "Email Address",
        placeholder="Enter your email",
        key="login_email"
    )

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter your password",
        key="login_password"
    )

    if st.button(
        "Login",
        type="primary",
        use_container_width=True,
        key="login_button"
    ):

        if not email.strip():
            st.error("Please enter your email.")
            return

        if not password:
            st.error("Please enter your password.")
            return

        user = authenticate_user(
            email,
            password
        )

        if user:

            st.session_state["logged_in"] = True
            st.session_state["user_id"] = user["id"]
            st.session_state["user_name"] = user["name"]
            st.session_state["user_email"] = user["email"]
            st.session_state["page"] = "projects"

            st.rerun()

        else:

            st.error("Invalid email or password.")

    st.write("")

    if st.button(
        "Don't have an account? Create one",
        use_container_width=True,
        key="login_register_button"
    ):

        st.session_state["page"] = "register"
        st.rerun()