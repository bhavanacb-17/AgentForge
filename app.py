import streamlit as st
import sqlite3
import hashlib
import textwrap
import shutil

from pathlib import Path
from datetime import datetime

from agents.pipeline import AgentPipeline
from core.gemini_client import GeminiClient
from projects.project_storage import ProjectStorage
from database.connection import get_connection

def add_history(project_id, activity_type, description):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO project_history
        (project_id, activity_type, description)
        VALUES (?, ?, ?)
        """,
        (
            project_id,
            activity_type,
            description
        )
    )

    connection.commit()
    connection.close()

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AgentForge",
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

GENERATED_PROJECTS_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    connection = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON")
    return connection

# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# ============================================================
# HTML RENDERING
# ============================================================

def render_html(html):

    st.html(
        textwrap.dedent(html)
    )


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "page": "home",
    "logged_in": False,
    "user_id": None,
    "user_name": "",
    "user_email": "",
    "current_project_id": None,
    "pipeline_results": {}
}

for key, value in defaults.items():

    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# NAVIGATION FUNCTIONS
# ============================================================

def go_home():

    st.session_state.page = "home"


def go_login():

    st.session_state.page = "login"


def go_register():

    st.session_state.page = "register"


def go_dashboard():

    st.session_state.page = "dashboard"


def go_create_project():

    st.session_state.page = "create_project"


def go_workspace():

    st.session_state.page = "workspace"


def logout():

    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = ""
    st.session_state.user_email = ""
    st.session_state.current_project_id = None
    st.session_state.pipeline_results = {}
    st.session_state.page = "home"


# ============================================================
# PROFESSIONAL UI CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       GLOBAL
       ======================================================== */

    .stApp {
        background:
            linear-gradient(
                180deg,
                #f8fafc 0%,
                #eef4ff 100%
            );

        color: #172033;
    }

    .block-container {
        max-width: 1400px;
        padding-top: 1rem;
        padding-bottom: 4rem;
    }

    h1,
    h2,
    h3,
    h4 {
        color: #172033 !important;
    }

    hr {
        border-color: #e2e8f0 !important;
    }


    /* ========================================================
       BUTTONS
       ======================================================== */

    [data-testid="stButton"] button {

        width: 100% !important;

        min-height: 42px !important;

        padding: 8px 14px !important;

        border-radius: 10px !important;

        background:
            linear-gradient(
                135deg,
                #2563eb,
                #1d4ed8
            ) !important;

        color: white !important;

        border: 1px solid #2563eb !important;

        font-weight: 600 !important;

        font-size: 14px !important;

        white-space: nowrap !important;

        box-shadow:
            0 4px 12px
            rgba(37, 99, 235, 0.18) !important;

        transition: all 0.2s ease !important;
    }

    [data-testid="stButton"] button:hover {

        background:
            linear-gradient(
                135deg,
                #1d4ed8,
                #1e40af
            ) !important;

        transform: translateY(-2px);

        box-shadow:
            0 8px 20px
            rgba(37, 99, 235, 0.28) !important;
    }


    /* ========================================================
       NAVBAR
       ======================================================== */

    .navbar-wrapper {

        background: #ffffff;

        border: 1px solid #dbe3ef;

        border-radius: 16px;

        padding: 10px 14px;

        margin-bottom: 28px;

        box-shadow:
            0 6px 20px
            rgba(15, 23, 42, 0.07);

        width: 100%;
    }

    .navbar-logo {

        height: 42px;

        display: flex;

        align-items: center;

        padding-left: 5px;

        font-size: 23px;

        font-weight: 800;

        color: #172033;

        white-space: nowrap;
    }


    /* ========================================================
       HERO
       ======================================================== */

    .hero-box {

        padding: 65px 45px;

        border-radius: 26px;

        background:
            linear-gradient(
                135deg,
                #ffffff 0%,
                #eff6ff 100%
            );

        border: 1px solid #dbeafe;

        box-shadow:
            0 20px 50px
            rgba(30, 64, 175, 0.08);

        margin-bottom: 35px;
    }

    .hero-badge {

        display: inline-block;

        padding: 7px 15px;

        border-radius: 30px;

        background: #dbeafe;

        color: #1d4ed8;

        font-size: 13px;

        font-weight: 700;

        margin-bottom: 18px;
    }

    .main-title {

        font-size: 54px;

        font-weight: 800;

        text-align: center;

        margin-top: 15px;

        margin-bottom: 18px;

        color: #111827;

        letter-spacing: -1.5px;
    }

    .main-subtitle {

        max-width: 850px;

        margin: auto;

        text-align: center;

        font-size: 19px;

        line-height: 1.8;

        color: #64748b;
    }


    /* ========================================================
       SECTION TITLE
       ======================================================== */

    .section-title {

        font-size: 30px;

        font-weight: 750;

        color: #172033;

        margin-top: 25px;

        margin-bottom: 18px;
    }


    /* ========================================================
       FEATURE CARD
       ======================================================== */

    .feature-card {

        background: white;

        padding: 28px;

        border-radius: 20px;

        border: 1px solid #e2e8f0;

        min-height: 190px;

        box-shadow:
            0 8px 25px
            rgba(15, 23, 42, 0.05);

        transition: all 0.2s ease;

        margin-bottom: 15px;
    }

    .feature-card:hover {

        transform: translateY(-4px);

        box-shadow:
            0 15px 35px
            rgba(15, 23, 42, 0.10);
    }

    .feature-icon {

        width: 46px;

        height: 46px;

        display: flex;

        align-items: center;

        justify-content: center;

        border-radius: 12px;

        background: #eff6ff;

        font-size: 22px;

        margin-bottom: 15px;
    }

    .feature-card h3 {

        margin: 0 0 10px 0;

        font-size: 19px;
    }

    .feature-card p {

        color: #64748b;

        line-height: 1.7;

        font-size: 14px;
    }


    /* ========================================================
       PROJECT CARD
       ======================================================== */

    .project-card {

        background: white;

        padding: 25px;

        border-radius: 20px;

        border: 1px solid #e2e8f0;

        margin-bottom: 18px;

        box-shadow:
            0 6px 20px
            rgba(15, 23, 42, 0.05);

        transition: all 0.2s ease;
    }

    .project-card:hover {

        border-color: #bfdbfe;

        box-shadow:
            0 12px 30px
            rgba(37, 99, 235, 0.10);

        transform: translateY(-2px);
    }


    /* ========================================================
       AGENT BOX
       ======================================================== */

    .agent-box {

        display: flex;

        align-items: center;

        background: white;

        padding: 19px 22px;

        border-radius: 16px;

        border: 1px solid #e2e8f0;

        margin-bottom: 12px;

        box-shadow:
            0 4px 14px
            rgba(15, 23, 42, 0.04);

        transition: all 0.2s ease;
    }

    .agent-box:hover {

        border-color: #93c5fd;

        transform: translateX(4px);
    }

    .agent-number {

        width: 40px;

        height: 40px;

        min-width: 40px;

        display: flex;

        align-items: center;

        justify-content: center;

        border-radius: 50%;

        background:
            linear-gradient(
                135deg,
                #2563eb,
                #4f46e5
            );

        color: white;

        font-weight: 700;

        margin-right: 15px;
    }

    .agent-name {

        font-weight: 650;

        color: #172033;

        font-size: 16px;
    }


    /* ========================================================
       WORKSPACE HEADER
       ======================================================== */

    .workspace-header {

        background: white;

        padding: 25px 30px;

        border-radius: 20px;

        border: 1px solid #e2e8f0;

        margin-bottom: 20px;

        box-shadow:
            0 6px 20px
            rgba(15, 23, 42, 0.04);
    }


    /* ========================================================
       FILE CARD
       ======================================================== */

    .file-card {

        background: white;

        border: 1px solid #e2e8f0;

        padding: 17px 20px;

        border-radius: 14px;

        margin-bottom: 10px;

        transition: all 0.2s ease;
    }

    .file-card:hover {

        border-color: #93c5fd;

        background: #f8fbff;
    }


    /* ========================================================
       HISTORY CARD
       ======================================================== */

    .history-card {

        background: white;

        padding: 18px 20px;

        border-radius: 14px;

        border-left: 4px solid #2563eb;

        border-top: 1px solid #e2e8f0;

        border-right: 1px solid #e2e8f0;

        border-bottom: 1px solid #e2e8f0;

        margin-bottom: 10px;
    }


    /* ========================================================
       STATUS BADGE
       ======================================================== */

    .status-badge {

        display: inline-block;

        padding: 5px 12px;

        border-radius: 20px;

        background: #dcfce7;

        color: #166534;

        font-size: 12px;

        font-weight: 700;
    }


    /* ========================================================
       RESPONSIVE
       ======================================================== */

    @media (max-width: 768px) {

        .main-title {
            font-size: 38px;
        }

        .main-subtitle {
            font-size: 16px;
        }

        .hero-box {
            padding: 40px 25px;
        }

        .navbar-logo {
            font-size: 19px;
        }

    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# NAVBAR
# ============================================================

def navbar():

    st.markdown(
        '<div class="navbar-wrapper">',
        unsafe_allow_html=True
    )

    col_logo, col_home, col_projects, col_account = st.columns(
        [4.2, 1.3, 1.6, 1.6],
        gap="small"
    )

    with col_logo:

        st.markdown(
            """
            <div class="navbar-logo">
                ⚡ AgentForge
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_home:

        if st.button(
            "🏠 Home",
            key="navbar_home",
            use_container_width=True
        ):

            go_home()
            st.rerun()

    with col_projects:

        if st.button(
            "📁 Projects",
            key="navbar_projects",
            use_container_width=True
        ):

            if st.session_state.logged_in:

                go_dashboard()

            else:

                go_login()

            st.rerun()

    with col_account:

        if st.session_state.logged_in:

            if st.button(
                "🚪 Logout",
                key="navbar_logout",
                use_container_width=True
            ):

                logout()
                st.rerun()

        else:

            if st.button(
                "🔐 Login",
                key="navbar_login",
                use_container_width=True
            ):

                go_login()
                st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# ============================================================
