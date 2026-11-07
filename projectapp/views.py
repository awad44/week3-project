from django.db import IntegrityError, transaction
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from tasks.models import OrganizationMembership
from tasks.pagination import TaskPageNumberPagination

from .filters import ProjectFilter
from .models import Project, ProjectCreateIdempotency
from .permissions import ProjectRBACPermission
from .serializers import ProjectSerializer, ProjectV2Serializer


# CRUD routes provided by ModelViewSet; available under /api/ and /api/v1/:
# GET    /projects/      -> list()
# GET    /projects/{id}/ -> retrieve()
# POST   /projects/      -> create()
# PUT    /projects/{id}/ -> update()
# PATCH  /projects/{id}/ -> partial_update()
# DELETE /projects/{id}/ -> destroy()
@extend_schema_view(
    list=extend_schema(
        summary="List projects",
        description=(
            "Return paginated projects belonging to the authenticated user's "
            "organization. Supports filtering, searching and ordering. "
            "Requires project view permission."
        ),
        tags=["Projects"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a project",
        description=(
            "Return one project from the authenticated user's organization. "
            "Projects in other organizations are not visible."
        ),
        tags=["Projects"],
    ),
    create=extend_schema(
        summary="Create a project",
        description=(
            "Create a project in the authenticated user's organization. "
            "The server sets the organization and creator. Requires project "
            "creation permission. Reusing an Idempotency-Key with the same "
            "data returns the saved response; using it with different data "
            "returns HTTP 409."
        ),
        tags=["Projects"],
        parameters=[
            OpenApiParameter(
                name="Idempotency-Key",
                type=str,
                location=OpenApiParameter.HEADER,
                required=False,
                description=(
                    "Unique key of 8 to 128 characters. Reuse it when retrying "
                    "the same project creation request."
                ),
            )
        ],
    ),
    update=extend_schema(
        summary="Replace a project",
        description=(
            "Replace a project's editable fields using PUT. Requires project "
            "change permission and access to the project."
        ),
        tags=["Projects"],
    ),
    partial_update=extend_schema(
        summary="Partially update a project",
        description=(
            "Update selected editable project fields using PATCH. Requires "
            "project change permission and access to the project."
        ),
        tags=["Projects"],
    ),
    destroy=extend_schema(
        summary="Delete a project",
        description=(
            "Delete a project in the authenticated user's organization. "
            "Deletion is rejected while the project contains tasks and "
            "requires project delete permission."
        ),
        tags=["Projects"],
    ),
)
class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.none()
    throttle_scope = "projects"
    serializer_class = ProjectSerializer
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated, ProjectRBACPermission]
    pagination_class = TaskPageNumberPagination
    filter_backends = [SearchFilter, OrderingFilter, DjangoFilterBackend]
    search_fields = ["name", "description"]
    ordering_fields = ["id", "name", "created_at"]
    ordering = ["id"]
    filterset_class = ProjectFilter

    def get_organization_id(self):
        if not self.request.user.is_authenticated:
            return None

        return (
            OrganizationMembership.objects.filter(user=self.request.user)
            .values_list("organization_id", flat=True)
            .first()
        )

    def get_queryset(self):
        organization_id = self.get_organization_id()

        if organization_id is None:
            return Project.objects.none()

        return (
            Project.objects.filter(organization_id=organization_id)
            .annotate(task_count=Count("tasks"))
            .select_related("organization", "created_by")
            .order_by("id")
        )

    # POST create() accepts an optional Idempotency-Key for safe retries.
    def create(self, request, *args, **kwargs):
        key = request.headers.get("Idempotency-Key")

        if key is None:
            return super().create(request, *args, **kwargs)

        key = key.strip()
        if not 8 <= len(key) <= 128:
            raise ValidationError(
                {"Idempotency-Key": ["Key must contain 8 to 128 characters."]}
            )

        organization_id = self.get_organization_id()
        if organization_id is None:
            raise PermissionDenied("You are not assigned to an organization.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Store the logical content of the request.
        payload = {
            "api_version": request.version or "v1",
            "name": serializer.validated_data["name"],
            "description": serializer.validated_data.get("description", ""),
        }
        lookup = {
            "user": request.user,
            "organization_id": organization_id,
            "key": key,
        }

        try:
            with transaction.atomic():
                record = ProjectCreateIdempotency.objects.create(
                    **lookup,
                    request_payload=payload,
                    response_payload={},
                )
                self.perform_create(serializer)
                result = dict(serializer.data)
                record.response_payload = result
                record.save(update_fields=["response_payload"])
        except IntegrityError:
            record = ProjectCreateIdempotency.objects.filter(**lookup).first()
            if record is None:
                raise

            if record.request_payload != payload:
                return Response(
                    {
                        "error": {
                            "code": "idempotency_conflict",
                            "message": (
                                "This key was already used with different "
                                "project data."
                            ),
                            "details": None,
                        }
                    },
                    status=status.HTTP_409_CONFLICT,
                )
            # Same key, same request: return saved response.
            return Response(
                record.response_payload,
                status=status.HTTP_201_CREATED,
                headers={"Idempotency-Replayed": "true"},
            )
        # first successful request: return the new project.
        return Response(
            result,
            status=status.HTTP_201_CREATED,
            headers={"Idempotency-Replayed": "false"},
        )

    # POST create() calls this hook to set the organization and creator.
    def perform_create(self, serializer):
        organization_id = self.get_organization_id()

        if organization_id is None:
            raise PermissionDenied("You are not assigned to an organization.")

        serializer.save(
            organization_id=organization_id,
            created_by=self.request.user,
        )

    # DELETE destroy() calls this hook; block deletion when tasks exist.
    def perform_destroy(self, instance):
        if instance.tasks.exists():
            raise ValidationError(
                {"project": ["Cannot delete a project that contains tasks."]}
            )

        instance.delete()

    # API versioning: return a different serializer for v2, which adds task_count.
    def get_serializer_class(self):
        if self.request.version == "v2":
            return ProjectV2Serializer

        return ProjectSerializer
