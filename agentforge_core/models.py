from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("archived", "Archived"),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    requirements = models.TextField(blank=True)

    category = models.CharField(max_length=100, blank=True)
    programming_language = models.CharField(max_length=100, blank=True)
    framework = models.CharField(max_length=100, blank=True)
    database = models.CharField(max_length=100, blank=True)
    additional_instructions = models.TextField(blank=True)

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="active"
    )

    ai_model = models.CharField(
        max_length=100,
        default="Gemini"
    )

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="projects"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProjectMessage(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.project.name} - {self.role}"


class ProjectFile(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="files"
    )

    file_path = models.CharField(max_length=500)
    file_name = models.CharField(max_length=255)
    file_size = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("project", "file_path")

    def __str__(self):
        return self.file_path


class ProjectHistory(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="history"
    )

    event_type = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.project.name} - {self.event_type}"


class ProjectDocumentation(models.Model):
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name="documentation"
    )

    content = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Documentation - {self.project.name}"