# HOME PAGE
# ============================================================

def show_home():

    navbar()

    render_html(
        """
        <div class="hero-box">

            <div style="text-align:center;">

                <div class="hero-badge">
                    ⚡ AUTONOMOUS AI SOFTWARE ENGINEERING
                </div>

                <div class="main-title">
                    Build Software With AI Agents
                </div>

                <div class="main-subtitle">
                    AgentForge transforms software requirements
                    into structured, tested and documented
                    software projects using a multi-agent
                    engineering pipeline.
                </div>

            </div>

        </div>
        """
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        render_html(
            """
            <div class="feature-card">

                <div class="feature-icon">🧠</div>

                <h3>AI-Powered Engineering</h3>

                <p>
                    Specialized AI agents handle requirements,
                    architecture, development, testing,
                    debugging, review and documentation.
                </p>

            </div>
            """
        )

    with col2:

        render_html(
            """
            <div class="feature-card">

                <div class="feature-icon">⚙️</div>

                <h3>Automated Development</h3>

                <p>
                    Transform natural-language software
                    requirements into structured project
                    outputs and generated source files.
                </p>

            </div>
            """
        )

    with col3:

        render_html(
            """
            <div class="feature-card">

                <div class="feature-icon">📦</div>

                <h3>Isolated Projects</h3>

                <p>
                    Every project has its own workspace,
                    conversations, generated files,
                    documentation and activity history.
                </p>

            </div>
            """
        )

    st.markdown(
        '<div class="section-title">How AgentForge Works</div>',
        unsafe_allow_html=True
    )

    agents = [
        ("1", "Requirements Analysis"),
        ("2", "Architect"),
        ("3", "Developer"),
        ("4", "Tester"),
        ("5", "Debugger"),
        ("6", "Code Reviewer"),
        ("7", "Documentation")
    ]

    for number, agent_name in agents:

        render_html(
            f"""
            <div class="agent-box">

                <div class="agent-number">
                    {number}
                </div>

                <div class="agent-name">
                    {agent_name}
                </div>

            </div>
            """
        )

    st.markdown(
        '<div class="section-title">Start Building</div>',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(
        [1, 2, 1]
    )

    with col2:

        if st.session_state.logged_in:

            if st.button(
                "🚀 Open My Projects",
                use_container_width=True,
                key="home_projects_button"
            ):

                go_dashboard()
                st.rerun()

        else:

            if st.button(
                "🚀 Get Started",
                use_container_width=True,
                key="home_get_started"
            ):

                go_register()
                st.rerun()


# ============================================================
# LOGIN PAGE
# ============================================================

def show_login():

    navbar()

    st.markdown(
        '<div class="section-title">🔐 Login to AgentForge</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Access your projects and continue building with AI agents."
    )

    email = st.text_input(
        "Email Address",
        key="login_email"
    )

    password = st.text_input(
        "Password",
        type="password",
        key="login_password"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🔐 Login",
            use_container_width=True,
            key="login_button"
        ):

            if not email or not password:

                st.error(
                    "Please enter email and password."
                )

                return

            connection = get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    email,
                    password
                FROM users
                WHERE email = ?
                """,
                (
                    email.strip(),
                )
            )

            user = cursor.fetchone()

            if not user:

                connection.close()

                st.error(
                    "Invalid email or password."
                )

                return

            hashed = hash_password(
                password
            )

            valid = (
                user[3] == hashed
                or user[3] == password
            )

            if valid:

                if user[3] == password:

                    cursor.execute(
                        """
                        UPDATE users
                        SET password = ?
                        WHERE id = ?
                        """,
                        (
                            hashed,
                            user[0]
                        )
                    )

                    connection.commit()

                connection.close()

                st.session_state.logged_in = True
                st.session_state.user_id = user[0]
                st.session_state.user_name = user[1]
                st.session_state.user_email = user[2]
                st.session_state.page = "dashboard"

                st.success(
                    "Login successful!"
                )

                st.rerun()

            else:

                connection.close()

                st.error(
                    "Invalid email or password."
                )

    with col2:

        if st.button(
            "✨ Create Account",
            use_container_width=True,
            key="login_register_button"
        ):

            go_register()
            st.rerun()


# ============================================================
# REGISTRATION PAGE
# ============================================================

def show_register():

    navbar()

    st.markdown(
        '<div class="section-title">✨ Create AgentForge Account</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Create an account to manage your AI-powered software projects."
    )

    name = st.text_input(
        "Full Name",
        key="register_name"
    )

    email = st.text_input(
        "Email Address",
        key="register_email"
    )

    password = st.text_input(
        "Password",
        type="password",
        key="register_password"
    )

    confirm_password = st.text_input(
        "Confirm Password",
        type="password",
        key="register_confirm_password"
    )

    if st.button(
        "🚀 Create Account",
        use_container_width=True,
        key="register_button"
    ):

        if not name.strip():

            st.error(
                "Full name is required."
            )

            return

        if not email.strip():

            st.error(
                "Email address is required."
            )

            return

        if not password:

            st.error(
                "Password is required."
            )

            return

        if len(password) < 6:

            st.error(
                "Password must contain at least 6 characters."
            )

            return

        if password != confirm_password:

            st.error(
                "Passwords do not match."
            )

            return

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (
                email.strip(),
            )
        )

        if cursor.fetchone():

            connection.close()

            st.error(
                "An account with this email already exists."
            )

            return

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
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
        )

        connection.commit()

        connection.close()

        st.success(
            "Account created successfully. You can now login."
        )


# ============================================================
# DASHBOARD
# ============================================================

def show_dashboard():

    navbar()

    # ---------------------------------------------------------
    # CHECK LOGIN
    # ---------------------------------------------------------

    if not st.session_state.get("logged_in", False):
        go_login()
        st.rerun()

    # ---------------------------------------------------------
    # TEMPORARY USER DEBUG
    # ---------------------------------------------------------

    st.write(
        "DEBUG USER ID:",
        st.session_state.get("user_id")
    )

    # ---------------------------------------------------------
    # PAGE TITLE
    # ---------------------------------------------------------

    st.markdown(
        '<div class="section-title">🚀 My Projects</div>',
        unsafe_allow_html=True
    )

    st.write(
        f"Welcome back, **{st.session_state.get('user_name', 'User')}**"
    )

    # ---------------------------------------------------------
    # SEARCH / STATUS / NEW PROJECT
    # ---------------------------------------------------------

    col1, col2, col3 = st.columns([3, 1.2, 1.3])

    with col1:
        search = st.text_input(
            "🔍 Search Projects",
            placeholder="Search by project name...",
            key="dashboard_search"
        )

    with col2:
        status_filter = st.selectbox(
            "Status",
            [
                "All",
                "Active",
                "Completed",
                "In Progress",
                "Archived"
            ],
            key="dashboard_status"
        )

    with col3:
        st.write("")

        if st.button(
            "➕ New Project",
            use_container_width=True,
            type="primary",
            key="dashboard_new_project"
        ):
            go_create_project()
            st.rerun()

    # ---------------------------------------------------------
    # GET USER PROJECTS
    # ---------------------------------------------------------

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
        WHERE user_id = ?
        ORDER BY updated_at DESC
        """,
        (
            st.session_state.get("user_id"),
        )
    )

    projects = cursor.fetchall()

    connection.close()

    # ---------------------------------------------------------
    # FILTER PROJECTS
    # ---------------------------------------------------------

    filtered_projects = []

    for project in projects:

        project_id = project[0]
        name = project[1] or ""
        description = project[2] or ""
        status = project[8]

        if search:

            search_text = search.lower()

            if (
                search_text not in name.lower()
                and search_text not in description.lower()
            ):
                continue

        if status_filter != "All":

            if status != status_filter:
                continue

        filtered_projects.append(project)

    # ---------------------------------------------------------
    # NO PROJECTS
    # ---------------------------------------------------------

    if not filtered_projects:

        st.info("No projects found.")

        if st.button(
            "➕ Create Your First Project",
            type="primary",
            key="create_first_project"
        ):
            go_create_project()
            st.rerun()

        return

    # ---------------------------------------------------------
    # DISPLAY PROJECTS
    # ---------------------------------------------------------

    for project in filtered_projects:

        project_id = project[0]
        name = project[1] or "Untitled Project"
        description = project[2] or "No description provided."
        requirements = project[3] or ""
        category = project[4] or "Web Application"
        language = project[5] or "Not specified"
        framework = project[6] or "Not specified"
        database = project[7] or "Not specified"
        status = project[8] or "Active"
        created_at = project[9]
        updated_at = project[10]

        # -----------------------------------------------------
        # PROJECT CARD
        # -----------------------------------------------------

        st.html(
            f"""
            <div style="
                font-size:22px;
                font-weight:700;
                color:#0f172a;
                margin-bottom:12px;
            ">
                📁 {name}
            </div>

            <div style="
                font-size:16px;
                color:#64748b;
                margin-bottom:15px;
            ">
                {description}
            </div>

            <span style="
                display:inline-block;
                background:#dcfce7;
                color:#166534;
                padding:8px 16px;
                border-radius:20px;
                font-size:14px;
                font-weight:600;
            ">
                {status}
            </span>
            """
        )

        st.caption(
            f"📁 {category}  •  "
            f"💻 {language}  •  "
            f"⚡ {framework}  •  "
            f"🗄️ {database}"
        )

        st.caption(
            f"🕘 Updated: {updated_at}"
        )

        # =====================================================
        # PROJECT ACTION BUTTONS
        # =====================================================

        col_open, col_rename, col_edit, col_duplicate, col_delete = st.columns(
            [1.4, 1, 1, 1.2, 1]
        )

        # -----------------------------------------------------
        # OPEN PROJECT
        # -----------------------------------------------------

        with col_open:

            if st.button(
                "🚀 Open Project →",
                use_container_width=True,
                type="primary",
                key=f"open_project_{project_id}"
            ):

                st.session_state.current_project_id = project_id
                st.session_state.page = "workspace"
                st.session_state.pipeline_result = None

                st.rerun()

        # -----------------------------------------------------
        # RENAME
        # -----------------------------------------------------

        with col_rename:

            if st.button(
                "✏️ Rename",
                use_container_width=True,
                key=f"rename_project_{project_id}"
            ):

                st.session_state.rename_project_id = project_id
                st.session_state.edit_project_id = None
                st.session_state.delete_project_id = None

                st.rerun()

        # -----------------------------------------------------
        # EDIT
        # -----------------------------------------------------

        with col_edit:

            if st.button(
                "⚙️ Edit",
                use_container_width=True,
                key=f"edit_project_{project_id}"
            ):

                st.session_state.edit_project_id = project_id
                st.session_state.rename_project_id = None
                st.session_state.delete_project_id = None

                st.rerun()

        # -----------------------------------------------------
        # DUPLICATE
        # -----------------------------------------------------

        with col_duplicate:

            if st.button(
                "📋 Duplicate",
                use_container_width=True,
                key=f"duplicate_project_{project_id}"
            ):

                st.session_state.duplicate_project_id = project_id
                st.rerun()

        # -----------------------------------------------------
        # DELETE
        # -----------------------------------------------------

        with col_delete:

            if st.button(
                "🗑️ Delete",
                use_container_width=True,
                key=f"delete_project_{project_id}"
            ):

                st.session_state.delete_project_id = project_id
                st.session_state.rename_project_id = None
                st.session_state.edit_project_id = None

                st.rerun()

        st.divider()

# ============================================================
# CREATE PROJECT
# ============================================================

def show_create_project():

    navbar()

    if not st.session_state.logged_in:

        go_login()
        st.rerun()

    st.markdown(
        '<div class="section-title">✨ Create New Project</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Define your project and let AgentForge build the engineering workflow."
    )

    name = st.text_input(
        "Project Name",
        placeholder="Example: Student Management System",
        key="create_project_name"
    )

    description = st.text_area(
        "Project Description",
        placeholder="Describe what the project should do...",
        key="create_project_description"
    )

    requirements = st.text_area(
        "Requirements",
        placeholder="Enter the functional and technical requirements...",
        height=180,
        key="create_project_requirements"
    )

    category = st.selectbox(
        "Project Category",
        [
            "Web Application",
            "Desktop Application",
            "Mobile Application",
            "API",
            "Automation",
            "Data Science",
            "AI / Machine Learning",
            "Other"
        ],
        key="create_project_category"
    )

    programming_language = st.selectbox(
        "Programming Language",
        [
            "Python",
            "Java",
            "JavaScript",
            "TypeScript",
            "C++",
            "C#",
            "Other"
        ],
        key="create_project_language"
    )

    framework = st.text_input(
        "Framework",
        placeholder="Example: Streamlit, Django, Spring Boot, React",
        key="create_project_framework"
    )

    database = st.text_input(
        "Database",
        placeholder="Example: SQLite, MySQL, PostgreSQL",
        key="create_project_database"
    )

    additional_instructions = st.text_area(
        "Additional Instructions",
        placeholder="Any additional instructions for the AI agents...",
        key="create_project_instructions"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🚀 Create Project",
            use_container_width=True,
            key="create_project_button"
        ):

            if not name.strip():

                st.error(
                    "Project name is required."
                )

                return

            if not description.strip():

                st.error(
                    "Project description is required."
                )

                return

            if not requirements.strip():

                st.error(
                    "Project requirements are required."
                )

                return

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
                    name.strip()
                )
            )

            if cursor.fetchone():

                connection.close()

                st.error(
                    "A project with this name already exists."
                )

                return

            combined_requirements = (
                requirements.strip()
            )

            if additional_instructions.strip():

                combined_requirements += (
                    "\n\nAdditional Instructions:\n"
                    + additional_instructions.strip()
                )

            now = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
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
                    name.strip(),
                    description.strip(),
                    combined_requirements,
                    category,
                    programming_language,
                    framework.strip(),
                    database.strip(),
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
                    f"Project '{name.strip()}' created",
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

            readme = (
                project_folder
                / "README.md"
            )

            readme.write_text(
                f"# {name.strip()}\n\n"
                f"{description.strip()}\n\n"
                f"## Requirements\n\n"
                f"{combined_requirements}\n",
                encoding="utf-8"
            )

            st.session_state.current_project_id = project_id

            st.session_state.page = "workspace"

            st.success(
                "Project created successfully!"
            )

            st.rerun()

    with col2:

        if st.button(
            "Cancel",
            use_container_width=True,
            key="create_project_cancel"
        ):

            go_dashboard()
            st.rerun()


