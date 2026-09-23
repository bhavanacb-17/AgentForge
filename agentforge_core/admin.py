from django.contrib import admin

from .models import (
    Project,
    ProjectMessage,
    ProjectFile,
    ProjectHistory,
    ProjectDocumentation,
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "owner",
        "status",
        "programming_language",
        "framework",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "programming_language",
        "framework",
        "database",
    )

    search_fields = (
        "name",
        "description",
        "requirements",
        "owner__username",
    )


@admin.register(ProjectMessage)
class ProjectMessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project",
        "role",
        "created_at",
    )

    list_filter = ("role",)
    search_fields = ("project__name", "message")


@admin.register(ProjectFile)
class ProjectFileAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project",
        "file_name",
        "file_path",
        "file_size",
        "updated_at",
    )

    search_fields = (
        "project__name",
        "file_name",
        "file_path",
    )


@admin.register(ProjectHistory)
class ProjectHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project",
        "event_type",
        "created_at",
    )

    list_filter = ("event_type",)
    search_fields = (
        "project__name",
        "description",
    )


@admin.register(ProjectDocumentation)
class ProjectDocumentationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "project",
        "created_at",
        "updated_at",
    )

    search_fields = ("project__name", "content")