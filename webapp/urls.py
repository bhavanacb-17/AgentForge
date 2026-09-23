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
        "projects/<int:project_id>/",
        views.project_workspace,
        name="project-workspace",
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