# ============================================================
# GET CURRENT PROJECT
# ============================================================

def get_current_project():

    project_id = (
        st.session_state.current_project_id
    )

    if not project_id:

        return None

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
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

    if not project:

        return None

    return {
        "id": project[0],
        "user_id": project[1],
        "name": project[2],
        "description": project[3],
        "requirements": project[4],
        "category": project[5],
        "programming_language": project[6],
        "framework": project[7],
        "database": project[8],
        "status": project[9],
        "created_at": project[10],
        "updated_at": project[11]
    }


# ============================================================
# WORKSPACE HEADER
# ============================================================

def workspace_header(project):

    render_html(
        f"""
        <div class="workspace-header">

            <h1 style="
                margin:0;
                font-size:32px;
                color:#172033;
            ">
                🚀 {project["name"]}
            </h1>

            <p style="
                color:#64748b;
                margin-top:10px;
                margin-bottom:0;
            ">
                {
                    project["description"]
                    or "No project description."
                }
            </p>

        </div>
        """
    )

    col1, col2, col3 = st.columns(
        [3, 1, 1]
    )

    with col1:

        st.caption(
            f"📂 {project['category']}   •   "
            f"💻 {project['programming_language']}   •   "
            f"⚡ {project['framework'] or 'No framework'}   •   "
            f"🗄️ {project['database'] or 'No database'}"
        )

    with col2:

        if st.button(
            "← Projects",
            key=f"workspace_projects_{project['id']}"
        ):

            go_dashboard()
            st.rerun()

    with col3:

        if st.button(
            "Logout",
            key=f"workspace_logout_{project['id']}"
        ):

            logout()
            st.rerun()

    st.divider()


