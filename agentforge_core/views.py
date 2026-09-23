from django.http import JsonResponse
from rest_framework import generics

from .models import (
    Project,
    ProjectMessage,
    ProjectFile,
    ProjectHistory,
    ProjectDocumentation,
)

from .serializers import (
    ProjectSerializer,
    ProjectMessageSerializer,
    ProjectFileSerializer,
    ProjectHistorySerializer,
    ProjectDocumentationSerializer,
)


def api_home(request):
    return JsonResponse({
        "success": True,
        "application": "AgentForge",
        "message": "AgentForge API is running",
    })


class ProjectListCreateView(generics.ListCreateAPIView):
    queryset = Project.objects.all().order_by("-created_at")
    serializer_class = ProjectSerializer


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class ProjectMessageListCreateView(generics.ListCreateAPIView):
    serializer_class = ProjectMessageSerializer

    def get_queryset(self):
        return ProjectMessage.objects.filter(
            project_id=self.kwargs["project_id"]
        ).order_by("created_at")


class ProjectFileListView(generics.ListAPIView):
    serializer_class = ProjectFileSerializer

    def get_queryset(self):
        return ProjectFile.objects.filter(
            project_id=self.kwargs["project_id"]
        ).order_by("-updated_at")


class ProjectHistoryListView(generics.ListAPIView):
    serializer_class = ProjectHistorySerializer

    def get_queryset(self):
        return ProjectHistory.objects.filter(
            project_id=self.kwargs["project_id"]
        ).order_by("-created_at")


class ProjectDocumentationView(generics.RetrieveUpdateAPIView):
    serializer_class = ProjectDocumentationSerializer

    def get_queryset(self):
        return ProjectDocumentation.objects.filter(
            project_id=self.kwargs["project_id"]
        )