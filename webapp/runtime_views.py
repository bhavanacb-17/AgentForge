from pathlib import Path
import os
import socket
import subprocess
import sys
import time

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render

from agentforge_core.models import Project
from projects.project_storage import ProjectStorage


# ============================================================
# CONFIGURATION
# ============================================================

BASE_RUNTIME_PORT = 8000


# ============================================================
# PROJECT FOLDER
# ============================================================

def _get_project_folder(project):
    """
    Return the generated project directory.
    """

    storage = ProjectStorage()

    return Path(
        storage.get_project_folder(project.id)
    ).resolve()


# ============================================================
# SAFE FILE ACCESS
# ============================================================

def _safe_project_file(
    project_folder,
    relative_path,
):
    """
    Safely resolve a generated project file.

    Prevents paths such as:
        ../../some_file
    """

    if not relative_path:
        raise Http404(
            "File path was not provided."
        )

    project_folder = project_folder.resolve()

    candidate = (
        project_folder / relative_path
    ).resolve()

    try:
        candidate.relative_to(
            project_folder
        )

    except ValueError:
        raise Http404(
            "Invalid file path."
        )

    if not candidate.exists():
        raise Http404(
            "Generated file does not exist."
        )

    if not candidate.is_file():
        raise Http404(
            "The requested path is not a file."
        )

    return candidate


# ============================================================
# PORT
# ============================================================

def _runtime_port(project):
    """
    Give every generated project its own port.

    Project 1 -> 8001
    Project 2 -> 8002
    Project 5 -> 8005
    """

    return BASE_RUNTIME_PORT + int(
        project.id
    )


def _is_port_open(
    host,
    port,
):
    """
    Check whether a TCP port is already in use.
    """

    with socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM,
    ) as sock:

        sock.settimeout(0.25)

        try:
            return (
                sock.connect_ex(
                    (host, port)
                ) == 0
            )

        except OSError:
            return False


# ============================================================
# RUNTIME LOG
# ============================================================

def _runtime_log_path(project):
    """
    Runtime logs are stored outside the
    generated project.
    """

    root = (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )

    logs_folder = root / "logs"

    logs_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    return (
        logs_folder
        / f"runtime_project_{project.id}.log"
    )


# ============================================================
# DJANGO ENVIRONMENT
# ============================================================

def _django_environment(
    project_folder,
    package_name,
):
    """
    Build the environment used by the generated
    Django application.

    IMPORTANT:
    AgentForge itself may have an inherited
    DJANGO_SETTINGS_MODULE such as:

        backend.settings

    That value must NEVER leak into the generated
    project.

    The generated project gets:

        DJANGO_SETTINGS_MODULE=config.settings

    or whatever package was detected.
    """

    environment = os.environ.copy()

    # --------------------------------------------------------
    # FORCE generated Django settings module
    # --------------------------------------------------------

    environment[
        "DJANGO_SETTINGS_MODULE"
    ] = (
        f"{package_name}.settings"
    )

    # --------------------------------------------------------
    # Make generated project importable
    # --------------------------------------------------------

    project_path = str(
        project_folder.resolve()
    )

    current_pythonpath = (
        environment.get(
            "PYTHONPATH",
            "",
        )
    )

    if current_pythonpath:

        environment["PYTHONPATH"] = (
            project_path
            + os.pathsep
            + current_pythonpath
        )

    else:

        environment["PYTHONPATH"] = (
            project_path
        )

    return environment


# ============================================================
# MANAGEMENT COMMAND
# ============================================================