# ============================================================
# PROJECT CHAT
# ============================================================

def show_project_chat(project):

    st.subheader("💬 Project Chat")

    st.write(
        "Discuss requirements, implementation and development "
        "ideas with the AgentForge AI assistant."
    )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            role,
            message,
            created_at
        FROM project_messages
        WHERE project_id = ?
        ORDER BY id ASC
        """,
        (
            project["id"],
        )
    )

    messages = cursor.fetchall()

    connection.close()

    if not messages:

        st.info(
            "No messages yet. Start the conversation below."
        )

    for role, message, created_at in messages:

        with st.chat_message(
            "user"
            if role == "user"
            else "assistant"
        ):

            if role == "user":

                st.write(
                    message
                )

            else:

                st.markdown(
                    message
                )

    prompt = st.chat_input(
        "Ask AgentForge about your project...",
        key=f"project_chat_input_{project['id']}"
    )

    if prompt:

        prompt = prompt.strip()

        if not prompt:

            return

        now = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

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
                project["id"],
                "user",
                prompt,
                now
            )
        )

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
                project["id"],
                "chat_sent",
                "User sent a project chat message",
                now
            )
        )

        connection.commit()

        connection.close()

        conversation_text = ""

        for role, message, created_at in messages[-10:]:

            conversation_text += (
                f"{role.upper()}: {message}\n"
            )

        project_context = f"""
