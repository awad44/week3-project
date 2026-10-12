from django.urls import path

from .views import ProjectViewSet, TaskViewSet

urlpatterns = [
    # ========================
    # TASK ENDPOINTS
    # ========================
    path(
        "tasks/",
        TaskViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="task-list",
    ),
    path(
        "tasks/<int:pk>/",
        TaskViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="task-detail",
    ),
    # ========================
    # PROJECT ENDPOINTS
    # ========================
    path(
        "projects/",
        ProjectViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="project-list",
    ),
    path(
        "projects/<int:pk>/",
        ProjectViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="project-detail",
    ),
]
