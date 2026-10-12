from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from rest_framework.test import APITestCase

from .models import (
    Organization,
    OrganizationMembership,
    Project,
    Task,
)


class Week3APITests(APITestCase):

    def setUp(self):
        # Reset local throttling counters.
        cache.clear()

        User = get_user_model()

        # =====================================
        # 1. CREATE TEST ORGANIZATIONS
        # =====================================

        self.alpha = Organization.objects.create(name="Test Alpha")

        self.beta = Organization.objects.create(name="Test Beta")

        # =====================================
        # 2. CREATE TEST USERS
        # =====================================

        self.viewer = User.objects.create_user(
            username="test_viewer",
            password="TestPass123!",
        )

        self.editor = User.objects.create_user(
            username="test_editor",
            password="TestPass123!",
        )

        self.manager = User.objects.create_user(
            username="test_manager",
            password="TestPass123!",
        )

        # =====================================
        # 3. ASSIGN ORGANIZATION MEMBERSHIPS
        # =====================================

        for user, organization in [
            (self.viewer, self.beta),
            (self.editor, self.alpha),
            (self.manager, self.alpha),
        ]:
            OrganizationMembership.objects.create(
                user=user,
                organization=organization,
            )

        # =====================================
        # 4. CREATE RBAC GROUPS
        # =====================================

        task_type = ContentType.objects.get_for_model(Task)

        task_role_permissions = {
            "TaskViewers": [
                "view_task",
            ],
            "TaskEditors": [
                "view_task",
                "add_task",
                "change_task",
            ],
            "TaskManagers": [
                "view_task",
                "add_task",
                "change_task",
                "delete_task",
            ],
        }

        groups = {}

        # Create groups BEFORE assigning
        # Project permissions to them.
        for name, codenames in task_role_permissions.items():

            group = Group.objects.create(name=name)

            group.permissions.set(
                Permission.objects.filter(
                    content_type=task_type,
                    codename__in=codenames,
                )
            )

            groups[name] = group

        # =====================================
        # 5. ASSIGN PROJECT PERMISSIONS
        # =====================================

        project_type = ContentType.objects.get_for_model(Project)

        project_role_permissions = {
            "TaskViewers": [
                "view_project",
            ],
            "TaskEditors": [
                "view_project",
                "add_project",
                "change_project",
            ],
            "TaskManagers": [
                "view_project",
                "add_project",
                "change_project",
                "delete_project",
            ],
        }

        for name, codenames in project_role_permissions.items():

            groups[name].permissions.add(
                *Permission.objects.filter(
                    content_type=project_type,
                    codename__in=codenames,
                )
            )

        # =====================================
        # 6. ASSIGN USERS TO GROUPS
        # =====================================

        self.viewer.groups.add(groups["TaskViewers"])

        self.editor.groups.add(groups["TaskEditors"])

        self.manager.groups.add(groups["TaskManagers"])

        # =====================================
        # 7. CREATE TEST PROJECTS
        # =====================================

        self.alpha_project = Project.objects.create(
            name="Alpha Test Project",
            description="Project for Alpha tasks",
            organization=self.alpha,
            created_by=self.editor,
        )

        self.beta_project = Project.objects.create(
            name="Beta Test Project",
            description="Project for Beta tasks",
            organization=self.beta,
            created_by=self.viewer,
        )

        # =====================================
        # 8. CREATE TEST TASKS
        # =====================================

        self.editor_task = Task.objects.create(
            title="Editor Pending Task",
            description="Editable task",
            completed=False,
            organization=self.alpha,
            owner=self.editor,
            project=self.alpha_project,
        )

        self.manager_task = Task.objects.create(
            title="Manager Pending Task",
            description="Manager task",
            completed=False,
            organization=self.alpha,
            owner=self.manager,
            project=self.alpha_project,
        )

        self.beta_task = Task.objects.create(
            title="Beta Private Task",
            description="Private to Beta",
            completed=False,
            organization=self.beta,
            owner=self.viewer,
            project=self.beta_project,
        )

    # =========================================
    # TEST 1 — ANONYMOUS AUTHENTICATION
    # =========================================

    def test_anonymous_cannot_list_tasks(self):

        response = self.client.get("/api/v1/tasks/")

        self.assertEqual(
            response.status_code,
            401,
            response.data,
        )

    # =========================================
    # TEST 2 — VIEWER CANNOT CREATE TASKS
    # =========================================

    def test_viewer_cannot_create(self):

        self.client.force_authenticate(user=self.viewer)

        response = self.client.post(
            "/api/v1/tasks/",
            {
                "title": "Viewer Task",
                "description": "Should not be created",
                "completed": False,
                "project": self.beta_project.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
            response.data,
        )

    # =========================================
    # TEST 3 — EDITOR OWNERSHIP
    # =========================================

    def test_editor_can_only_update_own_pending_task(self):

        self.client.force_authenticate(user=self.editor)

        # Editor updates their own task.
        own_response = self.client.patch(
            f"/api/v1/tasks/{self.editor_task.id}/",
            {
                "title": "Updated Own Task",
            },
            format="json",
        )

        # Editor attempts to update Manager's task.
        other_response = self.client.patch(
            f"/api/v1/tasks/{self.manager_task.id}/",
            {
                "title": "Unauthorized Update",
            },
            format="json",
        )

        self.assertEqual(
            own_response.status_code,
            200,
            own_response.data,
        )

        self.assertEqual(
            other_response.status_code,
            403,
            other_response.data,
        )

        self.editor_task.refresh_from_db()
        self.manager_task.refresh_from_db()

        self.assertEqual(
            self.editor_task.title,
            "Updated Own Task",
        )

        self.assertEqual(
            self.manager_task.title,
            "Manager Pending Task",
        )

    # =========================================
    # TEST 4 — COMPLETED TASK PROTECTION
    # =========================================

    def test_editor_cannot_update_completed_task(self):

        self.editor_task.completed = True

        self.editor_task.save(update_fields=["completed"])

        self.client.force_authenticate(user=self.editor)

        response = self.client.patch(
            f"/api/v1/tasks/{self.editor_task.id}/",
            {
                "title": "Changed Completed Task",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
            response.data,
        )

        self.editor_task.refresh_from_db()

        self.assertEqual(
            self.editor_task.title,
            "Editor Pending Task",
        )

    # =========================================
    # TEST 5 — TASK TENANT ISOLATION
    # =========================================

    def test_manager_cannot_access_other_tenant(self):

        self.client.force_authenticate(user=self.manager)

        response = self.client.get(f"/api/v1/tasks/{self.beta_task.id}/")

        self.assertEqual(
            response.status_code,
            404,
            response.data,
        )

    # =========================================
    # TEST 6 — AUTOMATIC OWNER AND TENANT
    # =========================================

    def test_create_assigns_owner_and_organization(self):

        self.client.force_authenticate(user=self.editor)

        response = self.client.post(
            "/api/v1/tasks/",
            {
                "title": "New Editor Task",
                "description": "Testing automatic assignment",
                "completed": False,
                "project": self.alpha_project.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
            response.data,
        )

        self.assertIn(
            "id",
            response.data,
        )

        task = Task.objects.get(id=response.data["id"])

        # Verify automatically assigned owner.
        self.assertEqual(
            task.owner_id,
            self.editor.id,
        )

        # Verify automatically assigned organization.
        self.assertEqual(
            task.organization_id,
            self.alpha.id,
        )

        # Verify selected project.
        self.assertEqual(
            task.project_id,
            self.alpha_project.id,
        )

    # =========================================
    # TEST 7 — TASK VALIDATION
    # =========================================

    def test_short_title_is_rejected(self):

        self.client.force_authenticate(user=self.editor)

        response = self.client.post(
            "/api/v1/tasks/",
            {
                "title": "AB",
                "description": "Testing validation",
                "completed": False,
                "project": self.alpha_project.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
            response.data,
        )

        self.assertEqual(
            response.data["error"]["code"],
            "validation_error",
        )

    # =========================================
    # TEST 8 — IDEMPOTENCY
    # =========================================

    def test_idempotency_prevents_duplicate_task(self):

        self.client.force_authenticate(user=self.editor)

        payload = {
            "title": "Idempotency Test",
            "description": "Retry should not duplicate",
            "completed": False,
            "project": self.alpha_project.id,
        }

        # First request with a unique key.
        first = self.client.post(
            "/api/v1/tasks/",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="week3-test-key-001",
        )

        # Repeat the exact request with the same key.
        second = self.client.post(
            "/api/v1/tasks/",
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="week3-test-key-001",
        )

        self.assertEqual(
            first.status_code,
            201,
            first.data,
        )

        self.assertEqual(
            second.status_code,
            201,
            second.data,
        )

        self.assertIn(
            "id",
            first.data,
        )

        self.assertIn(
            "id",
            second.data,
        )

        # Both responses must reference the same task.
        self.assertEqual(
            first.data["id"],
            second.data["id"],
        )

        # Only one database record must exist.
        self.assertEqual(
            Task.objects.filter(
                title="Idempotency Test",
                owner=self.editor,
            ).count(),
            1,
        )

        # The second response must be a replay.
        self.assertEqual(
            second.headers.get("Idempotency-Replayed"),
            "true",
        )

    # =========================================
    # TEST 9 — CROSS-TENANT PROJECT ASSIGNMENT
    # =========================================

    def test_editor_cannot_assign_beta_project(self):

        self.client.force_authenticate(user=self.editor)

        response = self.client.post(
            "/api/v1/tasks/",
            {
                "title": "Cross Tenant Attempt",
                "description": "Should be rejected",
                "completed": False,
                "project": self.beta_project.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
            response.data,
        )

        # No task should have been created.
        self.assertFalse(Task.objects.filter(title="Cross Tenant Attempt").exists())

    # =========================================
    # TEST 10 — PROJECT TENANT ISOLATION
    # =========================================

    def test_manager_cannot_read_beta_project(self):

        self.client.force_authenticate(user=self.manager)

        response = self.client.get(f"/api/v1/projects/{self.beta_project.id}/")

        self.assertEqual(
            response.status_code,
            404,
            response.data,
        )

    # =========================================
    # TEST 11 — PROJECT CREATION
    # =========================================

    def test_editor_can_create_alpha_project(self):

        self.client.force_authenticate(user=self.editor)

        response = self.client.post(
            "/api/v1/projects/",
            {
                "name": "New Alpha Project",
                "description": "Created during API testing",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
            response.data,
        )

        self.assertIn(
            "id",
            response.data,
        )

        project = Project.objects.get(id=response.data["id"])

        # Organization must be Alpha.
        self.assertEqual(
            project.organization_id,
            self.alpha.id,
        )

        # Creator must be the authenticated Editor.
        self.assertEqual(
            project.created_by_id,
            self.editor.id,
        )

    # =========================================
    # TEST 12 — CROSS-TENANT PROJECT UPDATE
    # =========================================

    def test_editor_cannot_move_task_to_beta_project(self):

        self.client.force_authenticate(user=self.editor)

        response = self.client.patch(
            f"/api/v1/tasks/{self.editor_task.id}/",
            {
                "project": self.beta_project.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
            response.data,
        )

        # Reload task data from PostgreSQL.
        self.editor_task.refresh_from_db()

        # The task must remain in Alpha's project.
        self.assertEqual(
            self.editor_task.project_id,
            self.alpha_project.id,
        )

    # =========================================
    # TEST 13 — MANAGER PROJECT PERMISSION
    # =========================================

    def test_manager_can_update_alpha_project(self):

        self.client.force_authenticate(user=self.manager)

        response = self.client.patch(
            f"/api/v1/projects/{self.alpha_project.id}/",
            {
                "name": "Updated Alpha Project",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
            response.data,
        )

        # Reload project data from PostgreSQL.
        self.alpha_project.refresh_from_db()

        self.assertEqual(
            self.alpha_project.name,
            "Updated Alpha Project",
        )