You are the AI Chat Assistant inside AgentForge.

You are helping the user with ONE specific software project.

PROJECT ID:
{project["id"]}

PROJECT NAME:
{project["name"]}

PROJECT DESCRIPTION:
{project["description"]}

PROJECT REQUIREMENTS:
{project["requirements"]}

CATEGORY:
{project["category"]}

PROGRAMMING LANGUAGE:
{project["programming_language"]}

FRAMEWORK:
{project["framework"] or "Not specified"}

DATABASE:
{project["database"] or "Not specified"}

PROJECT STATUS:
{project["status"]}

PREVIOUS CONVERSATION:
{conversation_text or "No previous conversation."}

USER'S NEW MESSAGE:
{prompt}

Instructions:
- Answer specifically for this project.
- Use the project requirements and technology stack.
- Give practical software engineering guidance.
- If code is requested, provide useful code.
- Do not claim code was executed unless it was actually executed.
"""

        try:

            with st.spinner(
                "🤖 AgentForge AI is thinking..."
            ):

                ai_client = GeminiClient()

                ai_response = ai_client.generate(
                    project_context
                )

        except Exception as error:

            ai_response = (
                "⚠️ **AI response failed.**\n\n"
                f"`{error}`"
            )

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
                project["id"],
                "assistant",
                ai_response,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
        )

        connection.commit()

        connection.close()

        st.rerun()

    if messages:

        if st.button(
            "🗑️ Clear Chat",
            key=f"clear_chat_{project['id']}"
        ):

            connection = get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM project_messages
                WHERE project_id = ?
                """,
                (
                    project["id"],
                )
            )

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
                    project["id"],
                    "chat_cleared",
                    "Project chat history cleared",
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )
            )

            connection.commit()

            connection.close()

            st.rerun()


# ============================================================
# REQUIREMENTS
# ============================================================

def show_project_requirements(project):

    st.subheader("📋 Requirements")

    render_html(
        f"""
        <div class="project-card">

            <h3>🎯 Project Description</h3>

            <p style="
                color:#64748b;
                line-height:1.7;
            ">
                {project["description"]}
            </p>

        </div>
        """
    )

    st.markdown(
        "### 📝 Project Requirements"
    )

    st.write(
        project["requirements"]
    )

    st.markdown(
        "### 🧩 Technology Stack"
    )

    col1, col2 = st.columns(2)

    with col1:

        st.info(
            f"📂 **Category**\n\n"
            f"{project['category']}"
        )

        st.info(
            f"💻 **Programming Language**\n\n"
            f"{project['programming_language']}"
        )

    with col2:

        st.info(
            f"⚡ **Framework**\n\n"
            f"{project['framework'] or 'Not specified'}"
        )

        st.info(
            f"🗄️ **Database**\n\n"
            f"{project['database'] or 'Not specified'}"
        )


# ============================================================
# AGENT PIPELINE
# ============================================================

