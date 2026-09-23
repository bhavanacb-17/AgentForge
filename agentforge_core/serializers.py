from rest_framework import serializers

from .models import (
    Project,
    ProjectMessage,
    ProjectFile,
    ProjectHistory,
    ProjectDocumentation,
)


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


class ProjectMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectMessage
        fields = "__all__"


class ProjectFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectFile
        fields = "__all__"


class ProjectHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectHistory
        fields = "__all__"


class ProjectDocumentationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectDocumentation
        fields = "__all__"