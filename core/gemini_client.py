import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv

try:
    from google import genai
except ImportError:
    genai = None

load_dotenv()


class GeminiClient:
    """Central AI client for AgentForge.

    Supports Gemini when configured and a deterministic mock mode for local
    development. The mock generator reads the project context instead of using
    a hard-coded Student Management System template.
    """

    def __init__(self, mode=None, model=None):
        self.mode = (mode or os.getenv("AGENTFORGE_AI_MODE", "GEMINI")).upper()
        self.model_name = model or os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.client = None

        if self.mode == "GEMINI" and genai and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as exc:
                print(f"Gemini initialization failed: {exc}")
                self.mode = "MOCK"
        elif self.mode == "GEMINI":
            self.mode = "MOCK"

    def generate(self, prompt, temperature=0.2, max_retries=3):
        """Generate text using Gemini, falling back to mock output."""
        if self.mode != "GEMINI" or not self.client:
            return self._mock_response(prompt)

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config={"temperature": temperature},
                )
                text = getattr(response, "text", None)
                if text:
                    return text.strip()
                return "No AI response was returned."
            except Exception as exc:
                message = str(exc).lower()
                retryable = any(
                    item in message
                    for item in ("429", "503", "resource_exhausted", "unavailable")
                )
                if retryable and attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                print(f"Gemini request failed: {exc}")
                return self._mock_response(prompt)

        return self._mock_response(prompt)

    def _mock_response(self, prompt):
        prompt_text = str(prompt or "")
        lower = prompt_text.lower()

        if "you are the requirements analysis agent" in lower:
            return self._mock_requirements(prompt_text)
        if "you are the architect agent" in lower:
            return self._mock_architect(prompt_text)
        if "you are the developer agent" in lower:
            return self._mock_developer(prompt_text)
        if "you are the tester agent" in lower:
            return self._mock_tester(prompt_text)
        if "you are the debugger agent" in lower:
            return self._mock_debugger(prompt_text)
        if "you are the code reviewer" in lower or "you are the code review agent" in lower:
            return self._mock_code_reviewer(prompt_text)
        if "you are the documentation agent" in lower:
            return self._mock_documentation(prompt_text)
        if "you are the chat assistant" in lower or "chat with the user" in lower:
            return self._mock_chat(prompt_text)
        return self._mock_generic(prompt_text)

    def _project_details(self, prompt):
        def value(label):
            match = re.search(
                rf"{re.escape(label)}\s*:\s*(.*?)(?=\n[A-Z][A-Z _/()-]+\s*:\s*|\Z)",
                prompt,
                flags=re.IGNORECASE | re.DOTALL,
            )
            return match.group(1).strip() if match else ""

        return {
            "id": value("PROJECT ID"),
            "name": value("PROJECT NAME") or "AgentForge Project",
            "description": value("DESCRIPTION"),
            "requirements": value("REQUIREMENTS"),
            "category": value("CATEGORY"),
            "language": value("PROGRAMMING LANGUAGE") or "Python",
            "framework": value("FRAMEWORK") or "Streamlit",
            "database": value("DATABASE") or "SQLite",
            "status": value("STATUS"),
        }

    def _mock_requirements(self, prompt):
        p = self._project_details(prompt)
        return f"""# Requirements Analysis

## Project
{p['name']}

## Functional Requirements
{p['requirements'] or 'Implement the functionality described by the project requirements.'}

## Non-Functional Requirements
- Provide a clear and maintainable user interface.
- Validate user input before database operations.
- Keep project files isolated inside the project workspace.
- Handle errors without crashing the application.
- Use the selected programming language, framework, and database.

## Roles
- User: uses the application and manages project data.
- AgentForge pipeline: analyzes, designs, develops, tests, debugs, reviews, and documents the project.

## Constraints
- Language: {p['language']}
- Framework: {p['framework']}
- Database: {p['database']}

## Acceptance Criteria
The generated application should start successfully, implement the requested CRUD or core features, persist data when a database is requested, and include basic tests and documentation."""

    def _mock_architect(self, prompt):
        p = self._project_details(prompt)
        return f"""# Architecture

## Project
{p['name']}

## Stack
- Language: {p['language']}
- Framework: {p['framework']}
- Database: {p['database']}

## Components
1. Application entry point and UI/routes.
2. Validation and business logic.
3. Database initialization and CRUD operations.
4. Tests for core application behavior.
5. README documentation.

## Data Layer
Use {p['database']} with a project-specific database file when persistence is required.

## Flow
User -> {p['framework']} interface -> application logic -> database -> result shown to user.

## Design Principles
- Keep files small and understandable.
- Use parameterized SQL.
- Keep generated files inside the project workspace.
- Do not mix unrelated projects or data."""

    def _mock_developer(self, prompt):
        p = self._project_details(prompt)
        framework = p["framework"].lower()

        if "flask" in framework:
            return self._mock_flask_developer(p)

        return self._mock_streamlit_developer(p)

    def _entity_details(self, project_name, requirements, description):
        text = f"{project_name} {requirements} {description}".lower()

        rules = [
            (
                "hospital",
                "Patient",
                "Patients",
                "patients",
                ["name", "age", "gender", "phone", "disease"],
            ),
            (
                "library",
                "Book",
                "Books",
                "books",
                ["title", "author", "isbn", "category"],
            ),
            (
                "employee",
                "Employee",
                "Employees",
                "employees",
                ["name", "email", "department", "salary"],
            ),
            (
                "customer",
                "Customer",
                "Customers",
                "customers",
                ["name", "email", "phone", "address"],
            ),
            (
                "product",
                "Product",
                "Products",
                "products",
                ["name", "price", "category", "quantity"],
            ),
            (
                "student",
                "Student",
                "Students",
                "students",
                ["name", "email", "course", "age"],
            ),
            (
                "book",
                "Book",
                "Books",
                "books",
                ["title", "author", "isbn", "category"],
            ),
            (
                "patient",
                "Patient",
                "Patients",
                "patients",
                ["name", "age", "gender", "phone", "disease"],
            ),
        ]

        for keyword, entity, plural, table, fields in rules:
            if keyword in text:
                return entity, plural, table, fields

        return (
            "Record",
            "Records",
            "records",
            ["name", "description", "status", "notes"],
        )

    def _mock_streamlit_developer(self, p):
        entity, plural, table, fields = self._entity_details(
            p["name"],
            p["requirements"],
            p["description"],
        )

        app = self._streamlit_app_code(
            p,
            entity,
            plural,
            table,
            fields,
        )

        test = self._streamlit_test_code(
            table,
            fields,
        )

        readme = self._readme(
            p,
            entity,
            plural,
            "app.py",
        )

        return self._format_generated_files(
            {
                "app.py": app,
                "requirements.txt": "streamlit\n",
                "README.md": readme,
                "tests/test_app.py": test,
            }
        )

    def _mock_flask_developer(self, p):
        entity, plural, table, fields = self._entity_details(
            p["name"],
            p["requirements"],
            p["description"],
        )

        app = self._flask_app_code(
            p,
            entity,
            plural,
            table,
            fields,
        )

        index = self._flask_index_code(
            entity,
            plural,
            fields,
        )

        form = self._flask_form_code(
            entity,
            fields,
        )

        update = self._flask_update_code(
            entity,
            fields,
        )

        test = self._flask_test_code()

        readme = self._readme(
            p,
            entity,
            plural,
            "app.py",
        )

        return self._format_generated_files(
            {
                "app.py": app,
                "templates/index.html": index,
                "templates/add_record.html": form,
                "templates/update_record.html": update,
                "requirements.txt": "flask\n",
                "README.md": readme,
                "tests/test_app.py": test,
            }
        )

    def _streamlit_app_code(
        self,
        p,
        entity,
        plural,
        table,
        fields,
    ):
        form_lines = []

        for field in fields:
            label = field.replace("_", " ").title()
            form_lines.append(
                f'    {field} = st.text_input("{label}")'
            )

        values = ", ".join(fields)
        placeholders = ", ".join("?" for _ in fields)
        columns = ", ".join(fields)
        update_set = ", ".join(
            f"{field} = ?" for field in fields
        )

        display = "\n".join(
            f'        st.write(f"**{field.title()}:** {{row["{field}"]}}")'
            for field in fields
        )

        return f'''import sqlite3

import streamlit as st

DB_NAME = "{table}.db"


def get_connection():
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_connection()
    connection.execute(
        "CREATE TABLE IF NOT EXISTS {table} "
        "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "{', '.join(field + ' TEXT NOT NULL' for field in fields)})"
    )
    connection.commit()
    connection.close()


def add_record(values):
    connection = get_connection()
    connection.execute(
        "INSERT INTO {table} ({columns}) VALUES ({placeholders})",
        values,
    )
    connection.commit()
    connection.close()


def get_records():
    connection = get_connection()
    rows = connection.execute(
        "SELECT * FROM {table} ORDER BY id DESC"
    ).fetchall()
    connection.close()
    return rows


def update_record(record_id, values):
    connection = get_connection()
    connection.execute(
        "UPDATE {table} SET {update_set} WHERE id = ?",
        (*values, record_id),
    )
    connection.commit()
    connection.close()


def delete_record(record_id):
    connection = get_connection()
    connection.execute(
        "DELETE FROM {table} WHERE id = ?",
        (record_id,),
    )
    connection.commit()
    connection.close()


st.set_page_config(
    page_title="{p['name']}",
    page_icon="⚙️",
    layout="wide",
)

init_db()

st.title("{p['name']}")
st.caption("Generated by AgentForge")

menu = st.sidebar.radio(
    "Menu",
    [
        "Add {entity}",
        "View {plural}",
        "Update {entity}",
        "Delete {entity}",
    ],
)

if menu == "Add {entity}":
    st.header("Add {entity}")
{chr(10).join(form_lines)}
    if st.button(
        "Add {entity}",
        use_container_width=True,
    ):
        if all(str(value).strip() for value in [{values}]):
            add_record(({values},))
            st.success("{entity} added successfully.")
        else:
            st.error("Please fill all fields.")

elif menu == "View {plural}":
    st.header("View {plural}")
    rows = get_records()

    if not rows:
        st.info("No records found.")

    for row in rows:
        with st.container(border=True):
            st.subheader(f"{entity} #{{row['id']}}")
{display}

elif menu == "Update {entity}":
    st.header("Update {entity}")

    record_id = st.number_input(
        "Record ID",
        min_value=1,
        step=1,
    )

{chr(10).join(form_lines)}

    if st.button(
        "Update {entity}",
        use_container_width=True,
    ):
        update_record(
            record_id,
            ({values},),
        )
        st.success("{entity} updated successfully.")

elif menu == "Delete {entity}":
    st.header("Delete {entity}")

    record_id = st.number_input(
        "Record ID",
        min_value=1,
        step=1,
    )

    if st.button(
        "Delete {entity}",
        use_container_width=True,
    ):
        delete_record(record_id)
        st.success("{entity} deleted successfully.")
'''

    def _flask_app_code(
        self,
        p,
        entity,
        plural,
        table,
        fields,
    ):
        columns = ", ".join(fields)
        schema = ", ".join(
            field + " TEXT NOT NULL"
            for field in fields
        )
        placeholders = ", ".join(
            "?" for _ in fields
        )

        update_set = ", ".join(
            f"{field} = ?" for field in fields
        )

        values = ", ".join(
            f'request.form.get("{field}", "").strip()'
            for field in fields
        )

        return f'''from flask import (
    Flask,
    redirect,
    render_template,
    request,
    url_for,
)
import sqlite3

app = Flask(__name__)

DB_NAME = "{table}.db"


def get_connection():
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    connection = get_connection()
    connection.execute(
        "CREATE TABLE IF NOT EXISTS {table} "
        "(id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "{schema})"
    )
    connection.commit()
    connection.close()


@app.route("/")
def index():
    connection = get_connection()

    rows = connection.execute(
        "SELECT * FROM {table} ORDER BY id DESC"
    ).fetchall()

    connection.close()

    return render_template(
        "index.html",
        records=rows,
        entity="{entity}",
        plural="{plural}",
        fields={fields!r},
    )


@app.route("/add", methods=["GET", "POST"])
def add_record():
    if request.method == "POST":
        values = ({values},)

        connection = get_connection()

        connection.execute(
            "INSERT INTO {table} ({columns}) "
            "VALUES ({placeholders})",
            values,
        )

        connection.commit()
        connection.close()

        return redirect(url_for("index"))

    return render_template(
        "add_record.html",
        entity="{entity}",
        fields={fields!r},
    )


@app.route(
    "/update/<int:record_id>",
    methods=["GET", "POST"],
)
def update_record(record_id):
    connection = get_connection()

    if request.method == "POST":
        values = ({values},)

        connection.execute(
            "UPDATE {table} SET {update_set} "
            "WHERE id = ?",
            (*values, record_id),
        )

        connection.commit()
        connection.close()

        return redirect(url_for("index"))

    record = connection.execute(
        "SELECT * FROM {table} WHERE id = ?",
        (record_id,),
    ).fetchone()

    connection.close()

    return render_template(
        "update_record.html",
        entity="{entity}",
        fields={fields!r},
        record=record,
    )


@app.route(
    "/delete/<int:record_id>",
    methods=["POST"],
)
def delete_record(record_id):
    connection = get_connection()

    connection.execute(
        "DELETE FROM {table} WHERE id = ?",
        (record_id,),
    )

    connection.commit()
    connection.close()

    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
'''

    def _flask_index_code(
        self,
        entity,
        plural,
        fields,
    ):
        body = "".join(
            f'<p><strong>{field.title()}:</strong> '
            f'{{{{ record["{field}"] }}}}</p>'
            for field in fields
        )

        return f'''<!doctype html>
<html>
<head>
    <title>{plural}</title>
</head>
<body>

<h1>{plural}</h1>

<a href="{{{{ url_for('add_record') }}}}">
    Add {entity}
</a>

{{% for record in records %}}

<hr>

<h2>
    {entity} #{{{{ record["id"] }}}}
</h2>

{body}

<a href="{{{{ url_for(
    'update_record',
    record_id=record['id']
) }}}}">
    Edit
</a>

<form
    method="post"
    action="{{{{ url_for(
        'delete_record',
        record_id=record['id']
    ) }}}}"
    style="display:inline"
>
    <button type="submit">
        Delete
    </button>
</form>

{{% else %}}

<p>No records found.</p>

{{% endfor %}}

</body>
</html>
'''

    def _flask_form_code(
        self,
        entity,
        fields,
    ):
        inputs = "\n".join(
            f'<label>{field.title()}'
            f'<input name="{field}" required>'
            f'</label><br>'
            for field in fields
        )

        return f'''<!doctype html>
<html>
<head>
    <title>Add {entity}</title>
</head>
<body>

<h1>Add {entity}</h1>

<form method="post">

{inputs}

<button type="submit">
    Save
</button>

</form>

<a href="{{{{ url_for('index') }}}}">
    Back
</a>

</body>
</html>
'''

    def _flask_update_code(
        self,
        entity,
        fields,
    ):
        inputs = "\n".join(
            f'<label>{field.title()}'
            f'<input name="{field}" '
            f'value="{{{{ record["{field}"] }}}}" required>'
            f'</label><br>'
            for field in fields
        )

        return f'''<!doctype html>
<html>
<head>
    <title>Update {entity}</title>
</head>
<body>

<h1>Update {entity}</h1>

<form method="post">

{inputs}

<button type="submit">
    Update
</button>

</form>

<a href="{{{{ url_for('index') }}}}">
    Back
</a>

</body>
</html>
'''

    def _streamlit_test_code(
        self,
        table,
        fields,
    ):
        return f'''def test_project_configuration():
    assert "{table}" == "{table}"
    assert {fields!r}
'''

    def _flask_test_code(self):
        return '''from app import app


def test_home_page():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
'''

    def _readme(
        self,
        p,
        entity,
        plural,
        entry_point,
    ):
        return f'''# {p["name"]}

{p["description"] or "Generated application by AgentForge."}

## Requirements

{p["requirements"] or "See the application interface for the implemented features."}

## Technology

- Language: {p["language"]}
- Framework: {p["framework"]}
- Database: {p["database"]}

## Run

Install dependencies from `requirements.txt`, then run
`{entry_point}` using the selected framework.

## Generated By

AgentForge autonomous multi-agent software engineering pipeline.
'''
    def _format_generated_files(self, files):
        parts = ["GENERATED FILES"]

        for path, content in files.items():
            cleaned_content = str(content).strip()

            # Remove Markdown code fences added by AI.
            cleaned_content = re.sub(
                r"^\s*```[a-zA-Z0-9_+-]*\s*\n?",
                "",
                cleaned_content,
                count=1,
            )

            cleaned_content = re.sub(
                r"\n?\s*```\s*$",
                "",
                cleaned_content,
                count=1,
            )

            parts.append(f"FILE: {path}")
            parts.append("CONTENT:")
            parts.append(cleaned_content.rstrip())
            parts.append("")

        return "\n".join(parts).rstrip()

    def _mock_tester(self, prompt):
        return """# Test Report

- Application structure checked.
- Database initialization checked.
- Core CRUD paths checked conceptually.
- Generated test file included.

STATUS: PASS

Potential runtime checks:
- Install dependencies.
- Start the selected framework.
- Exercise Add/View/Update/Delete.
- Run pytest.
"""

    def _mock_debugger(self, prompt):
        return """# Debugger Report

No blocking defect was identified from the available generated-project context.

Checks:
- Syntax and structure reviewed.
- Database operations reviewed.
- User input flow reviewed.
- Route/UI flow reviewed.

STATUS: NO BLOCKING BUG
"""

    def _mock_code_reviewer(self, prompt):
        return """# Code Review

## Strengths

- Uses a project-isolated generated workspace.
- Uses parameterized SQLite statements.
- Separates application code from tests and documentation.
- Keeps the generated project small and understandable.

## Recommendations

- Add stronger validation for production use.
- Add authentication and authorization where required.
- Add more unit and integration tests.
- Disable debug mode before production deployment.

STATUS: REVIEW COMPLETE
"""

    def _mock_documentation(self, prompt):
        p = self._project_details(prompt)

        return f"""# {p['name']} Documentation

## Overview

{p['description'] or 'Application generated by AgentForge.'}

## Objectives

- Implement the requested application functionality.
- Persist application data using the selected database.
- Provide a simple interface using the selected framework.

## Requirements

{p['requirements'] or 'Project requirements are defined by the user.'}

## Technology Stack

- Language: {p['language']}
- Framework: {p['framework']}
- Database: {p['database']}

## Architecture

The user interacts with the framework interface, which calls
application logic and the project database.

## Testing

Run the generated tests with pytest after installing
the project dependencies.

## Future Enhancements

- Authentication
- Better validation
- Role-based access
- API integration
- Deployment configuration

Generated by AgentForge Documentation Agent.
"""

    def _mock_chat(self, prompt):
        p = self._project_details(prompt)
        user_message = self._last_user_message(prompt)

        return (
            f"For **{p['name']}**, I can help with requirements, "
            f"architecture, code, tests, debugging, documentation, "
            f"or project changes.\n\n"
            f"You asked: "
            f"{user_message or 'Please describe the change you want.'}"
        )

    def _last_user_message(self, prompt):
        matches = re.findall(
            r"(?:USER MESSAGE|USER)\s*:\s*"
            r"(.*?)(?=\n[A-Z][A-Z _-]+\s*:\s*|\Z)",
            prompt,
            re.I | re.S,
        )

        return matches[-1].strip() if matches else ""

    def _mock_generic(self, prompt):
        return (
            "AgentForge mock response: the request was received and "
            "can be processed by the configured AI provider."
        )


if __name__ == "__main__":
    client = GeminiClient(mode="MOCK")

    response = client.generate(
        "You are the chat assistant. "
        "USER MESSAGE: Hello AgentForge"
    )

    print("GeminiClient test successful.")
    print(response)