def show_agent_pipeline(project):

    st.subheader("🤖 Agent Pipeline")

    st.write(
        "Run the complete seven-stage AgentForge "
        "software engineering pipeline."
    )

    agents = [
        ("1", "Requirements Analysis", "requirements_analysis"),
        ("2", "Architect", "architect"),
        ("3", "Developer", "developer"),
        ("4", "Tester", "tester"),
        ("5", "Debugger", "debugger"),
        ("6", "Code Reviewer", "code_reviewer"),
        ("7", "Documentation", "documentation")
    ]

    # -----------------------------------------
    # DISPLAY AGENT PIPELINE
    # -----------------------------------------

    for number, agent_name, agent_key in agents:

        render_html(
            f"""
            <div class="agent-box">

                <div class="agent-number">
                    {number}
                </div>

                <div class="agent-name">
                    {agent_name}
                </div>

            </div>
            """
        )

    st.divider()

    # -----------------------------------------
    # RUN PIPELINE BUTTON
    # -----------------------------------------

    if st.button(
        "▶️ Run Agent Pipeline",
        use_container_width=True,
        key=f"run_pipeline_{project['id']}"
    ):

        pipeline = AgentPipeline(project)

        add_history(
            project["id"],
            "pipeline_started",
            "Agent pipeline execution started."
        )

        try:

            with st.spinner(
                "⚙️ Running AgentForge pipeline..."
            ):

                result = pipeline.run()

            # Store result
            st.session_state.pipeline_result = {
                "success": not bool(pipeline.errors),
                "results": result,
                "errors": pipeline.errors
            }

            add_history(
                project["id"],
                "pipeline_completed",
                "Agent pipeline execution completed successfully."
            )

            st.success(
                "✅ Agent pipeline completed successfully."
            )

        except Exception as error:

            st.session_state.pipeline_result = {
                "success": False,
                "results": {},
                "errors": {
                    "pipeline": str(error)
                }
            }

            st.error(
                f"❌ Pipeline execution failed: {error}"
            )

    # -----------------------------------------
    # GET PREVIOUS PIPELINE RESULT
    # -----------------------------------------

    result = st.session_state.get(
        "pipeline_result"
    )

    if not result:

        st.info(
            "No pipeline has been executed yet. "
            "Click Run Agent Pipeline to start."
        )

        return

    # -----------------------------------------
    # PIPELINE RESULT
    # -----------------------------------------

    st.divider()

    st.subheader("📊 Pipeline Result")

    if result.get("success"):

        st.success(
            "✅ All seven agents completed successfully."
        )

    else:

        st.warning(
            "⚠️ Pipeline completed with one or more errors."
        )

    results = result.get(
        "results",
        {}
    )

    errors = result.get(
        "errors",
        {}
    )

    # -----------------------------------------
    # AGENT RESULTS
    # -----------------------------------------

    for number, agent_name, agent_key in agents:

        agent_output = results.get(
            agent_key
        )

        agent_error = errors.get(
            agent_key
        )

        if agent_error:

            status_icon = "❌"
            status_text = "Error"

        elif agent_output:

            status_icon = "✅"
            status_text = "Completed"

        else:

            status_icon = "⚪"
            status_text = "No Output"

        with st.expander(
            f"{number}. {agent_name} — "
            f"{status_icon} {status_text}"
        ):

            if agent_error:

                st.error(
                    agent_error
                )

            elif agent_output:

                st.markdown(
                    "### Agent Output"
                )

                st.write(
                    agent_output
                )

            else:

                st.info(
                    "No output was generated."
                )

    # -----------------------------------------
    # PIPELINE ERRORS
    # -----------------------------------------

    if errors:

        st.divider()

        st.subheader("⚠️ Pipeline Errors")

        for agent_name, error_message in errors.items():

            st.error(
                f"**{agent_name}:** {error_message}"
            )

    # -----------------------------------------
    # PIPELINE SUMMARY
    # -----------------------------------------

    st.divider()

    completed_count = sum(
        1
        for _, _, agent_key in agents
        if results.get(agent_key)
    )

    render_html(
        f"""
        <div class="project-card">

            <h3>📈 Pipeline Summary</h3>

            <p>
                <strong>Total Agents:</strong> 7
            </p>

            <p>
                <strong>Completed:</strong>
                {completed_count}
            </p>

            <p>
                <strong>Errors:</strong>
                {len(errors)}
            </p>

        </div>
        """
    )

# ============================================================
# GENERATED FILES
# ============================================================

def show_generated_files(project):

    st.subheader("📁 Generated Files")

    st.write(
        "Files generated specifically for this project."
    )

    project_folder = (
        GENERATED_PROJECTS_DIR
        / f"project_{project['id']}"
    )

    project_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    files = []

    for file_path in project_folder.rglob("*"):

        if file_path.is_file():

            relative_path = file_path.relative_to(
                project_folder
            )

            files.append(
                (
                    str(relative_path),
                    file_path
                )
            )

    files.sort(
        key=lambda item: item[0].lower()
    )

    if not files:

        st.info(
            "No generated files yet. "
            "Run the Agent Pipeline to generate project files."
        )

        return

    for relative_path, file_path in files:

        size = file_path.stat().st_size

        render_html(
            f"""
            <div class="file-card">

                <strong>
                    📄 {relative_path}
                </strong>

                <div style="
                    color:#64748b;
                    font-size:13px;
                    margin-top:5px;
                ">
                    {size:,} bytes
                </div>

            </div>
            """
        )

        col1, col2 = st.columns(2)

        with col1:

            if st.button(
                "👁️ View File",
                key=(
                    f"view_file_"
                    f"{project['id']}_"
                    f"{relative_path}"
                )
            ):

                try:

                    content = file_path.read_text(
                        encoding="utf-8"
                    )

                    extension = (
                        file_path.suffix.lower()
                    )

                    language_map = {
                        ".py": "python",
                        ".js": "javascript",
                        ".java": "java",
                        ".html": "html",
                        ".css": "css",
                        ".json": "json",
                        ".md": "markdown",
                        ".sql": "sql"
                    }

                    language = language_map.get(
                        extension,
                        "text"
                    )

                    st.code(
                        content,
                        language=language
                    )

                except Exception as error:

                    st.error(
                        f"Unable to read file: {error}"
                    )

        with col2:

            try:

                content = file_path.read_bytes()

                st.download_button(
                    "⬇️ Download",
                    data=content,
                    file_name=file_path.name,
                    key=(
                        f"download_file_"
                        f"{project['id']}_"
                        f"{relative_path}"
                    )
                )

            except Exception as error:

                st.error(
                    f"Unable to download file: {error}"
                )


# ============================================================
# DOCUMENTATION
# ============================================================

