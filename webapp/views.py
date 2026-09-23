from pathlib import Path
import shutil

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from agentforge_core.models import (
    Project,
    ProjectHistory,
    ProjectMessage,
)
from agents.pipeline import AgentPipeline
from projects.project_storage import ProjectStorage
from core.gemini_client import GeminiClient


def home(request):
    return render(request, "webapp/home.html")


def login_view(request):
    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        error = "Invalid username or password."

    return render(
        request,
        "webapp/login.html",
        {"error": error},
    )


def register_view(request):
    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not username or not email or not password:
            error = "All fields are required."

        elif password != confirm_password:
            error = "Passwords do not match."

        elif len(password) < 6:
            error = "Password must contain at least 6 characters."

        elif User.objects.filter(username=username).exists():
            error = "Username already exists."

        elif User.objects.filter(email=email).exists():
            error = "Email is already registered."

        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )

            login(request, user)
            return redirect("dashboard")

    return render(
        request,
        "webapp/register.html",
        {"error": error},
    )


def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def dashboard(request):
    projects = Project.objects.filter(
        owner=request.user
    ).order_by("-updated_at")

    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()

    if search:
        projects = projects.filter(
            name__icontains=search
        ) | projects.filter(
            description__icontains=search
        )

    valid_statuses = {
        choice[0]
        for choice in Project.STATUS_CHOICES
    }

    if status in valid_statuses:
        projects = projects.filter(status=status)

    return render(
        request,
        "webapp/dashboard.html",
        {
            "projects": projects,
            "search": search,
            "selected_status": status,
        },
    )


@login_required
def create_project(request):
    error = None

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        requirements = request.POST.get("requirements", "").strip()
        category = request.POST.get("category", "").strip()

        programming_language = request.POST.get(
            "programming_language",
            "",
        ).strip()

        framework = request.POST.get(
            "framework",
            "",
        ).strip()

        database = request.POST.get(
            "database",
            "",
        ).strip()

        additional_instructions = request.POST.get(
            "additional_instructions",
            "",
        ).strip()

        if not name:
            error = "Project name is required."

        elif Project.objects.filter(
            owner=request.user,
            name=name,
        ).exists():
            error = "You already have a project with this name."

        else:
            project = Project.objects.create(
                name=name,
                description=description,
                requirements=requirements,
                category=category,
                programming_language=programming_language,
                framework=framework,
                database=database,
                additional_instructions=additional_instructions,
                owner=request.user,
                status="active",
                ai_model="Gemini",
            )

            try:
                storage = ProjectStorage()
                storage.create_project_folder(project.id)
            except Exception:
                pass

            ProjectHistory.objects.create(
                project=project,
                event_type="project_created",
                description=(
                    f"Project created by {request.user.username}."
                ),
            )

            return redirect(
                "project-workspace",
                project_id=project.id,
            )

    return render(
        request,
        "webapp/create_project.html",
        {"error": error},
    )


@login_required
def edit_project(request, project_id):
    project = get_object_or_404(
        Project,
        id=project_id,
        owner=request.user,
    )

    error = None

    if request.method == "POST":

        name = request.POST.get("name", "").strip()

        duplicate_name = Project.objects.filter(
            owner=request.user,
            name=name,
        ).exclude(
            id=project.id
        ).exists()

        if not name:
            error = "Project name is required."

        elif duplicate_name:
            error = "You already have another project with this name."

        else:
            project.name = name

            project.description = request.POST.get(
                "description",
                "",
            ).strip()

            project.requirements = request.POST.get(
                "requirements",
                "",
            ).strip()

            project.category = request.POST.get(
                "category",
                "",
            ).strip()

            project.programming_language = request.POST.get(
                "programming_language",
                "",
            ).strip()

            project.framework = request.POST.get(
                "framework",
                "",
            ).strip()

            project.database = request.POST.get(
                "database",
                "",
            ).strip()

            project.additional_instructions = request.POST.get(
                "additional_instructions",
                "",
            ).strip()

            project.status = request.POST.get(
                "status",
                project.status,
            )

            project.save()

            ProjectHistory.objects.create(
                project=project,
                event_type="project_updated",
                description=(
                    f"Project updated by {request.user.username}."
                ),
            )

            return redirect(
                "project-workspace",
                project_id=project.id,
            )

    return render(
        request,
        "webapp/edit_project.html",
        {
            "project": project,
            "error": error,
        },
    )


