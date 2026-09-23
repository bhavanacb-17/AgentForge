from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.home,
        name="home",
    ),

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

    path(
        "projects/<int:project_id>/",
        views.project_workspace,
        name="project-workspace",
    ),

    path(
        "projects/<int:project_id>/chat/",
        views.project_chat,
        name="project-chat",
    ),

    path(
        "projects/<int:project_id>/pipeline/",
        views.project_pipeline,
        name="project-pipeline",
    ),

    path(
        "projects/<int:project_id>/files/",
        views.project_files,
        name="project-files",
    ),
]