def show_documentation(project):

    st.subheader("📚 Documentation")

    st.write(
        "Project documentation generated by AgentForge."
    )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            content,
            updated_at
        FROM project_documentation
        WHERE project_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (
            project["id"],
        )
    )

    documentation = cursor.fetchone()

    connection.close()

    # -----------------------------------------
    # DOCUMENTATION FROM DATABASE
    # -----------------------------------------

    if documentation:

        content = documentation[0]
        updated_at = documentation[1]

        render_html(
            """
            <div class="project-card">

                <div class="status-badge">
                    Documentation Available
                </div>

            </div>
            """
        )

        st.markdown(
            content
        )

        st.caption(
            f"Last updated: {updated_at}"
        )

        st.download_button(
            label="📥 Download Documentation",
            data=content,
            file_name=f"{project['name']}_Documentation.md",
            mime="text/markdown",
            use_container_width=True,
            key=f"download_documentation_{project['id']}"
        )

    # -----------------------------------------
    # DOCUMENTATION FROM README
    # -----------------------------------------

    else:

        readme_path = (
            GENERATED_PROJECTS_DIR
            / f"project_{project['id']}"
            / "README.md"
        )

        if readme_path.exists():

            try:

                content = readme_path.read_text(
                    encoding="utf-8"
                )

                render_html(
                    """
                    <div class="project-card">

                        <div class="status-badge">
                            README Available
                        </div>

                    </div>
                    """
                )

                st.markdown(
                    content
                )

                st.caption(
                    "Documentation loaded from project README.md"
                )

                st.download_button(
                    label="📥 Download Documentation",
                    data=content,
                    file_name=f"{project['name']}_README.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key=f"download_readme_{project['id']}"
                )

            except Exception as error:

                st.error(
                    f"Unable to read documentation: {error}"
                )

        else:

            st.info(
                "Documentation will be generated by the "
                "Documentation Agent after the pipeline runs."
            )

# ============================================================
# HISTORY
# ============================================================

def show_project_history(project):

    st.subheader("🕘 Project History")

    st.write(
        "Activity and events associated with this project."
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
        (
            project["id"],
        )
    )

    history = cursor.fetchall()

    connection.close()

    if not history:

        st.info(
            "No project activity yet."
        )

        return

    for activity_type, description, created_at in history:

        render_html(
            f"""
            <div class="history-card">

                <strong>
                    ⚡ {activity_type}
                </strong>

                <p style="
                    color:#475569;
                    margin-top:7px;
                    margin-bottom:7px;
                ">
                    {description}
                </p>

                <span style="
                    color:#64748b;
                    font-size:13px;
                ">
                    🕒 {created_at}
                </span>

            </div>
            """
        )


# ============================================================
# SETTINGS
# ============================================================

