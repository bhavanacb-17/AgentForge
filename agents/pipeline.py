from pathlib import Path
import py_compile
import shutil
import re

from core.gemini_client import GeminiClient
from projects.project_storage import ProjectStorage


class AgentPipeline:

    def __init__(self, project):
        self.project = project

        self.project_id = project.get("id")

        if not self.project_id:
            raise ValueError("Project ID is required.")

        self.storage = ProjectStorage()

        self.project_folder = Path(
            self.storage.get_project_folder(
                self.project_id
            )
        )

        self.project_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        self.ai = GeminiClient()

    # ================================================================
    # MAIN PIPELINE
    # ================================================================

    def run(self):

        self._clean_workspace()

        result = {}

        # ============================================================
        # AGENT 1 - REQUIREMENTS ANALYSIS
        # ============================================================

        requirements_prompt = f"""
You are the Requirements Analysis Agent
in an autonomous software engineering platform.

Analyze this project:

{self._project_context()}

Create a professional requirements document containing:

1. Project Overview
2. Functional Requirements
3. Non-Functional Requirements
4. User Roles
5. Main Features
6. Technical Constraints
7. Assumptions
8. Recommended Implementation Scope

MANDATORY TECHNOLOGY CONTRACT:

Programming Language:
{self.project.get("programming_language", "Python")}

Framework:
{self.project.get("framework", "Django")}

Database:
{self.project.get("database", "MySQL")}

The selected technology stack MUST NOT be replaced.
"""

        result["requirements_analysis"] = self._run_agent(
            "Requirements Analysis",
            requirements_prompt
        )

        # ============================================================
        # AGENT 2 - ARCHITECT
        # ============================================================

        architecture_prompt = f"""
You are the Architect Agent.

Design the architecture for this project.

PROJECT:

{self._project_context()}

REQUIREMENTS:

{result["requirements_analysis"]}

MANDATORY STACK:

Python
Django
MySQL

IMPORTANT:

This is a Django + MySQL application.

Do NOT recommend:

- Streamlit
- SQLite
- Flask
- FastAPI
- local database files

MySQL is a database SERVER.
Do not describe MySQL as a database file.

Describe:

1. Architecture
2. Components
3. Database layer
4. Request flow
5. Application structure
6. Security considerations
7. Testing strategy

Return a professional architecture document.
"""

        result["architect"] = self._run_agent(
            "Architect",
            architecture_prompt
        )

        # ============================================================
        # AGENT 3 - DEVELOPER
        # ============================================================

        developer_prompt = f"""
You are the Developer Agent.

Generate a REAL Django + MySQL project.

PROJECT:

{self._project_context()}

REQUIREMENTS:

{result["requirements_analysis"]}

ARCHITECTURE:

{result["architect"]}

============================================================
MANDATORY TECHNOLOGY CONTRACT
============================================================

Programming Language: Python

Framework: Django

Database: MySQL

============================================================
FORBIDDEN
============================================================

NEVER generate:

Streamlit
SQLite
sqlite3
students.db
Flask
FastAPI
*.db database files

============================================================
REQUIRED
============================================================

The generated project MUST contain:

manage.py

config/
    __init__.py
    settings.py
    urls.py
    asgi.py
    wsgi.py

students/
    __init__.py
    apps.py
    models.py
    views.py
    forms.py
    urls.py
    admin.py
    migrations/
        __init__.py

students/templates/students/

tests/

requirements.txt

README.md

============================================================
DATABASE
============================================================

settings.py MUST contain:

DATABASES = {{
    "default": {{
        "ENGINE": "django.db.backends.mysql",
        ...
    }}
}}

Use Django ORM.

Do not use sqlite3.

============================================================
APPLICATION
============================================================

Implement:

- Add Student
- View Students
- Update Student
- Delete Student
- Search Students
- Django Model
- Django Forms
- Django Admin
- HTML Templates
- Tests

============================================================
OUTPUT FORMAT
============================================================

Return files exactly like this:

FILE: manage.py
CONTENT:
complete file content

FILE: config/settings.py
CONTENT:
complete file content

FILE: config/urls.py
CONTENT:
complete file content

Continue for every required file.

Do not provide explanations between files.
"""

        result["developer"] = self._run_agent(
            "Developer",
            developer_prompt
        )

        self._save_generated_files(
            result["developer"]
        )

        # ============================================================
        # INITIAL VALIDATION
        # ============================================================

        result["python_validation"] = (
            self._validate_python()
        )

        result["technology_validation"] = (
            self._validate_technology()
        )

        # ============================================================
        # AGENT 4 - TESTER
        # ============================================================

        tester_prompt = f"""
You are the Tester Agent.

Project:

{self._project_context()}

Developer output:

{result["developer"]}

Python validation:

{result["python_validation"]}

Technology validation:

{result["technology_validation"]}

The required stack is:

Python + Django + MySQL

If technology validation is FAILED,
you MUST report:

STATUS: TECHNOLOGY MISMATCH

Do not report PASS when the technology
contract is violated.

Check:

- Project structure
- Django configuration
- MySQL configuration
- CRUD functionality
- Forms
- Tests
- Security
- Potential runtime issues

Return a professional test report.
"""

        result["tester"] = self._run_agent(
            "Tester",
            tester_prompt
        )

        # ============================================================
        # AGENT 5 - DEBUGGER
        # ============================================================

        result["debugger"] = self._run_debugger(
            result
        )

        # ============================================================
        # VALIDATE AFTER DEBUGGER
        # ============================================================

        result["technology_validation_after_debugger"] = (
            self._validate_technology()
        )

        result["python_validation_after_debugger"] = (
            self._validate_python()
        )

        # ============================================================
        # DETERMINISTIC REPAIR
        # ============================================================

        if (
            self._failed(
                result["technology_validation_after_debugger"]
            )
            or
            self._failed(
                result["python_validation_after_debugger"]
            )
        ):

            result["deterministic_repair"] = (
                self._repair_django_mysql()
            )

        else:

            result["deterministic_repair"] = (
                "STATUS: NOT_REQUIRED\n\n"
                "The generated project already satisfies "
                "the technology contract."
            )

        # ============================================================
        # VALIDATE AFTER DETERMINISTIC REPAIR
        # ============================================================

        result["technology_validation_after_repair"] = (
            self._validate_technology()
        )

        result["python_validation_after_repair"] = (
            self._validate_python()
        )

        # ============================================================
        # AGENT 6 - CODE REVIEWER
        # ============================================================

        reviewer_prompt = f"""
You are the Code Reviewer Agent.

Project:

{self._project_context()}

Required technology:

Python + Django + MySQL

Technology validation:

{result["technology_validation_after_repair"]}

Python validation:

{result["python_validation_after_repair"]}

Review the generated project.

Check:

- Django architecture
- MySQL configuration
- Django ORM
- CRUD implementation
- Security
- Maintainability
- Testing
- Project structure

If technology validation is FAILED,
return:

STATUS: REVIEW FAILED

Otherwise provide a professional review.
"""

        result["code_reviewer"] = self._run_agent(
            "Code Reviewer",
            reviewer_prompt
        )

        # ============================================================
        # AGENT 7 - DOCUMENTATION
        # ============================================================

        documentation_prompt = f"""
You are the Documentation Agent.

Create professional documentation for:

{self.project.get("name")}

Description:

{self.project.get("description")}

Required stack:

Python
Django
MySQL

Final technology validation:

{result["technology_validation_after_repair"]}

Final Python validation:

{result["python_validation_after_repair"]}

Include:

1. Overview
2. Objectives
3. Features
4. Requirements
5. Architecture
6. Technology Stack
7. Database
8. Installation
9. Usage
10. Testing
11. Future Enhancements

IMPORTANT:

Document the actual implementation.

Do NOT claim Streamlit.

Do NOT claim SQLite.

Return Markdown documentation.
"""

        result["documentation"] = self._run_agent(
            "Documentation",
            documentation_prompt
        )

        self._save_documentation(
            result["documentation"]
        )

        # ============================================================
        # FINAL VALIDATION
        # ============================================================

        result["final_python_validation"] = (
            self._validate_python()
        )

        result["final_technology_validation"] = (
            self._validate_technology()
        )

        python_ok = not self._failed(
            result["final_python_validation"]
        )

        technology_ok = not self._failed(
            result["final_technology_validation"]
        )

        if python_ok and technology_ok:
            result["pipeline_status"] = "SUCCESS"
        else:
            result["pipeline_status"] = "FAILED"

        return result

    # ================================================================
    # AI AGENT EXECUTION
    # ================================================================

    def _run_agent(
        self,
        agent_name,
        prompt
    ):

        try:

            response = self.ai.generate(
                prompt
            )

            if response is None:
                return (
                    f"Agent: {agent_name}\n"
                    "STATUS: ERROR\n"
                    "AI returned an empty response."
                )

            return str(response)

        except Exception as exc:

            return (
                f"Agent: {agent_name}\n"
                "STATUS: ERROR\n"
                f"Error: {exc}"
            )

    # ================================================================
    # DEBUGGER
    # ================================================================

    def _run_debugger(
        self,
        result
    ):

        technology_failed = self._failed(
            result["technology_validation"]
        )

        python_failed = self._failed(
            result["python_validation"]
        )

        if not technology_failed and not python_failed:

            return (
                "## Debugger Repair Status\n\n"
                "No repair was required.\n\n"
                "STATUS: NO_REPAIR_REQUIRED"
            )

        workspace = self._read_workspace()

        debugger_prompt = f"""
You are the Debugger Agent.

The generated project has validation failures.

PROJECT:

{self._project_context()}

TECHNOLOGY VALIDATION:

{result["technology_validation"]}

PYTHON VALIDATION:

{result["python_validation"]}

CURRENT FILES:

{workspace}

============================================================
MANDATORY
============================================================

The project MUST use:

Python
Django
MySQL

Repair the project.

DO NOT say:

"No repair was required."

DO NOT only explain the problem.

Return corrected files.

The project must contain:

manage.py
config/settings.py
config/urls.py
config/asgi.py
config/wsgi.py
students/models.py
students/views.py
students/forms.py
students/urls.py
students/admin.py
requirements.txt
tests

Django settings MUST use:

django.db.backends.mysql

DO NOT use:

sqlite3
SQLite
Streamlit
students.db
Flask
FastAPI

Output:

FILE: path
CONTENT:
complete corrected file
"""

        response = self._run_agent(
            "Debugger",
            debugger_prompt
        )

        saved = self._save_generated_files(
            response
        )

        if saved > 0:

            return (
                response
                + "\n\n"
                + "Debugger files applied: "
                + str(saved)
            )

        return (
            response
            + "\n\n"
            + "No debugger files were returned. "
            + "Deterministic repair will be attempted."
        )

    # ================================================================
    # DETERMINISTIC DJANGO + MYSQL REPAIR
    # ================================================================

    def _repair_django_mysql(self):

        self.project_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        # Remove invalid generated application.
        for name in [
            "app.py",
            "students.db",
            "app.db"
        ]:

            target = (
                self.project_folder
                / name
            )

            if target.exists():

                try:
                    target.unlink()
                except OSError:
                    pass

        # Remove cache folders.
        for cache in self.project_folder.rglob(
            "__pycache__"
        ):

            try:
                shutil.rmtree(cache)
            except OSError:
                pass

        # Required directories.
        directories = [
            "config",
            "students",
            "students/migrations",
            "students/templates/students",
            "tests"
        ]

        for directory in directories:

            (
                self.project_folder
                / directory
            ).mkdir(
                parents=True,
                exist_ok=True
            )

        # ============================================================
        # WRITE DJANGO PROJECT
        # ============================================================

        files = {

            "manage.py":
                self._manage_py(),

            "config/__init__.py":
                "",

            "config/settings.py":
                self._settings_py(),

            "config/urls.py":
                self._urls_py(),

            "config/asgi.py":
                self._asgi_py(),

            "config/wsgi.py":
                self._wsgi_py(),

            "students/__init__.py":
                "",

            "students/apps.py":
                self._apps_py(),

            "students/models.py":
                self._models_py(),

            "students/forms.py":
                self._forms_py(),

            "students/views.py":
                self._views_py(),

            "students/urls.py":
                self._student_urls_py(),

            "students/admin.py":
                self._admin_py(),

            "students/migrations/__init__.py":
                "",

            "students/templates/students/base.html":
                self._base_html(),

            "students/templates/students/student_list.html":
                self._student_list_html(),

            "students/templates/students/student_form.html":
                self._student_form_html(),

            "students/templates/students/student_confirm_delete.html":
                self._student_delete_html(),

            "tests/__init__.py":
                "",

            "tests/test_students.py":
                self._tests_py(),

            "requirements.txt":
                self._requirements(),

            "README.md":
                self._readme(),

        }

        for relative_path, content in files.items():

            self._write_file(
                relative_path,
                content
            )

        return (
            "STATUS: REPAIRED\n\n"
            "Deterministic Django + MySQL repair completed.\n\n"
            "Created:\n"
            "- manage.py\n"
            "- Django settings\n"
            "- Django URLs\n"
            "- Student model\n"
            "- Student forms\n"
            "- CRUD views\n"
            "- Admin configuration\n"
            "- HTML templates\n"
            "- Tests\n"
            "- MySQL configuration\n"
            "- requirements.txt\n"
            "- README.md"
        )

    # ================================================================
    # DJANGO FILE GENERATORS
    # ================================================================

    def _manage_py(self):

        return '''import os
import sys


def main():
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "config.settings"
    )

    from django.core.management import (
        execute_from_command_line
    )

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
'''

    def _settings_py(self):

        return '''import os

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "agentforge-development-key"
)


DEBUG = True


ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "students",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "config.urls"


TEMPLATES = [
    {
        "BACKEND":
            "django.template.backends.django.DjangoTemplates",

        "DIRS": [],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "config.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE":
            "django.db.backends.mysql",

        "NAME":
            os.getenv(
                "MYSQL_DATABASE",
                "agentforge_db"
            ),

        "USER":
            os.getenv(
                "MYSQL_USER",
                "agentforge_user"
            ),

        "PASSWORD":
            os.getenv(
                "MYSQL_PASSWORD",
                "AgentForge@123"
            ),

        "HOST":
            os.getenv(
                "MYSQL_HOST",
                "127.0.0.1"
            ),

        "PORT":
            os.getenv(
                "MYSQL_PORT",
                "3307"
            ),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME":
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator",
    },
    {
        "NAME":
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator",
    },
]


LANGUAGE_CODE = "en-us"


TIME_ZONE = "Asia/Kolkata"


USE_I18N = True


USE_TZ = True


STATIC_URL = "static/"


DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)
'''

    def _urls_py(self):

        return '''from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path(
        "admin/",
        admin.site.urls
    ),

    path(
        "",
        include("students.urls")
    ),
]
'''

    def _asgi_py(self):

        return '''import os

from django.core.asgi import (
    get_asgi_application
)


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)


application = get_asgi_application()
'''

    def _wsgi_py(self):

        return '''import os

from django.core.wsgi import (
    get_wsgi_application
)


os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)


application = get_wsgi_application()
'''

    def _apps_py(self):

        return '''from django.apps import AppConfig


class StudentsConfig(AppConfig):

    default_auto_field = (
        "django.db.models.BigAutoField"
    )

    name = "students"
'''

    def _models_py(self):

        return '''from django.db import models


class Student(models.Model):

    student_id = models.CharField(
        max_length=50,
        unique=True
    )

    first_name = models.CharField(
        max_length=100
    )

    last_name = models.CharField(
        max_length=100
    )

    email = models.EmailField(
        unique=True
    )

    course = models.CharField(
        max_length=200
    )

    age = models.PositiveIntegerField()


    class Meta:

        ordering = [
            "first_name",
            "last_name"
        ]


    def __str__(self):

        return (
            f"{self.student_id} - "
            f"{self.first_name} "
            f"{self.last_name}"
        )
'''

    def _forms_py(self):

        return '''from django import forms

from .models import Student


class StudentForm(forms.ModelForm):

    class Meta:

        model = Student

        fields = [
            "student_id",
            "first_name",
            "last_name",
            "email",
            "course",
            "age",
        ]
'''

    def _views_py(self):

        return '''from django.db import models

from django.shortcuts import (
    get_object_or_404,
    redirect,
    render
)

from .forms import StudentForm

from .models import Student


def student_list(request):

    query = request.GET.get(
        "q",
        ""
    ).strip()

    students = Student.objects.all()

    if query:

        students = students.filter(
            models.Q(
                student_id__icontains=query
            )
            |
            models.Q(
                first_name__icontains=query
            )
            |
            models.Q(
                last_name__icontains=query
            )
            |
            models.Q(
                course__icontains=query
            )
        )

    return render(
        request,
        "students/student_list.html",
        {
            "students": students,
            "query": query
        }
    )


def student_create(request):

    if request.method == "POST":

        form = StudentForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            return redirect(
                "student-list"
            )

    else:

        form = StudentForm()

    return render(
        request,
        "students/student_form.html",
        {
            "form": form,
            "title": "Add Student"
        }
    )


def student_update(
    request,
    pk
):

    student = get_object_or_404(
        Student,
        pk=pk
    )

    if request.method == "POST":

        form = StudentForm(
            request.POST,
            instance=student
        )

        if form.is_valid():

            form.save()

            return redirect(
                "student-list"
            )

    else:

        form = StudentForm(
            instance=student
        )

    return render(
        request,
        "students/student_form.html",
        {
            "form": form,
            "title": "Update Student"
        }
    )


def student_delete(
    request,
    pk
):

    student = get_object_or_404(
        Student,
        pk=pk
    )

    if request.method == "POST":

        student.delete()

        return redirect(
            "student-list"
        )

    return render(
        request,
        "students/student_confirm_delete.html",
        {
            "student": student
        }
    )
'''

    def _student_urls_py(self):

        return '''from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.student_list,
        name="student-list"
    ),

    path(
        "students/add/",
        views.student_create,
        name="student-create"
    ),

    path(
        "students/<int:pk>/edit/",
        views.student_update,
        name="student-update"
    ),

    path(
        "students/<int:pk>/delete/",
        views.student_delete,
        name="student-delete"
    ),
]
'''

    def _admin_py(self):

        return '''from django.contrib import admin

from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):

    list_display = (
        "student_id",
        "first_name",
        "last_name",
        "email",
        "course",
        "age"
    )

    search_fields = (
        "student_id",
        "first_name",
        "last_name",
        "email",
        "course"
    )
'''

    # ================================================================
    # HTML
    # ================================================================

    def _base_html(self):

        return '''<!DOCTYPE html>

<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width,
        initial-scale=1.0"
    >

    <title>
        Student Management System
    </title>

    <style>

        body {
            font-family: Arial, sans-serif;
            margin: 0;
            background: #f4f7fb;
            color: #1f2937;
        }

        nav {
            background: #111827;
            padding: 20px 40px;
        }

        nav a {
            color: white;
            text-decoration: none;
            font-size: 20px;
            font-weight: bold;
        }

        main {
            max-width: 1100px;
            margin: 40px auto;
            padding: 0 20px;
        }

        .card {
            background: white;
            padding: 25px;
            border-radius: 14px;
            margin-bottom: 25px;
            box-shadow:
                0 5px 20px
                rgba(0, 0, 0, 0.06);
        }

        .button {
            display: inline-block;
            background: #2563eb;
            color: white;
            padding: 10px 16px;
            border-radius: 8px;
            border: none;
            text-decoration: none;
            cursor: pointer;
        }

        .danger {
            background: #dc2626;
        }

        input {
            width: 100%;
            box-sizing: border-box;
            padding: 12px;
            margin: 8px 0 15px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th,
        td {
            padding: 12px;
            border-bottom: 1px solid #ddd;
            text-align: left;
        }

    </style>

</head>

<body>

<nav>

    <a href="{% url 'student-list' %}">
        Student Management System
    </a>

</nav>

<main>

    {% block content %}
    {% endblock %}

</main>

</body>

</html>
'''

    def _student_list_html(self):

        return '''{% extends "students/base.html" %}


{% block content %}


<div class="card">

    <h1>
        Student Management System
    </h1>

    <p>
        Manage student records using Django and MySQL.
    </p>

    <form method="get">

        <input
            type="text"
            name="q"
            value="{{ query }}"
            placeholder="Search by name, ID or course"
        >

        <button
            class="button"
            type="submit"
        >
            Search
        </button>

        <a
            class="button"
            href="{% url 'student-create' %}"
        >
            Add Student
        </a>

    </form>

</div>


<div class="card">

    <table>

        <thead>

            <tr>

                <th>
                    Student ID
                </th>

                <th>
                    Name
                </th>

                <th>
                    Email
                </th>

                <th>
                    Course
                </th>

                <th>
                    Age
                </th>

                <th>
                    Actions
                </th>

            </tr>

        </thead>

        <tbody>

        {% for student in students %}

            <tr>

                <td>
                    {{ student.student_id }}
                </td>

                <td>
                    {{ student.first_name }}
                    {{ student.last_name }}
                </td>

                <td>
                    {{ student.email }}
                </td>

                <td>
                    {{ student.course }}
                </td>

                <td>
                    {{ student.age }}
                </td>

                <td>

                    <a
                        class="button"
                        href="{% url 'student-update' student.pk %}"
                    >
                        Edit
                    </a>

                    <a
                        class="button danger"
                        href="{% url 'student-delete' student.pk %}"
                    >
                        Delete
                    </a>

                </td>

            </tr>

        {% empty %}

            <tr>

                <td colspan="6">
                    No students found.
                </td>

            </tr>

        {% endfor %}

        </tbody>

    </table>

</div>


{% endblock %}
'''

    def _student_form_html(self):

        return '''{% extends "students/base.html" %}


{% block content %}


<div class="card">

    <h1>
        {{ title }}
    </h1>


    <form method="post">

        {% csrf_token %}

        {{ form.as_p }}

        <button
            class="button"
            type="submit"
        >
            Save Student
        </button>

        <a
            class="button"
            href="{% url 'student-list' %}"
        >
            Cancel
        </a>

    </form>

</div>


{% endblock %}
'''

    def _student_delete_html(self):

        return '''{% extends "students/base.html" %}


{% block content %}


<div class="card">

    <h1>
        Delete Student
    </h1>

    <p>
        Are you sure you want to delete
        <strong>
            {{ student.first_name }}
            {{ student.last_name }}
        </strong>?
    </p>


    <form method="post">

        {% csrf_token %}

        <button
            class="button danger"
            type="submit"
        >
            Confirm Delete
        </button>

        <a
            class="button"
            href="{% url 'student-list' %}"
        >
            Cancel
        </a>

    </form>

</div>


{% endblock %}
'''

    # ================================================================
    # TESTS
    # ================================================================

    def _tests_py(self):

        return '''from django.test import TestCase

from django.urls import reverse

from students.models import Student


class StudentModelTest(TestCase):

    def setUp(self):

        self.student = Student.objects.create(

            student_id="STU001",

            first_name="Test",

            last_name="Student",

            email="test@example.com",

            course="Computer Science",

            age=21
        )


    def test_student_string(self):

        self.assertEqual(

            str(self.student),

            "STU001 - Test Student"
        )


    def test_student_list(self):

        response = self.client.get(

            reverse(
                "student-list"
            )
        )

        self.assertEqual(

            response.status_code,

            200
        )


    def test_student_is_displayed(self):

        response = self.client.get(

            reverse(
                "student-list"
            )
        )

        self.assertContains(

            response,

            "Test Student"
        )
'''

    # ================================================================
    # REQUIREMENTS
    # ================================================================

    def _requirements(self):

        return '''Django>=5.1,<6.0
mysqlclient>=2.2
'''

    # ================================================================
    # README
    # ================================================================

    def _readme(self):

        name = self.project.get(
            "name",
            "Student Management System"
        )

        description = self.project.get(
            "description",
            "A system for managing student records."
        )

        return f'''# {name}


## Description

{description}


## Technology Stack

- Python
- Django
- MySQL
- Django ORM


## Features

- Add students
- View students
- Search students
- Update students
- Delete students
- Django administration
- Form validation
- Automated tests


## Database

This application uses MySQL through the Django MySQL database backend.

Database engine:

django.db.backends.mysql


## Installation

Create a virtual environment:

python -m venv venv


Install dependencies:

pip install -r requirements.txt


Configure MySQL connection using:

MYSQL_DATABASE
MYSQL_USER
MYSQL_PASSWORD
MYSQL_HOST
MYSQL_PORT


## Database Setup

Run:

python manage.py makemigrations

python manage.py migrate


## Create Administrator

Run:

python manage.py createsuperuser


## Start Application

Run:

python manage.py runserver


## Run Tests

Run:

python manage.py test


## Generated By

AgentForge autonomous multi-agent software engineering platform.
'''

    # ================================================================
    # FILE PARSER
    # ================================================================

    def _save_generated_files(
        self,
        response
    ):

        if not response:
            return 0

        pattern = re.compile(
            r"FILE:\s*(.+?)\s*\n"
            r"CONTENT:\s*\n"
            r"(.*?)(?=\nFILE:\s*|\Z)",
            re.DOTALL
        )

        matches = pattern.findall(
            response
        )

        count = 0

        for relative_path, content in matches:

            relative_path = (
                relative_path.strip()
            )

            if not relative_path:
                continue

            content = content.strip()

            # Remove markdown fences if AI added them.
            if content.startswith("```"):

                lines = content.splitlines()

                if lines:
                    lines = lines[1:]

                if (
                    lines
                    and
                    lines[-1].strip() == "```"
                ):
                    lines = lines[:-1]

                content = "\n".join(lines)

            try:

                self._write_file(
                    relative_path,
                    content
                )

                count += 1

            except Exception:

                continue

        return count

    # ================================================================
    # SAFE FILE WRITER
    # ================================================================

    def _write_file(
        self,
        relative_path,
        content
    ):

        relative_path = (
            relative_path
            .replace("\\", "/")
        )

        relative = Path(
            relative_path
        )

        if relative.is_absolute():

            raise ValueError(
                "Absolute paths are not allowed."
            )

        if ".." in relative.parts:

            raise ValueError(
                "Path traversal is not allowed."
            )

        target = (
            self.project_folder
            / relative
        ).resolve()

        root = (
            self.project_folder
            .resolve()
        )

        if (
            target != root
            and root not in target.parents
        ):

            raise ValueError(
                "Generated file escaped project folder."
            )

        target.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        target.write_text(
            content,
            encoding="utf-8"
        )

        return target

    # ================================================================
    # PYTHON VALIDATION
    # ================================================================

    def _validate_python(self):

        python_files = list(
            self.project_folder.rglob(
                "*.py"
            )
        )

        if not python_files:

            return (
                "STATUS: FAILED\n\n"
                "No Python files were generated."
            )

        errors = []

        for file_path in python_files:

            if "__pycache__" in file_path.parts:
                continue

            try:

                py_compile.compile(
                    str(file_path),
                    doraise=True
                )

            except Exception as exc:

                errors.append(
                    f"{file_path.relative_to(self.project_folder)}: "
                    f"{exc}"
                )

        if errors:

            return (
                "STATUS: FAILED\n\n"
                "Python validation errors:\n\n"
                +
                "\n".join(
                    "- " + error
                    for error in errors
                )
            )

        return (
            "STATUS: PASS\n\n"
            f"Validated {len(python_files)} Python file(s).\n\n"
            "All generated Python files passed "
            "py_compile."
        )

    # ================================================================
    # TECHNOLOGY VALIDATION
    # ================================================================

    def _validate_technology(self):

        problems = []

        framework = str(
            self.project.get(
                "framework",
                "Django"
            )
        ).lower()

        database = str(
            self.project.get(
                "database",
                "MySQL"
            )
        ).lower()

        language = str(
            self.project.get(
                "programming_language",
                "Python"
            )
        ).lower()

        source = ""

        for file_path in self.project_folder.rglob("*"):

            if not file_path.is_file():
                continue

            if "__pycache__" in file_path.parts:
                continue

            if file_path.suffix.lower() not in [
                ".py",
                ".txt",
                ".json",
                ".yaml",
                ".yml",
                ".ini",
                ".cfg",
                ".toml"
            ]:
                continue

            try:

                source += (
                    "\n"
                    +
                    file_path.read_text(
                        encoding="utf-8",
                        errors="ignore"
                    ).lower()
                )

            except OSError:
                continue

        # ------------------------------------------------------------
        # DJANGO
        # ------------------------------------------------------------

        if framework == "django":

            if "streamlit" in source:

                problems.append(
                    "Streamlit code detected although "
                    "Django is selected."
                )

            if "flask" in source:

                problems.append(
                    "Flask code detected although "
                    "Django is selected."
                )

            if not (
                self.project_folder
                / "manage.py"
            ).exists():

                problems.append(
                    "manage.py was not generated "
                    "for the Django project."
                )

            if not list(
                self.project_folder.rglob(
                    "settings.py"
                )
            ):

                problems.append(
                    "Django settings.py was not generated."
                )

            django_indicators = [
                "django.db",
                "django.urls",
                "django.shortcuts",
                "django.contrib"
            ]

            if not any(
                item in source
                for item in django_indicators
            ):

                problems.append(
                    "Django framework indicators "
                    "were not found."
                )

        # ------------------------------------------------------------
        # MYSQL
        # ------------------------------------------------------------

        if database == "mysql":

            forbidden = [
                "import sqlite3",
                "from sqlite3",
                "sqlite3.connect",
                "sqlite://",
                "students.db",
                "sqlite",
                "streamlit"
            ]

            for item in forbidden:

                if item in source:

                    problems.append(
                        f"Incompatible database "
                        f"technology detected "
                        f"('{item}') although "
                        f"MySQL is selected."
                    )

            if (
                "django.db.backends.mysql"
                not in source
            ):

                problems.append(
                    "Django MySQL database backend "
                    "was not detected."
                )

        # ------------------------------------------------------------
        # RESULT
        # ------------------------------------------------------------

        if problems:

            unique = []

            for problem in problems:

                if problem not in unique:

                    unique.append(problem)

            return (
                "STATUS: FAILED\n\n"
                "Technology consistency problems "
                "were detected:\n\n"
                +
                "\n".join(
                    "- " + problem
                    for problem in unique
                )
            )

        return (
            "STATUS: PASS\n\n"
            "Technology contract validated successfully.\n\n"
            f"Language: {language}\n"
            f"Framework: {framework}\n"
            f"Database: {database}"
        )

    # ================================================================
    # VALIDATION STATUS
    # ================================================================

    def _failed(
        self,
        validation
    ):

        return str(
            validation or ""
        ).strip().upper().startswith(
            "STATUS: FAILED"
        )

    # ================================================================
    # WORKSPACE CLEANUP
    # ================================================================

    def _clean_workspace(self):

        self.project_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        for item in list(
            self.project_folder.iterdir()
        ):

            try:

                if item.is_dir():

                    shutil.rmtree(
                        item
                    )

                else:

                    item.unlink()

            except OSError:

                pass

    # ================================================================
    # READ WORKSPACE
    # ================================================================

    def _read_workspace(self):

        output = []

        for file_path in sorted(
            self.project_folder.rglob("*")
        ):

            if not file_path.is_file():
                continue

            if "__pycache__" in file_path.parts:
                continue

            try:

                relative = (
                    file_path.relative_to(
                        self.project_folder
                    )
                )

                content = (
                    file_path.read_text(
                        encoding="utf-8",
                        errors="ignore"
                    )
                )

                output.append(
                    f"\n--- FILE: {relative} ---\n"
                    f"{content[:10000]}"
                )

            except OSError:

                pass

        return "\n".join(output)

    # ================================================================
    # DOCUMENTATION
    # ================================================================

    def _save_documentation(
        self,
        documentation
    ):

        if not documentation:
            return

        try:

            self._write_file(
                "DOCUMENTATION.md",
                documentation
            )

        except Exception:

            pass

    # ================================================================
    # PROJECT CONTEXT
    # ================================================================

    def _project_context(self):

        return f"""
Project ID:
{self.project.get("id")}

Project Name:
{self.project.get("name")}

Description:
{self.project.get("description")}

Requirements:
{self.project.get("requirements")}

Category:
{self.project.get("category")}

Programming Language:
{self.project.get("programming_language")}

Framework:
{self.project.get("framework")}

Database:
{self.project.get("database")}

Additional Instructions:
{self.project.get("additional_instructions")}
"""