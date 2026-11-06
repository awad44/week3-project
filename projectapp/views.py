from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from tasks.models import OrganizationMembership
from tasks.pagination import TaskPageNumberPagination

from .filters import ProjectFilter
from .models import Project
from .permissions import ProjectRBACPermission
from .serializers import ProjectSerializer


# CRUD routes provided by ModelViewSet; available under /api/ and /api/v1/:
# GET    /projects/      -> list()
# GET    /projects/{id}/ -> retrieve()
# POST   /projects/      -> create()
# PUT    /projects/{id}/ -> update()
# PATCH  /projects/{id}/ -> partial_update()
# DELETE /projects/{id}/ -> destroy()
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
            .select_related("organization", "created_by")
            .order_by("id")
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