@login_required
def delete_project(request, project_id):
    project = get_object_or_404(
        Project,
        id=project_id,
        owner=request.user,
    )

    if request.method == "POST":

        project_name = project.name

        try:
            storage = ProjectStorage()

            project_folder = Path(
                storage.get_project_folder(project.id)
            )

            if project_folder.exists():
                shutil.rmtree(project_folder)

        except Exception:
            pass

        ProjectHistory.objects.create(
            project=project,
            event_type="project_deleted",
            description=(
                f"Project '{project_name}' deleted by "
                f"{request.user.username}."
            ),
        )

        project.delete()

        return redirect("dashboard")

    return render(
        request,
        "webapp/delete_project.html",
        {"project": project},
    )


@login_required
def duplicate_project(request, project_id):
    source = get_object_or_404(
        Project,
        id=project_id,
        owner=request.user,
    )

    base_name = f"{source.name} Copy"
    new_name = base_name
    counter = 2

    while Project.objects.filter(
        owner=request.user,
        name=new_name,
    ).exists():
        new_name = f"{base_name} {counter}"
        counter += 1

    duplicated = Project.objects.create(
        name=new_name,
        description=source.description,
        requirements=source.requirements,
        category=source.category,
        programming_language=source.programming_language,
        framework=source.framework,
        database=source.database,
        additional_instructions=source.additional_instructions,
        status="active",
        ai_model=source.ai_model,
        owner=request.user,
    )

    try:
        storage = ProjectStorage()

        source_folder = Path(
            storage.get_project_folder(source.id)
        )

        destination_folder = Path(
            storage.get_project_folder(duplicated.id)
        )

        if source_folder.exists():
            shutil.copytree(
                source_folder,
                destination_folder,
                dirs_exist_ok=True,
            )
        else:
            storage.create_project_folder(
                duplicated.id
            )

    except Exception:
        pass

    ProjectHistory.objects.create(
        project=duplicated,
        event_type="project_duplicated",
        description=(
            f"Duplicated from project '{source.name}'."
        ),
    )

    return redirect(
        "project-workspace",
        project_id=duplicated.id,
    )


@login_required
def project_workspace(request, project_id):
    project = get_object_or_404(
        Project,
        id=project_id,
        owner=request.user,
    )

    return render(
        request,
        "webapp/project_workspace.html",
        {"project": project},
    )


