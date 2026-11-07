from rest_framework.permissions import SAFE_METHODS, BasePermission

from tasks.models import OrganizationMembership


class ProjectRBACPermission(BasePermission):

    message = "You do not have permission to perform this project action."

    permission_map = {
        "GET": "projectapp.view_project",
        "HEAD": "projectapp.view_project",
        "OPTIONS": "projectapp.view_project",
        "POST": "projectapp.add_project",
        "PUT": "projectapp.change_project",
        "PATCH": "projectapp.change_project",
        "DELETE": "projectapp.delete_project",
    }

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        if not OrganizationMembership.objects.filter(user=request.user).exists():
            return False

        required_permission = self.permission_map.get(request.method)

        return bool(required_permission and request.user.has_perm(required_permission))

    def has_object_permission(self, request, view, obj):

        # Project must belong to the user's organization.
        same_organization = OrganizationMembership.objects.filter(
            user=request.user,
            organization_id=obj.organization_id,
        ).exists()

        if not same_organization:
            return False

        if request.method in SAFE_METHODS:
            return True

        is_manager = (
            request.user.is_superuser
            or request.user.groups.filter(name="TaskManagers").exists()
        )

        if request.method in ("PUT", "PATCH"):
            return is_manager or obj.created_by_id == request.user.id

        if request.method == "DELETE":
            return request.user.has_perm("tasks.delete_project")

        return False
