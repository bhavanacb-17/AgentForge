import streamlit as st
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
import shutil


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AgentForge | AI Software Engineering",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = BASE_DIR / "database" / "agentforge.db"

GENERATED_PROJECTS_DIR = BASE_DIR / "generated_projects"


# ============================================================
# DATABASE
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ============================================================
# PASSWORD
# ============================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "page": "home",
    "logged_in": False,
    "user_id": None,
    "user_name": None,
    "user_email": None,
    "current_project_id": None,
    "rename_project_id": None,
    "edit_project_id": None,
    "delete_project_id": None
}

for key, value in defaults.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# NAVIGATION
# ============================================================

def go_home():

    st.session_state.page = "home"
    st.rerun()


def go_login():

    st.session_state.page = "login"
    st.rerun()


def go_register():

    st.session_state.page = "register"
    st.rerun()


def go_dashboard():

    st.session_state.page = "dashboard"
    st.rerun()


def logout():

    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.user_email = None
    st.session_state.current_project_id = None
    st.session_state.page = "home"

    st.rerun()


# ============================================================
# AI MOCK RESPONSE
# ============================================================

def generate_ai_response(project, user_message):

    project_name = project[1]

    message_lower = user_message.lower()

    if "hello" in message_lower or "hi" in message_lower:

        return (
            f"Hello! I'm the AgentForge AI engineering assistant "
            f"for **{project_name}**. Tell me what you would like "
            f"to build or modify."
        )

    if "requirement" in message_lower:

        return (
            "I have analyzed your request. I can help convert "
            "your idea into functional requirements, technical "
            "constraints and expected outputs."
        )

    if "code" in message_lower or "build" in message_lower:

        return (
            "I understand the development request. In the next "
            "pipeline stages, AgentForge can pass this requirement "
            "through Requirements Analysis, Architect, Developer, "
            "Tester, Debugger, Code Reviewer and Documentation."
        )

    return (
        f"I've received your request for **{project_name}**.\n\n"
        f"Your request was:\n"
        f"> {user_message}\n\n"
        "The project context has been isolated to this project. "
        "The real AI agent pipeline will be connected in the "
        "next stage."
    )


# ============================================================
# GLOBAL CSS
# ============================================================

