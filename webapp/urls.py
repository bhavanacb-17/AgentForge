from django.urls import path

from . import views
from . import runtime_views


urlpatterns = [

    # ========================================================
    # MAIN
    # ========================================================

    path(
        "",
        views.home,
        name="home",
    ),

    # ========================================================
    # AUTHENTICATION
    # ========================================================

    path(
        "login/",
        views.login_view,
        name="login",
    ),

    path(
        "register/",
        views.register_view,
        name="register",
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),

    # ========================================================
    # PROJECT DASHBOARD
    # ========================================================

    path(
        "projects/",
        views.dashboard,
        name="dashboard",
    ),

    path(
        "projects/create/",
        views.create_project,
        name="create-project",
    ),

    # ========================================================
    # PROJECT MANAGEMENT
    # ========================================================

    path(
        "projects/<int:project_id>/",
        views.project_workspace,
        name="project-workspace",
    ),

    path(
        "projects/<int:project_id>/edit/",
        views.edit_project,
        name="edit-project",
    ),

    path(
        "projects/<int:project_id>/delete/",
        views.delete_project,
        name="delete-project",
    ),

    path(
        "projects/<int:project_id>/duplicate/",
        views.duplicate_project,
        name="duplicate-project",
    ),

    # ========================================================
    # AI CHAT
    # ========================================================

    path(
        "projects/<int:project_id>/chat/",
        views.project_chat,
        name="project-chat",
    ),

    # ========================================================
    # REQUIREMENTS
    # ========================================================

    path(
        "projects/<int:project_id>/requirements/",
        views.project_requirements,
        name="project-requirements",
    ),

    # ========================================================
    # AI PIPELINE
    # ========================================================

    path(
        "projects/<int:project_id>/pipeline/",
        views.project_pipeline,
        name="project-pipeline",
    ),

    # ========================================================
    # GENERATED FILES
    # ========================================================

    path(
        "projects/<int:project_id>/files/",
        views.project_files,
        name="project-files",
    ),

    path(
        "projects/<int:project_id>/files/inspect/",
        runtime_views.inspect_project_file,
        name="inspect-project-file",
    ),

    path(
        "projects/<int:project_id>/files/run/",
        runtime_views.run_project_application,
        name="run-project-application",
    ),

    path(
        "projects/<int:project_id>/files/download/",
        views.download_project_file,
        name="download-project-file",
    ),

    path(
        "projects/<int:project_id>/files/download-zip/",
        views.download_project_zip,
        name="download-project-zip",
    ),

    # ========================================================
    # DOCUMENTATION
    # ========================================================

    path(
        "projects/<int:project_id>/documentation/",
        views.project_documentation,
        name="project-documentation",
    ),

    path(
        "projects/<int:project_id>/documentation/download/docx/",
        views.download_documentation_docx,
        name="download-documentation-docx",
    ),

    path(
        "projects/<int:project_id>/documentation/download/pdf/",
        views.download_documentation_pdf,
        name="download-documentation-pdf",
    ),

    # ========================================================
    # HISTORY
    # ========================================================

    path(
        "projects/<int:project_id>/history/",
        views.project_history,
        name="project-history",
    ),

    # ========================================================
    # SETTINGS
    # ========================================================

    path(
        "projects/<int:project_id>/settings/",
        views.project_settings,
        name="project-settings",
    ),

    path(
        "projects/<int:project_id>/settings/archive/",
        views.archive_project,
        name="archive-project",
    ),

    path(
        "projects/<int:project_id>/settings/restore/",
        views.restore_project,
        name="restore-project",
    ),

    path(
        "projects/<int:project_id>/settings/clear-chat/",
        views.clear_project_chat,
        name="clear-project-chat",
    ),

    path(
        "projects/<int:project_id>/settings/delete-files/",
        views.delete_project_files,
        name="delete-project-files",
    ),
]