from django.contrib import admin

from .models import Organization, OrganizationMembership, Project, Task


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "organization")
    list_filter = ("organization",)
    search_fields = ("user__username", "organization__name")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "organization", "created_by")
    list_filter = ("organization",)
    search_fields = ("name",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "completed",
        "owner",
        "project",
        "organization",
    )
    list_filter = ("completed", "organization")
    search_fields = ("title",)