@login_required
def project_chat(request, project_id):
    project = get_object_or_404(
        Project,
        id=project_id,
        owner=request.user,
    )

    if request.method == "POST":

        action = request.POST.get("action", "").strip()

        # -----------------------------------------
        # CLEAR CHAT
        # -----------------------------------------
        if action == "clear":

            ProjectMessage.objects.filter(
                project=project
            ).delete()

            ProjectHistory.objects.create(
                project=project,
                event_type="chat_cleared",
                description=(
                    f"Chat history cleared by "
                    f"{request.user.username}."
                ),
            )

            return redirect(
                "project-chat",
                project_id=project.id,
            )

        # -----------------------------------------
        # SEND MESSAGE
        # -----------------------------------------
        user_message = request.POST.get(
            "message",
            "",
        ).strip()

        if user_message:

            ProjectMessage.objects.create(
                project=project,
                role="user",
                message=user_message,
            )

            try:

                # Retrieve recent conversation history.
                previous_messages = ProjectMessage.objects.filter(
                    project=project
                ).order_by("-created_at")[:20]

                previous_messages = list(
                    reversed(previous_messages)
                )

                conversation = []

                for item in previous_messages:
                    conversation.append(
                        f"{item.role.upper()}: {item.message}"
                    )

                conversation_text = "\n".join(
                    conversation
                )

                # Build project context.
                project_context = f"""
PROJECT CONTEXT

Project Name:
{project.name}

Description:
{project.description}

Requirements:
{project.requirements}

Category:
{project.category}

Programming Language:
{project.programming_language}

Framework:
{project.framework}

Database:
{project.database}

Additional Instructions:
{project.additional_instructions}

AI Model:
{project.ai_model}
"""

                prompt = f"""
You are AgentForge AI, an AI software engineering
assistant working inside a specific software project.

Your job is to help the developer understand,
design, build, test, debug, review, and improve
the project.

Always use the project context when answering.

{project_context}

CONVERSATION HISTORY

{conversation_text}

CURRENT USER REQUEST

{user_message}

INSTRUCTIONS

1. Give a useful software-engineering response.
2. Stay relevant to the current project.
3. If the user asks for code, provide practical code.
4. If requirements are unclear, explain what is missing.
5. Do not pretend that code was executed if it was not.
6. Keep explanations structured and readable.
7. When appropriate, suggest the next development step.
"""

                client = GeminiClient()

                response = client.generate(
                    prompt
                )

                if response is None:
                    response = (
                        "AgentForge AI did not return a response. "
                        "Please try again."
                    )

                response_text = str(response).strip()

                ProjectMessage.objects.create(
                    project=project,
                    role="assistant",
                    message=response_text,
                )

                ProjectHistory.objects.create(
                    project=project,
                    event_type="chat_message_sent",
                    description=(
                        f"AI chat interaction by "
                        f"{request.user.username}."
                    ),
                )

            except Exception as exc:

                ProjectMessage.objects.create(
                    project=project,
                    role="assistant",
                    message=(
                        "AgentForge AI encountered an error "
                        "while processing your request.\n\n"
                        f"Error: {exc}"
                    ),
                )

            return redirect(
                "project-chat",
                project_id=project.id,
            )

    messages = ProjectMessage.objects.filter(
        project=project
    ).order_by("created_at")

    return render(
        request,
        "webapp/project_chat.html",
        {
            "project": project,
            "messages": messages,
        },
    )


@login_required
def project_pipeline(request, project_id):
    project = get_object_or_404(
        Project,
        id=project_id,
        owner=request.user,
    )

    result = None
    error = None

    if request.method == "POST":

        project_data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "requirements": project.requirements,
            "category": project.category,
            "programming_language": project.programming_language,
            "framework": project.framework,
            "database": project.database,
            "additional_instructions": project.additional_instructions,
        }

        try:

            ProjectHistory.objects.create(
                project=project,
                event_type="pipeline_started",
                description=(
                    "AI agent pipeline started."
                ),
            )

            pipeline = AgentPipeline(project_data)

            if hasattr(pipeline, "run"):
                result = pipeline.run()

            elif hasattr(pipeline, "execute"):
                result = pipeline.execute()

            elif hasattr(pipeline, "run_pipeline"):
                result = pipeline.run_pipeline()

            else:
                raise AttributeError(
                    "AgentPipeline does not contain "
                    "run(), execute(), or run_pipeline()."
                )

            ProjectHistory.objects.create(
                project=project,
                event_type="pipeline_completed",
                description=(
                    "AI agent pipeline completed."
                ),
            )

        except Exception as exc:
            error = str(exc)

    return render(
        request,
        "webapp/project_pipeline.html",
        {
            "project": project,
            "result": result,
            "error": error,
        },
    )


@login_required
def project_files(request, project_id):
    project = get_object_or_404(
        Project,
        id=project_id,
        owner=request.user,
    )

    storage = ProjectStorage()

    project_folder = Path(
        storage.get_project_folder(project.id)
    )

    files = []

    if project_folder.exists():

        for file_path in sorted(
            project_folder.rglob("*")
        ):

            if file_path.is_file():

                relative_path = file_path.relative_to(
                    project_folder
                )

                files.append(
                    {
                        "name": file_path.name,
                        "path": str(relative_path),
                        "size": file_path.stat().st_size,
                    }
                )

    return render(
        request,
        "webapp/project_files.html",
        {
            "project": project,
            "files": files,
        },
    )