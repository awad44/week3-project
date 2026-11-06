from django.conf import settings
from django.db import models

from tasks.models import Organization


class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="projects",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tasks_project"

    def __str__(self):
        return self.name
