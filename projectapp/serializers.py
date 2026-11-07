from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    organization_id = serializers.IntegerField(read_only=True)
    organization_name = serializers.CharField(
        source="organization.name",
        read_only=True,
    )
    created_by_id = serializers.IntegerField(read_only=True)
    created_by_username = serializers.CharField(
        source="created_by.username",
        read_only=True,
    )

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "description",
            "organization_id",
            "organization_name",
            "created_by_id",
            "created_by_username",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_name(self, value):
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "Project name must contain at least 3 characters."
            )

        return value

    def validate_description(self, value):
        if len(value) > 1000:
            raise serializers.ValidationError(
                "Description cannot exceed 1000 characters."
            )

        return value


class ProjectV2Serializer(ProjectSerializer):
    task_count = serializers.SerializerMethodField()

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + ["task_count"]

    @extend_schema_field(int)
    # obj is the current Project
    def get_task_count(self, obj):
        # getattr is a built-in Python function. It looks up an attribute by its name:
        annotated_count = getattr(obj, "task_count", None)
        if annotated_count is not None:
            return annotated_count

        return obj.tasks.count()
