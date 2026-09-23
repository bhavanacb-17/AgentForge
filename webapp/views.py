from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from agentforge_core.models import Project
from agents.pipeline import AgentPipeline
from projects.project_storage import ProjectStorage

from pathlib import Path


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


def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def dashboard(request):
    projects = Project.objects.filter(
        owner=request.user
    ).order_by("-updated_at")

    return render(
        request,
        "webapp/dashboard.html",
        {"projects": projects},
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