st.markdown(
    """
<style>

.block-container {
    max-width: 1250px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

.stApp {
    background-color: #ffffff;
}

/* Buttons */

.stButton > button {
    min-height: 42px !important;
    height: 42px !important;
    padding: 8px 18px !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    line-height: 1.2 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* Primary buttons */

.stButton > button[kind="primary"] {
    background-color: #7c3aed !important;
    color: white !important;
    border: 1px solid #7c3aed !important;
}

.stButton > button[kind="primary"]:hover {
    background-color: #6d28d9 !important;
    color: white !important;
}

/* Normal buttons */

.stButton > button:not([kind="primary"]) {
    background-color: white !important;
    color: #4c1d95 !important;
    border: 1px solid #ddd6fe !important;
}

.stButton > button:not([kind="primary"]):hover {
    border-color: #7c3aed !important;
}

/* Inputs */

.stTextInput input,
.stTextArea textarea {
    border-radius: 10px !important;
}

/* Titles */

h1, h2, h3 {
    color: #252538;
}

</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# LOGIN
# ============================================================

if st.session_state.page == "login":

    brand_col, empty_col, home_col = st.columns(
        [3, 5, 1.5],
        vertical_alignment="center"
    )

    with brand_col:

        st.markdown("## ⚡ AgentForge")

        st.caption(
            "AUTONOMOUS SOFTWARE ENGINEERING"
        )

    with home_col:

        if st.button(
            "← Home",
            key="login_home",
            use_container_width=True
        ):

            go_home()

    st.divider()

    left, center, right = st.columns(
        [1.5, 4, 1.5]
    )

    with center:

        st.write("")

        st.markdown("## Welcome Back 👋")

        st.write(
            "Sign in to continue to your AgentForge workspace."
        )

        st.write("")

        with st.container(border=True):

            st.markdown("### Sign in")

            email = st.text_input(
                "Email Address",
                placeholder="Enter your email address",
                key="login_email"
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password"
            )

            st.write("")

            if st.button(
                "Login →",
                key="login_submit",
                type="primary",
                use_container_width=True
            ):

                if not email.strip():

                    st.error(
                        "Please enter your email address."
                    )

                elif not password:

                    st.error(
                        "Please enter your password."
                    )

                else:

                    try:

                        connection = get_connection()

                        cursor = connection.cursor()

                        cursor.execute(
                            """
                            SELECT id, name, email, password
                            FROM users
                            WHERE email = ?
                            """,
                            (email.strip(),)
                        )

                        user = cursor.fetchone()

                        if user is None:

                            connection.close()

                            st.error(
                                "No account found with this email."
                            )

                        else:

                            user_id = user[0]
                            user_name = user[1]
                            user_email = user[2]
                            stored_password = user[3]

                            password_hash = hash_password(
                                password
                            )

                            valid = (
                                stored_password == password_hash
                                or
                                stored_password == password
                            )

                            if not valid:

                                connection.close()

                                st.error(
                                    "Incorrect password."
                                )

                            else:

                                if stored_password == password:

                                    cursor.execute(
                                        """
                                        UPDATE users
                                        SET password = ?
                                        WHERE id = ?
                                        """,
                                        (
                                            password_hash,
                                            user_id
                                        )
                                    )

                                    connection.commit()

                                connection.close()

                                st.session_state.logged_in = True
                                st.session_state.user_id = user_id
                                st.session_state.user_name = user_name
                                st.session_state.user_email = user_email
                                st.session_state.page = "dashboard"

                                st.rerun()

                    except sqlite3.Error as error:

                        st.error(
                            f"Database error: {error}"
                        )

        st.write("")

        if st.button(
            "Don't have an account? Create one",
            key="login_register",
            use_container_width=True
        ):

            go_register()

    st.stop()


# ============================================================
# REGISTER
# ============================================================

if st.session_state.page == "register":

    brand_col, empty_col, login_col = st.columns(
        [3, 5, 1.5],
        vertical_alignment="center"
    )

    with brand_col:

        st.markdown("## ⚡ AgentForge")

        st.caption(
            "AUTONOMOUS SOFTWARE ENGINEERING"
        )

    with login_col:

        if st.button(
            "← Login",
            key="register_login",
            use_container_width=True
        ):

            go_login()

    st.divider()

    left, center, right = st.columns(
        [1.5, 4, 1.5]
    )

    with center:

        st.markdown("## Create Your Account")

        st.write(
            "Create your account and start building with AgentForge."
        )

        st.write("")

        with st.container(border=True):

            st.markdown("### Create Account")

            name = st.text_input(
                "Full Name",
                placeholder="Enter your full name",
                key="register_name"
            )

            email = st.text_input(
                "Email Address",
                placeholder="Enter your email address",
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
                key="register_confirm"
            )

            st.write("")

            if st.button(
                "Create Account →",
                key="register_submit",
                type="primary",
                use_container_width=True
            ):

                if not name.strip():

                    st.error("Please enter your name.")

                elif not email.strip():

                    st.error("Please enter your email.")

                elif not password:

                    st.error("Please create a password.")

                elif len(password) < 6:

                    st.error(
                        "Password must contain at least 6 characters."
                    )

                elif password != confirm_password:

                    st.error(
                        "Passwords do not match."
                    )

                else:

                    try:

                        connection = get_connection()

                        cursor = connection.cursor()

                        cursor.execute(
                            """
                            SELECT id
                            FROM users
                            WHERE email = ?
                            """,
                            (email.strip(),)
                        )

                        existing = cursor.fetchone()

                        if existing:

                            connection.close()

                            st.error(
                                "An account with this email already exists."
                            )

                        else:

                            cursor.execute(
                                """
                                INSERT INTO users
                                (
                                    name,
                                    email,
                                    password,
                                    created_at
                                )
                                VALUES (?, ?, ?, ?)
                                """,
                                (
                                    name.strip(),
                                    email.strip(),
                                    hash_password(password),
                                    datetime.now().isoformat()
                                )
                            )

                            connection.commit()

                            connection.close()

                            st.success(
                                "Account created successfully!"
                            )

                            st.session_state.page = "login"

                            st.rerun()

                    except sqlite3.Error as error:

                        st.error(
                            f"Database error: {error}"
                        )

    st.stop()


# ============================================================
# CREATE PROJECT
# ============================================================

if st.session_state.page == "create_project":

    if not st.session_state.logged_in:

        go_login()

    brand_col, empty_col, logout_col = st.columns(
        [3, 5, 1.5],
        vertical_alignment="center"
    )

    with brand_col:

        st.markdown("## ⚡ AgentForge")

        st.caption(
            "AUTONOMOUS SOFTWARE ENGINEERING"
        )

    with logout_col:

        if st.button(
            "Logout",
            key="create_logout",
            use_container_width=True
        ):

            logout()

    st.divider()

    st.title("Create New Project")

    st.write(
        "Define your project requirements and prepare "
        "your AgentForge engineering workspace."
    )

    st.write("")

    with st.container(border=True):

        st.markdown("### Project Information")

        project_name = st.text_input(
            "Project Name *",
            placeholder="Example: Student Management System",
            key="create_name"
        )

        project_description = st.text_area(
            "Description *",
            placeholder="Describe what your application should do...",
            height=120,
            key="create_description"
        )

        requirements = st.text_area(
            "Requirements *",
            placeholder=(
                "- User registration\n"
                "- Add student\n"
                "- Update student\n"
                "- Delete student\n"
                "- Search student"
            ),
            height=180,
            key="create_requirements"
        )

        col1, col2 = st.columns(2)

        with col1:

            category = st.selectbox(
                "Category",
                [
                    "Web Application",
                    "Mobile Application",
                    "Desktop Application",
                    "API / Backend",
                    "Data / AI Project",
                    "Automation",
                    "Other"
                ],
                key="create_category"
            )

        with col2:

            programming_language = st.selectbox(
                "Programming Language",
                [
                    "Python",
                    "Java",
                    "JavaScript",
                    "TypeScript",
                    "C++",
                    "C#",
                    "Go",
                    "Other"
                ],
                key="create_language"
            )

        col3, col4 = st.columns(2)

        with col3:

            framework = st.text_input(
                "Framework",
                placeholder="Example: Streamlit / Django / React",
                key="create_framework"
            )

        with col4:

            database_name = st.text_input(
                "Database",
                placeholder="Example: SQLite / MySQL / PostgreSQL",
                key="create_database"
            )

        additional_instructions = st.text_area(
            "Additional Instructions",
            placeholder="Add technical constraints or preferences...",
            height=120,
            key="create_instructions"
        )

    st.write("")

    cancel_col, create_col = st.columns(2)

    with cancel_col:

        if st.button(
            "← Cancel",
            key="create_cancel",
            use_container_width=True
        ):

            go_dashboard()

    with create_col:

        if st.button(
            "Create Project →",
            key="create_submit",
            type="primary",
            use_container_width=True
        ):

            if not project_name.strip():

                st.error("Please enter a project name.")

            elif not project_description.strip():

                st.error("Please enter a description.")

            elif not requirements.strip():

                st.error("Please enter the requirements.")

            else:

                try:

                    connection = get_connection()

                    cursor = connection.cursor()

                    cursor.execute(
                        """
                        SELECT id
                        FROM projects
                        WHERE user_id = ?
                        AND LOWER(name) = LOWER(?)
                        """,
                        (
                            st.session_state.user_id,
                            project_name.strip()
                        )
                    )

                    existing = cursor.fetchone()

                    if existing:

                        connection.close()

                        st.error(
                            "You already have a project with this name."
                        )

                    else:

                        now = datetime.now().isoformat()

                        final_requirements = (
                            requirements.strip()
                        )

                        if additional_instructions.strip():

                            final_requirements += (
                                "\n\nAdditional Instructions:\n"
                                +
                                additional_instructions.strip()
                            )

                        cursor.execute(
                            """
                            INSERT INTO projects
                            (
                                user_id,
                                name,
                                description,
                                requirements,
                                category,
                                programming_language,
                                framework,
                                database,
                                status,
                                created_at,
                                updated_at
                            )
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                st.session_state.user_id,
                                project_name.strip(),
                                project_description.strip(),
                                final_requirements,
                                category,
                                programming_language,
                                framework.strip(),
                                database_name.strip(),
                                "Active",
                                now,
                                now
                            )
                        )

                        project_id = cursor.lastrowid

                        cursor.execute(
                            """
                            INSERT INTO project_history
                            (
                                project_id,
                                activity_type,
                                description,
                                created_at
                            )
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                project_id,
                                "project_created",
                                f"Project '{project_name.strip()}' was created.",
                                now
                            )
                        )

                        connection.commit()

                        connection.close()

                        project_folder = (
                            GENERATED_PROJECTS_DIR
                            / f"project_{project_id}"
                        )

                        project_folder.mkdir(
                            parents=True,
                            exist_ok=True
                        )

                        readme = project_folder / "README.md"

                        readme.write_text(
                            f"# {project_name.strip()}\n\n"
                            f"## Description\n\n"
                            f"{project_description.strip()}\n\n"
                            f"## Requirements\n\n"
                            f"{final_requirements}\n\n"
                            f"## Technology\n\n"
                            f"- Language: {programming_language}\n"
                            f"- Framework: {framework or 'Not specified'}\n"
                            f"- Database: {database_name or 'Not specified'}\n",
                            encoding="utf-8"
                        )

                        st.session_state.current_project_id = project_id
                        st.session_state.page = "workspace"

                        st.rerun()

                except sqlite3.Error as error:

                    st.error(
                        f"Unable to create project: {error}"
                    )

    st.stop()


# ============================================================
# PROJECT WORKSPACE
# ============================================================

if st.session_state.page == "workspace":

    if not st.session_state.logged_in:

        go_login()

    project_id = st.session_state.current_project_id

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            name,
            description,
            requirements,
            category,
            programming_language,
            framework,
            database,
            status,
            created_at,
            updated_at
        FROM projects
        WHERE id = ?
        AND user_id = ?
        """,
        (
            project_id,
            st.session_state.user_id
        )
    )

    project = cursor.fetchone()

    connection.close()

    if project is None:

        st.error("Project not found.")

        if st.button(
            "← Back to Projects",
            key="workspace_missing"
        ):

            go_dashboard()

        st.stop()

    # --------------------------------------------------------
    # WORKSPACE NAVBAR
    # --------------------------------------------------------

    brand_col, project_col, back_col, logout_col = st.columns(
        [3, 3, 1.5, 1.5],
        vertical_alignment="center"
    )

    with brand_col:

        st.markdown("## ⚡ AgentForge")

        st.caption(
            "AUTONOMOUS SOFTWARE ENGINEERING"
        )

    with project_col:

        st.write(
            f"**📁 {project[1]}**"
        )

    with back_col:

        if st.button(
            "← Projects",
            key=f"workspace_projects_{project_id}",
            use_container_width=True
        ):

            go_dashboard()

    with logout_col:

        if st.button(
            "Logout",
            key=f"workspace_logout_{project_id}",
            use_container_width=True
        ):

            logout()

    st.divider()

    # --------------------------------------------------------
    # PROJECT HEADER
    # --------------------------------------------------------

    st.title(
        f"📁 {project[1]}"
    )

    st.write(
        project[2] or "No description available."
    )

    info1, info2, info3, info4 = st.columns(4)

    with info1:

        st.caption("CATEGORY")
        st.write(project[4])

    with info2:

        st.caption("LANGUAGE")
        st.write(project[5])

    with info3:

        st.caption("FRAMEWORK")
        st.write(project[6] or "Not specified")

    with info4:

        st.caption("DATABASE")
        st.write(project[7] or "Not specified")

    st.write("")

    # --------------------------------------------------------
    # WORKSPACE TABS
    # --------------------------------------------------------

    tab_chat, tab_req, tab_pipeline, tab_files, tab_docs, tab_history, tab_settings = st.tabs(
        [
            "💬 Chat",
            "📋 Requirements",
            "🤖 Agent Pipeline",
            "📄 Generated Files",
            "📚 Documentation",
            "🕒 History",
            "⚙️ Settings"
        ]
    )


    # ========================================================
    # CHAT
    # ========================================================

    with tab_chat:

        chat_header_col, clear_col = st.columns(
            [5, 1.5],
            vertical_alignment="center"
        )

        with chat_header_col:

            st.markdown(
                "### Project Chat"
            )

            st.caption(
                "Your conversation is isolated to this project."
            )

        with clear_col:

            if st.button(
                "Clear Chat",
                key=f"clear_chat_{project_id}",
                use_container_width=True
            ):

                connection = get_connection()

                cursor = connection.cursor()

                cursor.execute(
                    """
                    DELETE FROM project_messages
                    WHERE project_id = ?
                    """,
                    (project_id,)
                )

                now = datetime.now().isoformat()

                cursor.execute(
                    """
                    INSERT INTO project_history
                    (
                        project_id,
                        activity_type,
                        description,
                        created_at
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        project_id,
                        "chat_cleared",
                        "Project chat history was cleared.",
                        now
                    )
                )

                connection.commit()

                connection.close()

                st.success(
                    "Chat history cleared."
                )

                st.rerun()


        # ----------------------------------------------------
        # LOAD MESSAGES
        # ----------------------------------------------------

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                role,
                message,
                created_at
            FROM project_messages
            WHERE project_id = ?
            ORDER BY id ASC
            """,
            (project_id,)
        )

        messages = cursor.fetchall()

        connection.close()


        # ----------------------------------------------------
        # CHAT DISPLAY
        # ----------------------------------------------------

        if not messages:

            with st.container(border=True):

                st.markdown(
                    "### 👋 Start a conversation"
                )

                st.write(
                    "Tell AgentForge what you want to build, "
                    "change or improve in this project."
                )

                st.write("")

                st.info(
                    "Example: Build a student registration "
                    "API with authentication and MySQL."
                )

        else:

            for message in messages:

                role = message[1]
                content = message[2]

                if role == "user":

                    with st.chat_message("user"):

                        st.write(content)

                else:

                    with st.chat_message("assistant"):

                        st.markdown(content)


        # ----------------------------------------------------
        # CHAT INPUT
        # ----------------------------------------------------

        user_message = st.chat_input(
            "Message AgentForge...",
            key=f"project_chat_input_{project_id}"
        )


        if user_message:

            user_message = user_message.strip()

            if user_message:

                now = datetime.now().isoformat()

                try:

                    connection = get_connection()

                    cursor = connection.cursor()


                    # ----------------------------------------
                    # SAVE USER MESSAGE
                    # ----------------------------------------

                    cursor.execute(
                        """
                        INSERT INTO project_messages
                        (
                            project_id,
                            role,
                            message,
                            created_at
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            project_id,
                            "user",
                            user_message,
                            now
                        )
                    )


                    # ----------------------------------------
                    # HISTORY
                    # ----------------------------------------

                    cursor.execute(
                        """
                        INSERT INTO project_history
                        (
                            project_id,
                            activity_type,
                            description,
                            created_at
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            project_id,
                            "chat_sent",
                            "User sent a project chat message.",
                            now
                        )
                    )


                    connection.commit()

                    connection.close()


                    # ----------------------------------------
                    # AI RESPONSE
                    # ----------------------------------------

                    with st.spinner(
                        "AgentForge is thinking..."
                    ):

                        ai_response = generate_ai_response(
                            project,
                            user_message
                        )


                    # ----------------------------------------
                    # SAVE AI MESSAGE
                    # ----------------------------------------

                    connection = get_connection()

                    cursor = connection.cursor()


                    cursor.execute(
                        """
                        INSERT INTO project_messages
                        (
                            project_id,
                            role,
                            message,
                            created_at
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            project_id,
                            "assistant",
                            ai_response,
                            datetime.now().isoformat()
                        )
                    )


                    connection.commit()

                    connection.close()


                    st.rerun()


                except sqlite3.Error as error:

                    st.error(
                        f"Unable to save chat message: {error}"
                    )


    # ========================================================
    # REQUIREMENTS
    # ========================================================

    with tab_req:

        st.markdown(
            "### Project Requirements"
        )

        st.write(
            project[3] or "No requirements available."
        )


    # ========================================================
    # AGENT PIPELINE
    # ========================================================

    with tab_pipeline:

        st.markdown(
            "### Multi-Agent Pipeline"
        )

        st.write(
            "AgentForge will process your project through "
            "the following engineering agents:"
        )

        pipeline = [
            (
                "01",
                "Requirements Analysis",
                "Analyzes the project requirements."
            ),
            (
                "02",
                "Architect",
                "Designs the application architecture."
            ),
            (
                "03",
                "Developer",
                "Generates the application code."
            ),
            (
                "04",
                "Tester",
                "Creates and runs automated tests."
            ),
            (
                "05",
                "Debugger",
                "Analyzes and fixes detected issues."
            ),
            (
                "06",
                "Code Reviewer",
                "Reviews code quality and maintainability."
            ),
            (
                "07",
                "Documentation",
                "Generates technical documentation."
            )
        ]

        for number, name, description in pipeline:

            with st.container(border=True):

                st.caption(number)

                st.markdown(
                    f"### {name}"
                )

                st.write(
                    description
                )

        st.write("")

        if st.button(
            "▶ Run Agent Pipeline",
            key=f"run_pipeline_{project_id}",
            type="primary"
        ):

            st.info(
                "The real multi-agent pipeline will be connected "
                "after the chat module."
            )


    # ========================================================
    # GENERATED FILES
    # ========================================================

    with tab_files:

        st.markdown(
            "### Generated Files"
        )

        project_folder = (
            GENERATED_PROJECTS_DIR
            / f"project_{project_id}"
        )

        if project_folder.exists():

            files = [
                file
                for file in project_folder.rglob("*")
                if file.is_file()
            ]

            if files:

                for file in files:

                    relative_path = file.relative_to(
                        project_folder
                    )

                    col1, col2 = st.columns(
                        [5, 1]
                    )

                    with col1:

                        st.write(
                            f"📄 `{relative_path}`"
                        )

                    with col2:

                        st.caption(
                            f"{file.stat().st_size} bytes"
                        )

            else:

                st.info(
                    "No generated files yet."
                )

        else:

            st.info(
                "Project folder does not exist."
            )


    # ========================================================
    # DOCUMENTATION
    # ========================================================

    with tab_docs:

        st.markdown(
            "### Project Documentation"
        )

        st.info(
            "Documentation generation will be connected "
            "in the next stage."
        )


    # ========================================================
    # HISTORY
    # ========================================================

    with tab_history:

        st.markdown(
            "### Project History"
        )

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                activity_type,
                description,
                created_at
            FROM project_history
            WHERE project_id = ?
            ORDER BY id DESC
            """,
            (project_id,)
        )

        history = cursor.fetchall()

        connection.close()

        if history:

            for item in history:

                with st.container(border=True):

                    st.markdown(
                        f"**{item[0]}**"
                    )

                    st.write(
                        item[1]
                    )

                    st.caption(
                        item[2]
                    )

        else:

            st.info(
                "No project history yet."
            )


    # ========================================================
    # SETTINGS
    # ========================================================

    with tab_settings:

        st.markdown(
            "### Project Settings"
        )

        st.write(
            f"**Project:** {project[1]}"
        )

        st.write(
            f"**Status:** {project[8]}"
        )

        st.write(
            f"**Created:** {project[9]}"
        )

        st.write(
            f"**Updated:** {project[10]}"
        )

    st.stop()


