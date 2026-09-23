import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

try:
    from google import genai
except ImportError:
    genai = None


class GeminiClient:
    """
    AgentForge AI client.

    Supports:
    - Gemini
    - MOCK fallback

    The MOCK mode generates project-aware starter code without
    hard-coding one particular project.
    """

    def __init__(self):
        self.mode = os.getenv("AGENTFORGE_AI_MODE", "MOCK").upper()
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model_name = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.6-flash"
        )

        self.client = None

        if self.mode == "GEMINI" and genai and self.api_key:
            try:
                self.client = genai.Client(
                    api_key=self.api_key
                )
            except Exception as exc:
                print(f"Gemini initialization failed: {exc}")
                self.mode = "MOCK"

    # ============================================================
    # PUBLIC API
    # ============================================================

    def generate(self, prompt):
        """
        Generate an AI response.

        Gemini mode:
            Uses Gemini API.

        MOCK mode:
            Uses local project-aware responses.
        """

        if self.mode == "GEMINI" and self.client:
            return self._generate_with_gemini(prompt)

        return self._mock_response(prompt)

    # ============================================================
    # GEMINI
    # ============================================================

    def _generate_with_gemini(self, prompt):
        """Call Gemini with retry handling."""

        for attempt in range(3):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )

                if response and response.text:
                    return response.text

                return "Gemini returned an empty response."

            except Exception as exc:
                error_text = str(exc)

                is_retryable = (
                    "429" in error_text
                    or "503" in error_text
                    or "RESOURCE_EXHAUSTED" in error_text
                    or "UNAVAILABLE" in error_text
                )

                if not is_retryable:
                    print(f"Gemini error: {error_text}")
                    return self._mock_response(prompt)

                if attempt < 2:
                    wait_time = 5 * (attempt + 1)
                    print(
                        f"Gemini temporarily unavailable. "
                        f"Retrying in {wait_time} seconds..."
                    )
                    time.sleep(wait_time)

        print("Gemini unavailable. Using MOCK response.")
        return self._mock_response(prompt)

    # ============================================================
    # PROJECT CONTEXT
    # ============================================================

    def _extract_project_context(self, prompt):
        """Extract project information from AgentPipeline prompts."""

        text = str(prompt or "")

        return {
            "id": self._extract_field(text, "PROJECT ID"),
            "name": self._extract_field(
                text,
                "PROJECT NAME",
                "AgentForge Project"
            ),
            "description": self._extract_field(
                text,
                "DESCRIPTION"
            ),
            "requirements": self._extract_field(
                text,
                "REQUIREMENTS"
            ),
            "category": self._extract_field(
                text,
                "CATEGORY"
            ),
            "language": self._extract_field(
                text,
                "PROGRAMMING LANGUAGE",
                "Python"
            ),
            "framework": self._extract_field(
                text,
                "FRAMEWORK",
                "Streamlit"
            ),
            "database": self._extract_field(
                text,
                "DATABASE",
                "SQLite"
            ),
            "status": self._extract_field(
                text,
                "STATUS"
            )
        }

    def _extract_field(
        self,
        text,
        field_name,
        default=""
    ):
        """
        Extract a field from the PROJECT CONTEXT block.

        Stops at the next uppercase context label.
        """

        pattern = (
            rf"{re.escape(field_name)}:\s*"
            rf"(.*?)(?=\n[A-Z][A-Z ]+:\s*|\Z)"
        )

        match = re.search(
            pattern,
            text,
            re.IGNORECASE | re.DOTALL
        )

        if not match:
            return default

        value = match.group(1).strip()

        return value if value else default

    # ============================================================
    # MOCK ROUTER
    # ============================================================

    def _mock_response(self, prompt):
        """Route a prompt to the appropriate mock agent."""

        text = str(prompt or "").lower()

        if "requirements analysis" in text:
            return self._mock_requirements_analysis(prompt)

        if "architect agent" in text or "architecture" in text:
            return self._mock_architect(prompt)

        if "developer agent" in text:
            return self._mock_developer(prompt)

        if "tester agent" in text:
            return self._mock_tester(prompt)

        if "debugger agent" in text:
            return self._mock_debugger(prompt)

        if "code reviewer" in text:
            return self._mock_code_reviewer(prompt)

        if "documentation agent" in text:
            return self._mock_documentation(prompt)

        return self._mock_chat(prompt)

    # ============================================================
    # REQUIREMENTS AGENT
    # ============================================================

    def _mock_requirements_analysis(self, prompt):
        project = self._extract_project_context(prompt)

        name = project["name"]
        description = project["description"]
        requirements = project["requirements"]

        return f"""
# Requirements Analysis

## Project
{name}

## Description
{description}

## Functional Requirements
{requirements}

## Non-Functional Requirements
- User-friendly interface
- Input validation
- Error handling
- Persistent database storage
- Modular project structure
- Maintainable source code
- Testable application components

## Suggested Roles
- Administrator
- Application User

## Core Features
The application should implement the features specified in the
project requirements.

## Constraints
- Programming Language: {project["language"]}
- Framework: {project["framework"]}
- Database: {project["database"]}

## Expected Output
A working application implementing the requested functionality.
"""

    # ============================================================
    # ARCHITECT AGENT
    # ============================================================

    def _mock_architect(self, prompt):
        project = self._extract_project_context(prompt)

        name = project["name"]

        return f"""
# Architecture Design

## Project
{name}

## Architecture

The application will use a modular architecture consisting of:

1. Presentation Layer
2. Application Logic Layer
3. Data Access Layer
4. Database Layer
5. Testing Layer

## Technology Stack

- Language: {project["language"]}
- Framework: {project["framework"]}
- Database: {project["database"]}

## Suggested Structure

{name.replace(" ", "_")}/
├── app.py
├── requirements.txt
├── README.md
├── database/
│   └── application.db
└── tests/
    └── test_app.py

## Design Principles

- Separation of concerns
- Reusable functions
- Input validation
- Database isolation
- Clear error handling
- Testability
"""

    # ============================================================
    # DEVELOPER AGENT
    # ============================================================

    def _mock_developer(self, prompt):
        """
        Generate project-aware source files.

        The MOCK generator creates a generic CRUD-style starter
        application based on the current project's name and
        requirements.
        """

        project = self._extract_project_context(prompt)

        name = project["name"]
        description = project["description"]
        requirements = project["requirements"]
        framework = project["framework"]
        database = project["database"]

        framework_lower = framework.lower()

        if "flask" in framework_lower:
            return self._generate_flask_project(
                name,
                description,
                requirements,
                database
            )

        return self._generate_streamlit_project(
            name,
            description,
            requirements,
            database
        )

    # ============================================================
    # STREAMLIT GENERATOR
    # ============================================================

    def _generate_streamlit_project(
        self,
        name,
        description,
        requirements,
        database
    ):
        title = self._safe_text(name)
        desc = self._safe_text(description)
        req = self._safe_text(requirements)

        table_name = self._table_name(name)

        app_code = f'''import sqlite3
from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "{table_name}.db"


def get_connection():
    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )
    return connection


def initialize_database():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT
        )
        """
    )

    connection.commit()
    connection.close()


def add_record(name, description):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO records(name, description)
        VALUES (?, ?)
        """,
        (name, description)
    )

    connection.commit()
    connection.close()


def get_records():
    connection = get_connection()

    records = connection.execute(
        """
        SELECT id, name, description
        FROM records
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return records


def update_record(record_id, name, description):
    connection = get_connection()

    connection.execute(
        """
        UPDATE records
        SET name = ?, description = ?
        WHERE id = ?
        """,
        (name, description, record_id)
    )

    connection.commit()
    connection.close()


def delete_record(record_id):
    connection = get_connection()

    connection.execute(
        """
        DELETE FROM records
        WHERE id = ?
        """,
        (record_id,)
    )

    connection.commit()
    connection.close()


def main():
    initialize_database()

    st.set_page_config(
        page_title="{title}",
        page_icon="🚀",
        layout="wide"
    )

    st.title("🚀 {title}")
    st.write("{desc}")

    st.info(
        "Requirements: {req}"
    )

    tab_add, tab_view, tab_update, tab_delete = st.tabs(
        [
            "Add",
            "View",
            "Update",
            "Delete"
        ]
    )

    with tab_add:
        st.subheader("Add Record")

        name = st.text_input(
            "Name",
            key="add_name"
        )

        description = st.text_area(
            "Description",
            key="add_description"
        )

        if st.button(
            "Add Record",
            use_container_width=True
        ):
            if not name.strip():
                st.error("Name is required.")
            else:
                add_record(
                    name.strip(),
                    description.strip()
                )

                st.success(
                    "Record added successfully."
                )

                st.rerun()

    with tab_view:
        st.subheader("View Records")

        records = get_records()

        if records:
            for record in records:
                st.markdown(
                    f"### {{record[1]}}"
                )

                st.write(
                    record[2] or "No description"
                )

                st.divider()
        else:
            st.info("No records available.")

    with tab_update:
        st.subheader("Update Record")

        records = get_records()

        if records:
            record_map = {{
                record[0]: record
                for record in records
            }}

            selected_id = st.selectbox(
                "Select Record",
                list(record_map.keys()),
                key="update_record_select"
            )

            selected = record_map[selected_id]

            name = st.text_input(
                "Name",
                value=selected[1],
                key="update_name"
            )

            description = st.text_area(
                "Description",
                value=selected[2] or "",
                key="update_description"
            )

            if st.button(
                "Update Record",
                use_container_width=True
            ):
                update_record(
                    selected_id,
                    name.strip(),
                    description.strip()
                )

                st.success(
                    "Record updated successfully."
                )

                st.rerun()
        else:
            st.info("No records available.")

    with tab_delete:
        st.subheader("Delete Record")

        records = get_records()

        if records:
            record_map = {{
                record[0]: record
                for record in records
            }}

            selected_id = st.selectbox(
                "Select Record",
                list(record_map.keys()),
                key="delete_record_select"
            )

            if st.button(
                "Delete Record",
                use_container_width=True
            ):
                delete_record(selected_id)

                st.success(
                    "Record deleted successfully."
                )

                st.rerun()
        else:
            st.info("No records available.")


if __name__ == "__main__":
    main()
'''

        requirements_file = """streamlit
"""

        readme = f"""# {title}

## Description

{desc}

## Requirements

{req}

## Technology Stack

- Python
- Streamlit
- {database}

## Installation

```bash
pip install -r requirements.txt"""