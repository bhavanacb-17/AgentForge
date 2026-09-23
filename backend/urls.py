from django.contrib import admin
from django.urls import include, path


urlpatterns = [

    # Django Admin
    path(
        "admin/",
        admin.site.urls,
    ),

    # AgentForge REST API
    path(
        "api/",
        include("agentforge_core.urls"),
    ),

    # AgentForge Web Application
    path(
        "",
        include("webapp.urls"),
    ),
]