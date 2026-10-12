# after adding idempotency key #20
from django.db import IntegrityError, transaction
from django_filters.rest_framework import DjangoFilterBackend

# api documentation #21
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import (
    OrderingFilter,
    SearchFilter,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import (
    JWTAuthentication,
)

from .filters import TaskFilter
from .models import OrganizationMembership, Project, Task, TaskCreateIdempotency
from .pagination import TaskPageNumberPagination
from .permissions import ProjectRBACPermission, TaskRBACPermission
from .serializers import (
    ProjectSerializer,
    TaskSerializer,
    TaskV2Serializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List tasks",
        description=(
            "Return paginated tasks belonging to the "
            "authenticated user's organization. "
            "Supports filtering, searching and ordering."
        ),
        tags=["Tasks"],
    ),
    retrieve=extend_schema(
        summary="Retrieve a task",
        description=(
            "Retrieve one task from the user's organization. "
            "A task outside that organization is not visible."
        ),
        tags=["Tasks"],
    ),
    update=extend_schema(
        summary="Replace a task",
        description=(
            "Update a task using PUT. Editors may modify "
            "their own pending tasks. Managers may modify "
            "tasks in their organization."
        ),
        tags=["Tasks"],
    ),
    partial_update=extend_schema(
        summary="Partially update a task",
        description=(
            "Update selected task fields using PATCH. "
            "Editors may modify only their own pending tasks. "
            "Managers may modify any task in their organization."
        ),
        tags=["Tasks"],
    ),
    destroy=extend_schema(
        summary="Delete a task",
        description=(
            "Delete a task in the user's organization. "
            "Requires the TaskManager role or equivalent "
            "delete_task permission."
        ),
        tags=["Tasks"],
    ),
)
class TaskViewSet(viewsets.ModelViewSet):

    # Database records
    queryset = Task.objects.none()

    throttle_scope = "tasks"

    def get_organization_id(self):

        user = self.request.user

        if not user.is_authenticated:
            return None

        return (
            OrganizationMembership.objects.filter(user=user)
            .values_list("organization_id", flat=True)
            .first()
        )

    def get_queryset(self):

        organization_id = self.get_organization_id()

        if organization_id is None:
            return Task.objects.none()

        return Task.objects.filter(organization_id=organization_id).order_by("id")

    def perform_create(self, serializer):

        organization_id = self.get_organization_id()

        if organization_id is None:
            raise PermissionDenied("You are not assigned to an organization.")
        serializer.save(
            organization_id=organization_id,
            owner=self.request.user,
        )

    # after adding idempotency key #20
    # api Document the Idempotency-Key header
    @extend_schema(
        summary="Create a task",
        description=(
            "Create a task in the authenticated user's organization. "
            "The server automatically assigns the owner and organization. "
            "Requires task creation permission. "
            "An optional Idempotency-Key prevents duplicate creation "
            "when the same logical request is retried. "
            "The same key with different data returns HTTP 409."
        ),
        tags=["Tasks"],
        parameters=[
            OpenApiParameter(
                name="Idempotency-Key",
                type=str,
                location=OpenApiParameter.HEADER,
                required=False,
                description=(
                    "Unique key of 8 to 128 characters. "
                    "Reuse it when retrying the same task creation."
                ),
            )
        ],
    )
    def create(self, request, *args, **kwargs):

        key = request.headers.get("Idempotency-Key")

        # Preserve normal POST behavior when no key is given.
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

        # Validate the task using our existing serializer.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Store the logical content of the request.
        payload = {
            "api_version": request.version or "v1",
            "title": serializer.validated_data["title"],
            "description": serializer.validated_data.get("description", ""),
            "completed": serializer.validated_data.get("completed", False),
            "project_id": (
                serializer.validated_data["project"].id
                if "project" in serializer.validated_data
                else None
            ),
        }

        lookup = {
            "user": request.user,
            "organization_id": organization_id,
            "key": key,
        }

        try:
            with transaction.atomic():

                record = TaskCreateIdempotency.objects.create(
                    **lookup,
                    request_payload=payload,
                    response_payload={},
                )

                # Uses our existing organization and owner logic.
                self.perform_create(serializer)

                result = dict(serializer.data)

                # Save the original successful response.
                record.response_payload = result
                record.save(update_fields=["response_payload"])

        except IntegrityError:

            # Another request already used this key.
            record = TaskCreateIdempotency.objects.filter(**lookup).first()

            if record is None:
                raise

            # Same key, different request: reject it.
            if record.request_payload != payload:
                return Response(
                    {
                        "error": {
                            "code": "idempotency_conflict",
                            "message": (
                                "This key was already used " "with different task data."
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

        # First successful request.
        return Response(
            result,
            status=status.HTTP_201_CREATED,
            headers={"Idempotency-Replayed": "false"},
        )

    # Default serializer
    serializer_class = TaskSerializer

    # This tells DRF to use session-based authentication for this ViewSet.
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    # This tells DRF to deny access when the requester is not authenticated.
    permission_classes = [IsAuthenticated, TaskRBACPermission]

    # Pagination from #8
    pagination_class = TaskPageNumberPagination

    # Filtering, searching, and ordering
    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    # Filtering from #9
    filterset_class = TaskFilter

    # Searching from #9
    search_fields = [
        "title",
        "description",
    ]

    # New: allowed ordering fields
    ordering_fields = [
        "id",
        "title",
        "completed",
        "created_at",
    ]

    # New: default ordering
    ordering = ["id"]

    # API versioning from #7
    def get_serializer_class(self):
        if self.request.version == "v2":
            return TaskV2Serializer

        return TaskSerializer


class ProjectViewSet(viewsets.ModelViewSet):

    queryset = Project.objects.none()
    serializer_class = ProjectSerializer

    authentication_classes = [
        JWTAuthentication,
        SessionAuthentication,
    ]

    permission_classes = [
        IsAuthenticated,
        ProjectRBACPermission,
    ]

    pagination_class = TaskPageNumberPagination

    throttle_scope = "projects"

    filter_backends = [
        SearchFilter,
        OrderingFilter,
    ]

    search_fields = ["name", "description"]

    ordering_fields = ["id", "name", "created_at"]

    ordering = ["id"]

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
            .select_related(
                "organization",
                "created_by",
            )
            .order_by("id")
        )

    def perform_create(self, serializer):

        organization_id = self.get_organization_id()

        if organization_id is None:
            raise PermissionDenied("You are not assigned to an organization.")

        serializer.save(
            organization_id=organization_id,
            created_by=self.request.user,
        )

    def perform_destroy(self, instance):

        if instance.tasks.exists():
            raise ValidationError(
                {"project": ["Cannot delete a project that contains tasks."]}
            )

        instance.delete()
