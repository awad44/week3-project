from django.conf import settings
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class OrganizationMembership(models.Model):
    # A user can have only one membership record
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_membership",
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="memberships",
    )

    def __str__(self):
        return f"{self.user.username} - {self.organization.name}"


class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="tasks",
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_tasks",
    )

    project = models.ForeignKey(
        "projectapp.Project",
        on_delete=models.PROTECT,
        related_name="tasks",
    )

    def __str__(self):
        return self.title


class Comment(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="task_comments",
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment on {self.task_id} by {self.author_id}"


class TaskCreateIdempotency(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
    )

    key = models.CharField(max_length=128)

    request_payload = models.JSONField()

    response_payload = models.JSONField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "organization", "key"],
                name="unique_task_create_idempotency",
            ),
        ]