def show_project_settings(project):

    project_id = project["id"]

    st.subheader("⚙️ Project Settings")

    st.write(
        "Manage project information, status, generated files "
        "and project data."
    )

    # --------------------------------------------------------
    # EDIT INFORMATION
    # --------------------------------------------------------

    st.markdown(
        "### ✏️ Edit Project Information"
    )

    language_options = [
        "Python",
        "Java",
        "JavaScript",
        "TypeScript",
        "C++",
        "C#",
        "Other"
    ]

    status_options = [
        "Active",
        "In Progress",
        "Completed",
        "Archived"
    ]

    current_language = (
        project["programming_language"]
    )

    current_status = project["status"]

    language_index = (
        language_options.index(
            current_language
        )
        if current_language in language_options
        else 0
    )

    status_index = (
        status_options.index(
            current_status
        )
        if current_status in status_options
        else 0
    )

    with st.form(
        f"project_settings_form_{project_id}"
    ):

        name = st.text_input(
            "Project Name",
            value=project["name"],
            key=f"settings_name_{project_id}"
        )

        description = st.text_area(
            "Description",
            value=project["description"] or "",
            key=f"settings_description_{project_id}"
        )

        language = st.selectbox(
            "Programming Language",
            language_options,
            index=language_index,
            key=f"settings_language_{project_id}"
        )

        framework = st.text_input(
            "Framework",
            value=project["framework"] or "",
            placeholder="Example: Streamlit, Django, Spring Boot, React",
            key=f"settings_framework_{project_id}"
        )

        database = st.text_input(
            "Database",
            value=project["database"] or "",
            placeholder="Example: SQLite, MySQL, PostgreSQL",
            key=f"settings_database_{project_id}"
        )

        status = st.selectbox(
            "Status",
            status_options,
            index=status_index,
            key=f"settings_status_{project_id}"
        )

        save_changes = st.form_submit_button(
            "💾 Save Changes",
            use_container_width=True
        )

        if save_changes:

            if not name.strip():

                st.error(
                    "Project name is required."
                )

                return

            if not description.strip():

                st.error(
                    "Project description is required."
                )

                return

            connection = get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT id
                FROM projects
                WHERE user_id = ?
                AND LOWER(name) = LOWER(?)
                AND id != ?
                """,
                (
                    st.session_state.user_id,
                    name.strip(),
                    project_id
                )
            )

            if cursor.fetchone():

                connection.close()

                st.error(
                    "Another project with this name already exists."
                )

                return

            now = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            cursor.execute(
                """
                UPDATE projects
                SET
                    name = ?,
                    description = ?,
                    programming_language = ?,
                    framework = ?,
                    database = ?,
                    status = ?,
                    updated_at = ?
                WHERE id = ?
                AND user_id = ?
                """,
                (
                    name.strip(),
                    description.strip(),
                    language,
                    framework.strip(),
                    database.strip(),
                    status,
                    now,
                    project_id,
                    st.session_state.user_id
                )
            )

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
                    "project_updated",
                    "Project settings updated",
                    now
                )
            )

            connection.commit()

            connection.close()

            st.success(
                "✅ Project settings updated successfully."
            )

            st.rerun()

    # --------------------------------------------------------
    # CURRENT INFORMATION
    # --------------------------------------------------------

    st.divider()

    st.markdown(
        "### 📊 Current Project Information"
    )

    col1, col2 = st.columns(2)

    with col1:

        render_html(
            f"""
            <div class="project-card">

                <strong>📁 Project</strong>

                <p>{project["name"]}</p>

                <strong>💻 Language</strong>

                <p>{project["programming_language"]}</p>

                <strong>⚡ Framework</strong>

                <p>
                    {project["framework"] or "Not specified"}
                </p>

            </div>
            """
        )

    with col2:

        render_html(
            f"""
            <div class="project-card">

                <strong>🗄️ Database</strong>

                <p>
                    {project["database"] or "Not specified"}
                </p>

                <strong>📌 Status</strong>

                <p>{project["status"]}</p>

                <strong>🕒 Updated</strong>

                <p>{project["updated_at"]}</p>

            </div>
            """
        )

    # --------------------------------------------------------
    # ARCHIVE / RESTORE
    # --------------------------------------------------------

    st.divider()

    st.markdown(
        "### 📦 Project Status"
    )

    if project["status"] == "Archived":

        if st.button(
            "♻️ Restore Project",
            use_container_width=True,
            key=f"restore_project_{project_id}"
        ):

            connection = get_connection()

            cursor = connection.cursor()

            now = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            cursor.execute(
                """
                UPDATE projects
                SET
                    status = 'Active',
                    updated_at = ?
                WHERE id = ?
                AND user_id = ?
                """,
                (
                    now,
                    project_id,
                    st.session_state.user_id
                )
            )

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
                    "project_restored",
                    "Project restored from archive",
                    now
                )
            )

            connection.commit()

            connection.close()

            st.success(
                "♻️ Project restored successfully."
            )

            st.rerun()

    else:

        if st.button(
            "📦 Archive Project",
            use_container_width=True,
            key=f"archive_project_{project_id}"
        ):

            connection = get_connection()

            cursor = connection.cursor()

            now = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            cursor.execute(
                """
                UPDATE projects
                SET
                    status = 'Archived',
                    updated_at = ?
                WHERE id = ?
                AND user_id = ?
                """,
                (
                    now,
                    project_id,
                    st.session_state.user_id
                )
            )

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
                    "project_archived",
                    "Project archived",
                    now
                )
            )

            connection.commit()

            connection.close()

            st.success(
                "📦 Project archived successfully."
            )

            st.rerun()

    # --------------------------------------------------------
    # CLEAR CHAT
    # --------------------------------------------------------

    st.divider()

    st.markdown(
        "### 🗑️ Project Data"
    )

    clear_chat_confirm = st.checkbox(
        "I confirm that I want to clear this project's chat.",
        key=f"confirm_clear_chat_{project_id}"
    )

    if st.button(
        "🗑️ Clear Project Chat",
        use_container_width=True,
        key=f"settings_clear_chat_{project_id}"
    ):

        if not clear_chat_confirm:

            st.error(
                "Please confirm before clearing the chat."
            )

        else:

            connection = get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM project_messages
                WHERE project_id = ?
                """,
                (
                    project_id,
                )
            )

            now = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

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
                    "Project chat history cleared from settings",
                    now
                )
            )

            connection.commit()

            connection.close()

            st.success(
                "🗑️ Project chat cleared."
            )

            st.rerun()

    # --------------------------------------------------------
    # DELETE GENERATED FILES
    # --------------------------------------------------------

    delete_files_confirm = st.checkbox(
        "I confirm that I want to delete generated project files.",
        key=f"confirm_delete_files_{project_id}"
    )

    if st.button(
        "🗑️ Delete Generated Files",
        use_container_width=True,
        key=f"settings_delete_files_{project_id}"
    ):

        if not delete_files_confirm:

            st.error(
                "Please confirm before deleting files."
            )

        else:

            ProjectStorage.delete_project_files(
                project_id
            )

            connection = get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM project_files
                WHERE project_id = ?
                """,
                (
                    project_id,
                )
            )

            now = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

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
                    "files_deleted",
                    "All generated project files deleted",
                    now
                )
            )

            connection.commit()

            connection.close()

            st.success(
                "🗑️ Generated files deleted."
            )

            st.rerun()

    # --------------------------------------------------------
    # DELETE PROJECT
    # --------------------------------------------------------

    st.divider()

    st.markdown(
        "### ⚠️ Danger Zone"
    )

    st.warning(
        "Deleting the project permanently removes its "
        "database record, chat history, documentation, "
        "activity history and generated files."
    )

    confirm_delete = st.checkbox(
        "I understand that this action cannot be undone.",
        key=f"confirm_delete_{project_id}"
    )

    if st.button(
        "🔥 Delete Project Permanently",
        type="primary",
        use_container_width=True,
        key=f"delete_project_{project_id}"
    ):

        if not confirm_delete:

            st.error(
                "Please confirm the deletion first."
            )

        else:

            ProjectStorage.delete_project_files(
                project_id
            )

            connection = get_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM projects
                WHERE id = ?
                AND user_id = ?
                """,
                (
                    project_id,
                    st.session_state.user_id
                )
            )

            connection.commit()

            connection.close()

            st.session_state.current_project_id = None

            st.session_state.pipeline_results = {}

            st.session_state.page = "dashboard"

            st.rerun()


# ============================================================
# PROJECT WORKSPACE
# ============================================================

def show_workspace():

    if not st.session_state.logged_in:

        go_login()
        st.rerun()

    project = get_current_project()

    if not project:

        st.error(
            "Project could not be found."
        )

        if st.button(
            "← Back to Projects",
            key="workspace_project_not_found"
        ):

            go_dashboard()
            st.rerun()

        return

    workspace_header(
        project
    )

    tabs = st.tabs(
        [
            "💬 Chat",
            "📋 Requirements",
            "🤖 Agent Pipeline",
            "📁 Generated Files",
            "📚 Documentation",
            "🕘 History",
            "⚙️ Settings"
        ]
    )

    with tabs[0]:

        show_project_chat(
            project
        )

    with tabs[1]:

        show_project_requirements(
            project
        )

    with tabs[2]:

        show_agent_pipeline(
            project
        )

    with tabs[3]:

        show_generated_files(
            project
        )

    with tabs[4]:

        show_documentation(
            project
        )

    with tabs[5]:

        show_project_history(
            project
        )

    with tabs[6]:

        show_project_settings(
            project
        )


# ============================================================
# APPLICATION ROUTER
# ============================================================

if st.session_state.page == "home":

    show_home()

elif st.session_state.page == "login":

    show_login()

elif st.session_state.page == "register":

    show_register()

elif st.session_state.page == "dashboard":

    show_dashboard()

elif st.session_state.page == "create_project":

    show_create_project()

elif st.session_state.page == "workspace":

    show_workspace()

else:

    show_home()