def _run_management_command(
    project_folder,
    package_name,
    command,
    log_file,
):
    """
    Run:

        python manage.py <command>

    inside the generated project.

    The generated project's Django settings
    are explicitly supplied through the environment.
    """

    command_text = " ".join(
        [
            "python",
            "manage.py",
            *command,
        ]
    )

    log_file.write(
        "\n"
        + "-" * 70
        + "\n"
    )

    log_file.write(
        f"COMMAND: {command_text}\n"
    )

    log_file.write(
        f"DJANGO_SETTINGS_MODULE: "
        f"{package_name}.settings\n"
    )

    log_file.write(
        f"PROJECT DIRECTORY: "
        f"{project_folder}\n"
    )

    log_file.write(
        "-" * 70
        + "\n"
    )

    log_file.flush()

    environment = _django_environment(
        project_folder,
        package_name,
    )

    try:

        process = subprocess.run(
            [
                sys.executable,
                "manage.py",
                *command,
            ],
            cwd=str(project_folder),
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    except Exception as exc:

        output = str(exc)

        log_file.write(
            output
        )

        log_file.write("\n")

        log_file.flush()

        return {
            "success": False,
            "returncode": -1,
            "output": output,
        }

    output = (
        process.stdout
        or ""
    )

    log_file.write(
        output
    )

    log_file.write("\n")

    log_file.flush()

    return {
        "success": (
            process.returncode == 0
        ),
        "returncode": process.returncode,
        "output": output,
    }


# ============================================================
# DETECT DJANGO PACKAGE
# ============================================================

def _detect_django_package(
    project_folder,
):
    """
    Detect the generated Django package.

    Example:

        project_5/
            manage.py
            config/
                settings.py
                urls.py
                asgi.py
                wsgi.py

    Returns:

        config
    """

    if not project_folder.exists():
        return None

    candidates = []

    try:

        children = list(
            project_folder.iterdir()
        )

    except OSError:

        return None

    for item in children:

        if not item.is_dir():
            continue

        if item.name.startswith("."):
            continue

        if item.name in {
            "__pycache__",
            "venv",
            ".venv",
        }:
            continue

        settings_file = (
            item / "settings.py"
        )

        if settings_file.exists():

            candidates.append(
                item.name
            )

    # AgentForge-generated projects
    # conventionally use config/.
    if "config" in candidates:
        return "config"

    if candidates:
        return candidates[0]

    return None


# ============================================================
# REPAIR DJANGO MODULE REFERENCES
# ============================================================

def _repair_django_module_references(
    project_folder,
    package_name,
    log_file,
):
    """
    Repair stale references such as:

        backend.settings
        backend.urls
        backend.wsgi
        backend.asgi

    when the actual Django package is:

        config
    """

    replacements = []

    try:

        python_files = list(
            project_folder.rglob(
                "*.py"
            )
        )

    except OSError as exc:

        log_file.write(
            "\nUnable to scan Python files: "
            f"{exc}\n"
        )

        log_file.flush()

        return replacements

    for file_path in python_files:

        if "__pycache__" in file_path.parts:
            continue

        try:

            content = file_path.read_text(
                encoding="utf-8",
                errors="replace",
            )

        except Exception:

            continue

        original = content

        # ----------------------------------------------------
        # Django settings
        # ----------------------------------------------------

        content = content.replace(
            "backend.settings",
            f"{package_name}.settings",
        )

        # ----------------------------------------------------
        # Django URLs
        # ----------------------------------------------------

        content = content.replace(
            "backend.urls",
            f"{package_name}.urls",
        )

        # ----------------------------------------------------
        # WSGI
        # ----------------------------------------------------

        content = content.replace(
            "backend.wsgi",
            f"{package_name}.wsgi",
        )

        # ----------------------------------------------------
        # ASGI
        # ----------------------------------------------------

        content = content.replace(
            "backend.asgi",
            f"{package_name}.asgi",
        )

        if content == original:
            continue

        try:

            file_path.write_text(
                content,
                encoding="utf-8",
            )

            replacements.append(
                str(
                    file_path.relative_to(
                        project_folder
                    )
                )
            )

        except Exception as exc:

            log_file.write(
                "\nUnable to repair "
                f"{file_path}: {exc}\n"
            )

    log_file.write(
        "\n"
        "DJANGO MODULE REFERENCE REPAIR\n"
    )

    log_file.write(
        f"Detected package: {package_name}\n"
    )

    if replacements:

        log_file.write(
            "Repaired files:\n"
        )

        for item in replacements:

            log_file.write(
                f"  - {item}\n"
            )

    else:

        log_file.write(
            "No stale backend references found.\n"
        )

    log_file.flush()

    return replacements


# ============================================================
# PREPARE DJANGO APPLICATION
# ============================================================

def _prepare_django_project(
    project,
    project_folder,
    package_name,
    log_file,
):
    """
    Prepare the generated Django project.

    AgentForge automatically performs:

        1. Detect Django package
        2. Repair stale module references
        3. Django system check
        4. Create migrations
        5. Apply migrations
    """

    log_file.write(
        "\n"
        + "=" * 70
        + "\n"
    )

    log_file.write(
        "AGENTFORGE APPLICATION PREPARATION\n"
    )

    log_file.write(
        f"Project: {project.name}\n"
    )

    log_file.write(
        f"Project ID: {project.id}\n"
    )

    log_file.write(
        f"Django package: {package_name}\n"
    )

    log_file.write(
        f"Django settings: "
        f"{package_name}.settings\n"
    )

    log_file.write(
        "=" * 70
        + "\n"
    )

    log_file.flush()

    # ========================================================
    # REPAIR MODULE REFERENCES
    # ========================================================

    _repair_django_module_references(
        project_folder,
        package_name,
        log_file,
    )

    # ========================================================
    # DJANGO SYSTEM CHECK
    # ========================================================

    check_result = (
        _run_management_command(
            project_folder,
            package_name,
            ["check"],
            log_file,
        )
    )

    if not check_result["success"]:

        return {
            "success": False,
            "stage": "Django system check",
            "message": (
                "Django system check failed.\n\n"
                + check_result["output"]
            ),
        }

    # ========================================================
    # CREATE MIGRATIONS
    # ========================================================

    migrations_result = (
        _run_management_command(
            project_folder,
            package_name,
            [
                "makemigrations",
                "--noinput",
            ],
            log_file,
        )
    )

    if not migrations_result["success"]:

        return {
            "success": False,
            "stage": "Create migrations",
            "message": (
                "Django could not create "
                "migrations.\n\n"
                + migrations_result["output"]
            ),
        }

    # ========================================================
    # APPLY MIGRATIONS
    # ========================================================

    migrate_result = (
        _run_management_command(
            project_folder,
            package_name,
            [
                "migrate",
                "--noinput",
            ],
            log_file,
        )
    )

    if not migrate_result["success"]:

        return {
            "success": False,
            "stage": "Apply migrations",
            "message": (
                "Django could not apply "
                "database migrations.\n\n"
                + migrate_result["output"]
            ),
        }

    # ========================================================
    # SUCCESS
    # ========================================================

    log_file.write(
        "\n"
        + "=" * 70
        + "\n"
    )

    log_file.write(
        "APPLICATION PREPARATION COMPLETED\n"
    )

    log_file.write(
        f"Django package: "
        f"{package_name}\n"
    )

    log_file.write(
        f"Django settings: "
        f"{package_name}.settings\n"
    )

    log_file.write(
        "Django check: PASS\n"
    )

    log_file.write(
        "Migrations: APPLIED\n"
    )

    log_file.write(
        "=" * 70
        + "\n"
    )

    log_file.flush()

    return {
        "success": True,
        "stage": "Completed",
        "message": (
            "Django checks passed. "
            "Generated-project references "
            "were repaired and MySQL migrations "
            "were applied successfully."
        ),
    }


# ============================================================
# START GENERATED DJANGO APPLICATION
# ============================================================

def _start_django_project(
    project,
):
    """
    Start the generated Django application.
    """

    project_folder = (
        _get_project_folder(project)
    )

    manage_py = (
        project_folder / "manage.py"
    )

    # --------------------------------------------------------
    # PROJECT FOLDER
    # --------------------------------------------------------

    if not project_folder.exists():

        return {
            "success": False,
            "url": "",
            "port": None,
            "message": (
                "The generated project folder "
                "does not exist."
            ),
            "log_path": None,
        }

    # --------------------------------------------------------
    # MANAGE.PY
    # --------------------------------------------------------

    if not manage_py.exists():

        return {
            "success": False,
            "url": "",
            "port": None,
            "message": (
                "manage.py was not found.\n\n"
                "The generated project is not "
                "a Django application."
            ),
            "log_path": None,
        }

    # --------------------------------------------------------
    # DETECT DJANGO PACKAGE BEFORE ANY COMMAND
    # --------------------------------------------------------

    package_name = _detect_django_package(
        project_folder
    )

    if not package_name:

        return {
            "success": False,
            "url": "",
            "port": None,
            "message": (
                "AgentForge could not detect "
                "the Django settings package.\n\n"
                "No settings.py file was found."
            ),
            "log_path": None,
        }

    host = "127.0.0.1"

    port = _runtime_port(
        project
    )

    application_url = (
        f"http://{host}:{port}/"
    )

    log_path = (
        _runtime_log_path(project)
    )

    # --------------------------------------------------------
    # ALREADY RUNNING
    # --------------------------------------------------------

    if _is_port_open(
        host,
        port,
    ):

        return {
            "success": True,
            "url": application_url,
            "port": port,
            "message": (
                "The generated application "
                "is already running."
            ),
            "log_path": log_path,
        }

    # --------------------------------------------------------
    # OPEN LOG
    # --------------------------------------------------------

    try:

        log_file = open(
            log_path,
            "a",
            encoding="utf-8",
        )

    except Exception as exc:

        return {
            "success": False,
            "url": "",
            "port": port,
            "message": (
                "Unable to create the "
                "runtime log.\n\n"
                + str(exc)
            ),
            "log_path": None,
        }

    try:

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        log_file.write(
            "\n\n"
            + "#" * 70
            + "\n"
        )

        log_file.write(
            "AGENTFORGE GENERATED APPLICATION\n"
        )

        log_file.write(
            f"Project: {project.name}\n"
        )

        log_file.write(
            f"Project ID: {project.id}\n"
        )

        log_file.write(
            f"Django package: {package_name}\n"
        )

        log_file.write(
            f"Django settings: "
            f"{package_name}.settings\n"
        )

        log_file.write(
            f"URL: {application_url}\n"
        )

        log_file.write(
            "#" * 70
            + "\n"
        )

        log_file.flush()

        # ----------------------------------------------------
        # PREPARE APPLICATION
        # ----------------------------------------------------

        preparation = (
            _prepare_django_project(
                project,
                project_folder,
                package_name,
                log_file,
            )
        )

        if not preparation["success"]:

            log_file.close()

            return {
                "success": False,
                "url": "",
                "port": port,
                "message": (
                    f"{preparation['stage']} failed.\n\n"
                    + preparation["message"]
                ),
                "log_path": log_path,
            }

        # ----------------------------------------------------
        # START DJANGO
        # ----------------------------------------------------

        log_file.write(
            "\n"
            + "=" * 70
            + "\n"
        )

        log_file.write(
            "STARTING DJANGO DEVELOPMENT SERVER\n"
        )

        log_file.write(
            f"URL: {application_url}\n"
        )

        log_file.write(
            f"DJANGO_SETTINGS_MODULE: "
            f"{package_name}.settings\n"
        )

        log_file.write(
            "=" * 70
            + "\n"
        )

        log_file.flush()

        # ----------------------------------------------------
        # IMPORTANT:
        # Explicitly construct the environment.
        # This prevents AgentForge's own environment
        # from forcing backend.settings.
        # ----------------------------------------------------

        environment = _django_environment(
            project_folder,
            package_name,
        )

        creation_flags = 0

        if sys.platform.startswith(
            "win"
        ):

            creation_flags = (
                subprocess.CREATE_NEW_PROCESS_GROUP
            )

        process = subprocess.Popen(
            [
                sys.executable,
                str(manage_py),
                "runserver",
                f"{host}:{port}",
                "--noreload",
            ],
            cwd=str(project_folder),
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=creation_flags,
        )

        # ----------------------------------------------------
        # WAIT FOR SERVER
        # ----------------------------------------------------

        started = False

        for _ in range(40):

            time.sleep(0.25)

            if _is_port_open(
                host,
                port,
            ):

                started = True
                break

            if process.poll() is not None:
                break

        # ----------------------------------------------------
        # SERVER FAILED
        # ----------------------------------------------------

        if not started:

            log_file.flush()
            log_file.close()

            try:

                error_text = (
                    log_path.read_text(
                        encoding="utf-8",
                        errors="replace",
                    )[-12000:]
                )

            except Exception:

                error_text = (
                    "Unable to read the "
                    "runtime log."
                )

            return {
                "success": False,
                "url": "",
                "port": port,
                "message": (
                    "The generated Django "
                    "application could not be started.\n\n"
                    + error_text
                ),
                "log_path": log_path,
            }

        # ----------------------------------------------------
        # SERVER STARTED
        # ----------------------------------------------------

        return {
            "success": True,
            "url": application_url,
            "port": port,
            "message": (
                "Generated Django application "
                "was prepared successfully.\n\n"
                "Django validation passed, "
                "MySQL migrations were applied, "
                "and the application is now running."
            ),
            "log_path": log_path,
        }

    except Exception as exc:

        try:
            log_file.close()

        except Exception:
            pass

        return {
            "success": False,
            "url": "",
            "port": port,
            "message": (
                "Unexpected runtime error:\n\n"
                + str(exc)
            ),
            "log_path": log_path,
        }


# ============================================================
# INSPECT GENERATED FILE
# ============================================================

@login_required
def inspect_project_file(
    request,
    project_id,
):
    """
    Display a generated file inside
    the AgentForge interface.
    """

    project = get_object_or_404(
        Project,
        id=project_id,
        owner=request.user,
    )

    relative_path = (
        request.GET.get(
            "path",
            "",
        ).strip()
    )

    project_folder = (
        _get_project_folder(project)
    )

    file_path = _safe_project_file(
        project_folder,
        relative_path,
    )

    try:

        content = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        )

    except Exception as exc:

        return HttpResponse(
            (
                "Unable to read generated file: "
                + str(exc)
            ),
            status=500,
        )

    return render(
        request,
        "webapp/project_file_inspect.html",
        {
            "project": project,
            "file": {
                "name": file_path.name,
                "path": str(
                    file_path.relative_to(
                        project_folder
                    )
                ),
            },
            "content": content,
        },
    )


# ============================================================
# RUN APPLICATION
# ============================================================

@login_required
def run_project_application(
    request,
    project_id,
):
    """
    Run the generated Django application.

    The button performs:

        Detect Django package
        ↓
        Repair package references
        ↓
        Set DJANGO_SETTINGS_MODULE
        ↓
        Django check
        ↓
        makemigrations
        ↓
        migrate
        ↓
        runserver
    """

    project = get_object_or_404(
        Project,
        id=project_id,
        owner=request.user,
    )

    if request.method != "POST":

        return HttpResponse(
            (
                "Run Application must be "
                "started using the Run "
                "Application button."
            ),
            status=405,
        )

    result = _start_django_project(
        project
    )

    return render(
        request,
        "webapp/project_run.html",
        {
            "project": project,
            "result": result,
        },
    )