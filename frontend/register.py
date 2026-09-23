import streamlit as st
import hashlib

from database.connection import get_connection


def hash_password(password):

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def show_register_page():

    st.title("🚀 Create your AgentForge Account")

    st.write(
        "Start building software with your AI engineering team."
    )

    name = st.text_input(
        "Full Name",
        placeholder="Enter your full name",
        key="register_name"
    )

    email = st.text_input(
        "Email Address",
        placeholder="Enter your email",
        key="register_email"
    )

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Create a password",
        key="register_password"
    )

    confirm_password = st.text_input(
        "Confirm Password",
        type="password",
        placeholder="Confirm your password",
        key="register_confirm_password"
    )

    if st.button(
        "Create Account",
        type="primary",
        use_container_width=True,
        key="register_button"
    ):

        if not name.strip():
            st.error("Please enter your name.")
            return

        if not email.strip():
            st.error("Please enter your email.")
            return

        if len(password) < 6:
            st.error(
                "Password must contain at least 6 characters."
            )
            return

        if password != confirm_password:
            st.error("Passwords do not match.")
            return

        connection = get_connection()

        try:

            cursor = connection.cursor()

            cursor.execute(
                "SELECT id FROM users WHERE email = ?",
                (email.strip().lower(),)
            )

            if cursor.fetchone():

                st.error(
                    "An account with this email already exists."
                )

                return

            hashed_password = hash_password(password)

            cursor.execute(
                """
                INSERT INTO users
                (name, email, password, created_at)
                VALUES (?, ?, ?, datetime('now'))
                """,
                (
                    name.strip(),
                    email.strip().lower(),
                    hashed_password
                )
            )

            connection.commit()

            st.success(
                "Account created successfully!"
            )

            st.session_state["page"] = "login"

            st.rerun()

        except Exception as error:

            connection.rollback()

            st.error(
                f"Registration failed: {error}"
            )

        finally:

            connection.close()

    st.write("")

    if st.button(
        "Already have an account? Login",
        use_container_width=True,
        key="register_login_button"
    ):

        st.session_state["page"] = "login"

        st.rerun()