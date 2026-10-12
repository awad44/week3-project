from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import OrganizationMembership


class IsStaffOrReadOnly(BasePermission):

    message = "Only staff users can modify tasks."

    def has_permission(self, request, view):

        if request.method in SAFE_METHODS:
            return True

        return request.user.is_authenticated and request.user.is_staff


class TaskRBACPermission(BasePermission):

    message = "You do not have permission to perform this task action."

    permission_map = {
        "GET": "tasks.view_task",
        "HEAD": "tasks.view_task",
        "OPTIONS": "tasks.view_task",
        "POST": "tasks.add_task",
        "PUT": "tasks.change_task",
        "PATCH": "tasks.change_task",
        "DELETE": "tasks.delete_task",
    }

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        if not OrganizationMembership.objects.filter(user=request.user).exists():
            return False

        required_permission = self.permission_map.get(request.method)

        if required_permission is None:
            return False

        return request.user.has_perm(required_permission)

    def has_object_permission(self, request, view, obj):

        # 1. Check authentication
        if not request.user.is_authenticated:
            return False

        # 2. Check organization / tenant isolation
        belongs_to_organization = OrganizationMembership.objects.filter(
            user=request.user,
            organization_id=obj.organization_id,
        ).exists()

        if not belongs_to_organization:
            return False

        # 3. Allow reading within the organization
        if request.method in SAFE_METHODS:
            return True

        # 4. Handle task updates
        if request.method in ("PUT", "PATCH"):

            # Managers can update tasks in their organization
            is_manager = (
                request.user.is_superuser
                or request.user.groups.filter(name="TaskManagers").exists()
            )

            if is_manager:
                return True

            # Check whether the authenticated user owns the task
            is_owner = obj.owner_id == request.user.id

            # Editors can update only their own pending tasks
            return is_owner and not obj.completed

        # 5. Handle task deletion
        if request.method == "DELETE":
            return request.user.has_perm("tasks.delete_task")

        return False


class ProjectRBACPermission(BasePermission):

    message = "You do not have permission to perform this project action."

    permission_map = {
        "GET": "tasks.view_project",
        "HEAD": "tasks.view_project",
        "OPTIONS": "tasks.view_project",
        "POST": "tasks.add_project",
        "PUT": "tasks.change_project",
        "PATCH": "tasks.change_project",
        "DELETE": "tasks.delete_project",
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
