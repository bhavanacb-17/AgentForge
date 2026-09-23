from django.urls import path

from . import views


urlpatterns = [
    path("", views.api_home, name="api-home"),

    # Projects
    path(
        "projects/",
        views.ProjectListCreateView.as_view(),
        name="project-list-create",
    ),

    path(
        "projects/<int:pk>/",
        views.ProjectDetailView.as_view(),
        name="project-detail",
    ),

    # Project messages / chat
    path(
        "projects/<int:project_id>/messages/",
        views.ProjectMessageListCreateView.as_view(),
        name="project-messages",
    ),

    # Generated files
    path(
        "projects/<int:project_id>/files/",
        views.ProjectFileListView.as_view(),
        name="project-files",
    ),

    # Project history
    path(
        "projects/<int:project_id>/history/",
        views.ProjectHistoryListView.as_view(),
        name="project-history",
    ),

    # Documentation
    path(
        "projects/<int:project_id>/documentation/",
        views.ProjectDocumentationView.as_view(),
        name="project-documentation",
    ),
]