# ============================================================
# DASHBOARD
# ============================================================

if st.session_state.page == "dashboard":

    if not st.session_state.logged_in:

        go_login()

    # --------------------------------------------------------
    # NAVBAR
    # --------------------------------------------------------

    brand_col, empty_col, logout_col = st.columns(
        [3, 5, 1.5],
        vertical_alignment="center"
    )

    with brand_col:

        st.markdown("## ⚡ AgentForge")

        st.caption(
            "AUTONOMOUS SOFTWARE ENGINEERING"
        )

    with logout_col:

        if st.button(
            "Logout",
            key="dashboard_logout",
            use_container_width=True
        ):

            logout()

    st.divider()

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    title_col, new_col = st.columns(
        [4, 1.5],
        vertical_alignment="center"
    )

    with title_col:

        st.title("Projects")

        st.write(
            f"Welcome, {st.session_state.user_name}."
        )

    with new_col:

        if st.button(
            "＋ New Project",
            key="dashboard_new",
            type="primary",
            use_container_width=True
        ):

            st.session_state.page = "create_project"

            st.rerun()

    st.write("")

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    search_col, filter_col = st.columns(
        [3, 1.5]
    )

    with search_col:

        search_text = st.text_input(
            "Search Projects",
            placeholder="Search projects...",
            key="dashboard_search"
        )

    with filter_col:

        status_filter = st.selectbox(
            "Status",
            [
                "All Projects",
                "Active",
                "In Progress",
                "Completed",
                "Archived"
            ],
            key="dashboard_filter"
        )

    # --------------------------------------------------------
    # LOAD PROJECTS
    # --------------------------------------------------------

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            name,
            description,
            category,
            programming_language,
            framework,
            database,
            status,
            created_at,
            updated_at
        FROM projects
        WHERE user_id = ?
        ORDER BY updated_at DESC
        """,
        (
            st.session_state.user_id,
        )
    )

    projects = cursor.fetchall()

    connection.close()

    # --------------------------------------------------------
    # FILTER
    # --------------------------------------------------------

    if search_text.strip():

        query = search_text.lower().strip()

        projects = [
            project
            for project in projects
            if query in (
                f"{project[1]} {project[2] or ''}"
            ).lower()
        ]

    if status_filter != "All Projects":

        projects = [
            project
            for project in projects
            if project[7] == status_filter
        ]

    # --------------------------------------------------------
    # EMPTY
    # --------------------------------------------------------

    if not projects:

        with st.container(border=True):

            st.markdown(
                "### No projects found"
            )

            st.write(
                "Create a new project to start building."
            )

            if st.button(
                "＋ Create Project",
                key="dashboard_empty",
                type="primary"
            ):

                st.session_state.page = "create_project"

                st.rerun()

        st.stop()

    # --------------------------------------------------------
    # PROJECT CARDS
    # --------------------------------------------------------

    for project in projects:

        project_id = project[0]

        with st.container(border=True):

            top_col, status_col = st.columns(
                [4, 1.5],
                vertical_alignment="center"
            )

            with top_col:

                st.markdown(
                    f"### 📁 {project[1]}"
                )

            with status_col:

                if project[7] == "Completed":

                    st.success("✓ Completed")

                elif project[7] == "In Progress":

                    st.info("⚙️ In Progress")

                elif project[7] == "Archived":

                    st.warning("📦 Archived")

                else:

                    st.success("● Active")

            st.write(
                project[2] or "No description provided."
            )

            info1, info2, info3, info4 = st.columns(4)

            with info1:

                st.caption("TYPE")
                st.write(project[3])

            with info2:

                st.caption("LANGUAGE")
                st.write(project[4])

            with info3:

                st.caption("FRAMEWORK")
                st.write(project[5] or "Not specified")

            with info4:

                st.caption("DATABASE")
                st.write(project[6] or "Not specified")

            st.divider()

            action1, action2 = st.columns(2)

            with action1:

                if st.button(
                    "Open Project →",
                    key=f"open_{project_id}",
                    type="primary",
                    use_container_width=True
                ):

                    st.session_state.current_project_id = project_id
                    st.session_state.page = "workspace"

                    st.rerun()

            with action2:

                if st.button(
                    "Create Another Project",
                    key=f"new_after_{project_id}",
                    use_container_width=True
                ):

                    st.session_state.page = "create_project"

                    st.rerun()

    st.stop()


# ============================================================
# HOME PAGE
# ============================================================

# ------------------------------------------------------------
# NAVBAR
# ------------------------------------------------------------

brand_col, nav_col, login_col = st.columns(
    [3, 5, 1.5],
    vertical_alignment="center"
)

with brand_col:

    st.markdown(
        "## ⚡ AgentForge"
    )

    st.caption(
        "AUTONOMOUS SOFTWARE ENGINEERING"
    )

with nav_col:

    nav1, nav2, nav3, nav4 = st.columns(
        4,
        vertical_alignment="center"
    )

    with nav1:

        st.write("**Home**")

    with nav2:

        st.write("**Features**")

    with nav3:

        st.write("**How It Works**")

    with nav4:

        st.write("**About**")

with login_col:

    if st.button(
        "Login",
        key="home_login",
        type="primary",
        use_container_width=True
    ):

        go_login()

st.divider()


# ============================================================
# HERO
# ============================================================

st.write("")

hero_left, hero_center, hero_right = st.columns(
    [1, 4, 1]
)

with hero_center:

    st.info(
        "✦ POWERED BY MULTI-AGENT AI"
    )

    st.title(
        "Build Software"
    )

    st.markdown(
        "## :violet[Smarter. Faster. Together.]"
    )

    st.write("")

    st.write(
        "AgentForge is an autonomous AI software engineering "
        "platform that transforms your ideas into working "
        "software through a collaborative team of specialized "
        "AI agents."
    )


# ============================================================
# PROMPT
# ============================================================

st.write("")

st.markdown(
    "### ✦ Describe what you want to build"
)

project_prompt = st.text_area(
    "Project description",
    placeholder=(
        "Example: Build an e-commerce backend with "
        "authentication, product management and payment APIs..."
    ),
    height=130,
    label_visibility="collapsed",
    key="home_prompt"
)

st.write("")

start_col1, start_col2, start_col3 = st.columns(
    [2, 1.5, 2]
)

with start_col2:

    if st.button(
        "Start Building →",
        key="home_start",
        type="primary",
        use_container_width=True
    ):

        if not project_prompt.strip():

            st.warning(
                "Please describe what you want to build."
            )

        elif not st.session_state.logged_in:

            go_login()

        else:

            st.session_state.page = "create_project"

            st.rerun()


# ============================================================
# CAPABILITIES
# ============================================================

st.write("")
st.write("")

st.markdown(
    "## Everything you need to build software"
)

st.write(
    "From your first idea to production-ready documentation, "
    "AgentForge handles the software engineering workflow."
)

st.write("")

features = [

    (
        "🔍",
        "Requirements Analysis",
        "Convert your idea into clear functional "
        "and technical requirements."
    ),

    (
        "🏗️",
        "Architecture",
        "Design scalable application architecture "
        "and technology structure."
    ),

    (
        "💻",
        "Code Generation",
        "Generate structured application code."
    ),

    (
        "🧪",
        "Automated Testing",
        "Create and execute automated tests."
    ),

    (
        "🐞",
        "Debugging",
        "Analyze failures and resolve software defects."
    ),

    (
        "🔎",
        "Code Review",
        "Review code quality and maintainability."
    ),

    (
        "📚",
        "Documentation",
        "Generate technical project documentation."
    )

]

for start in range(0, len(features), 3):

    columns = st.columns(3)

    for index, column in enumerate(columns):

        position = start + index

        if position >= len(features):

            break

        icon, title, description = features[position]

        with column:

            with st.container(border=True):

                st.markdown(
                    f"### {icon}"
                )

                st.markdown(
                    f"**{title}**"
                )

                st.write(
                    description
                )


# ============================================================
# AGENT WORKFLOW
# ============================================================

st.write("")
st.write("")

st.markdown(
    "## Your AI software engineering team"
)

st.write(
    "Seven specialized agents collaborate through "
    "a structured software engineering pipeline."
)

st.write("")

agents = [

    (
        "01",
        "🔍 Requirements Analysis",
        "Analyzes your idea and requirements."
    ),

    (
        "02",
        "🏗️ Architect",
        "Creates the application architecture."
    ),

    (
        "03",
        "💻 Developer",
        "Generates the application code."
    ),

    (
        "04",
        "🧪 Tester",
        "Creates and executes tests."
    ),

    (
        "05",
        "🐞 Debugger",
        "Analyzes and resolves failures."
    ),

    (
        "06",
        "🔎 Code Reviewer",
        "Reviews implementation quality."
    ),

    (
        "07",
        "📚 Documentation",
        "Creates technical documentation."
    )

]

for start in range(0, len(agents), 3):

    columns = st.columns(3)

    for index, column in enumerate(columns):

        position = start + index

        if position >= len(agents):

            break

        number, title, description = agents[position]

        with column:

            with st.container(border=True):

                st.caption(number)

                st.markdown(
                    f"### {title}"
                )

                st.write(
                    description
                )


# ============================================================
# PIPELINE
# ============================================================

st.write("")
st.write("")

st.markdown(
    "### Agent Pipeline"
)

st.info(
    "Requirements Analysis → Architect → Developer → "
    "Tester → Debugger → Code Reviewer → Documentation"
)


# ============================================================
# SIMPLE WORKFLOW
# ============================================================

st.write("")
st.write("")

st.markdown(
    "## From idea to software"
)

workflow = [

    (
        "01",
        "Describe",
        "Tell AgentForge what you want to build."
    ),

    (
        "02",
        "Collaborate",
        "AI agents analyze, design, build, test and review."
    ),

    (
        "03",
        "Build",
        "Receive structured software with code and tests."
    )

]

columns = st.columns(3)

for column, item in zip(columns, workflow):

    number, title, description = item

    with column:

        with st.container(border=True):

            st.caption(number)

            st.markdown(
                f"### {title}"
            )

            st.write(
                description
            )


# ============================================================
# CTA
# ============================================================

st.write("")
st.write("")

cta_left, cta_center, cta_right = st.columns(
    [1, 4, 1]
)

with cta_center:

    st.markdown(
        "## Turn your idea into software."
    )

    st.write(
        "Start with a simple description. Let your AI "
        "engineering team take it from there."
    )

    st.write("")

    if st.button(
        "Start Building →",
        key="bottom_start",
        type="primary",
        use_container_width=True
    ):

        if st.session_state.logged_in:

            st.session_state.page = "create_project"

            st.rerun()

        else:

            go_login()


# ============================================================
# FOOTER
# ============================================================

st.write("")
st.divider()

st.caption(
    "⚡ AgentForge • Autonomous Software Engineering Platform"
)