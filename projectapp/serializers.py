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
