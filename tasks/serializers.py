from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import OrganizationMembership, Project, Task


# API Version 1
class TaskSerializer(serializers.ModelSerializer):

    # Information about the task owner
    owner_id = serializers.IntegerField(read_only=True)

    owner_username = serializers.CharField(source="owner.username", read_only=True)

    # Information about the organization
    organization_id = serializers.IntegerField(read_only=True)

    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )

    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.none(),
        required=True,
        allow_null=False,
    )

    project_name = serializers.CharField(
        source="project.name",
        read_only=True,
    )

    class Meta:
        model = Task

        fields = [
            "id",
            "title",
            "description",
            "completed",
            "created_at",
            # Ownership fields
            "owner_id",
            "owner_username",
            # Tenant fields
            "organization_id",
            "organization_name",
            "project",
            "project_name",
        ]

        read_only_fields = [
            "id",
            "created_at",
        ]

    # 1. Validate one field: title
    def validate_title(self, value):
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "Title must contain at least 3 characters."
            )

        return value

    # 2. Validate one field: description
    def validate_description(self, value):
        if len(value) > 1000:
            raise serializers.ValidationError(
                "Description cannot exceed 1000 characters."
            )

        return value

    # 3. Validate a combination of fields
    def validate(self, attrs):
        existing_task = self.instance

        completed = attrs.get(
            "completed", existing_task.completed if existing_task else False
        )

        description = attrs.get(
            "description", existing_task.description if existing_task else ""
        )

        if completed and not description.strip():
            raise serializers.ValidationError(
                {"description": ["A completed task must have a description."]}
            )

        return attrs

    def get_fields(self):
        fields = super().get_fields()

        request = self.context.get("request")

        if request and request.user.is_authenticated:

            organization_id = (
                OrganizationMembership.objects.filter(user=request.user)
                .values_list(
                    "organization_id",
                    flat=True,
                )
                .first()
            )

            if organization_id is not None:
                fields["project"].queryset = Project.objects.filter(
                    organization_id=organization_id
                )

        return fields


# API Version 2
class TaskV2Serializer(TaskSerializer):

    title_length = serializers.SerializerMethodField()

    class Meta(TaskSerializer.Meta):
        fields = TaskSerializer.Meta.fields + ["title_length"]

    # The new decorator tells the documentation generator that this method returns an integer.
    @extend_schema_field(int)
    def get_title_length(self, obj):
        return len(obj.title)


class ProjectSerializer(serializers.ModelSerializer):

    organization_id = serializers.IntegerField(read_only=True)

    organization_name = serializers.CharField(
        source="organization.name", read_only=True
    )

    created_by_id = serializers.IntegerField(read_only=True)

    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
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

        read_only_fields = [
            "id",
            "created_at",
        ]
