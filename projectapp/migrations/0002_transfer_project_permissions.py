from django.db import migrations

PROJECT_PERMISSIONS = [
    "view_project",
    "add_project",
    "change_project",
    "delete_project",
]


def copy_project_permissions(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Permission = apps.get_model("auth", "Permission")
    Group = apps.get_model("auth", "Group")

    old_type = ContentType.objects.filter(
        app_label="tasks",
        model="project",
    ).first()

    if old_type is None:
        return

    new_type, _ = ContentType.objects.get_or_create(
        app_label="projectapp",
        model="project",
    )

    for codename in PROJECT_PERMISSIONS:
        old_permission = Permission.objects.filter(
            content_type=old_type,
            codename=codename,
        ).first()

        if old_permission is None:
            continue

        new_permission, _ = Permission.objects.get_or_create(
            content_type=new_type,
            codename=codename,
            defaults={"name": old_permission.name},
        )

        for group in Group.objects.filter(permissions=old_permission):
            group.permissions.add(new_permission)


class Migration(migrations.Migration):
    dependencies = [
        ("projectapp", "0001_initial"),
        ("tasks", "0009_alter_task_project_delete_project"),
    ]

    operations = [
        migrations.RunPython(
            copy_project_permissions,
            migrations.RunPython.noop,
        ),
    ]
