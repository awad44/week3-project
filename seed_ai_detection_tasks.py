from django.db import transaction

from projectapp.models import Project
from tasks.models import OrganizationMembership, Task

project = Project.objects.select_related("organization", "created_by").get(
    name="AI-Cheating Detection",
    organization__name="Beta",
)
owner = project.created_by

if not OrganizationMembership.objects.filter(
    user=owner,
    organization=project.organization,
).exists():
    raise ValueError(
        f"{owner.username} must have a membership in "
        f"{project.organization.name} before creating tasks."
    )

task_data = [
    (
        "Define project goals",
        "Set the detector's scope and define how its results will be evaluated.",
    ),
    (
        "Document privacy requirements",
        "Record how submitted text will be collected, stored, and protected.",
    ),
    (
        "Collect permitted human-written samples",
        "Gather examples with permission and record their source.",
    ),
    (
        "Collect permitted AI-generated samples",
        "Gather generated examples and record the model and source.",
    ),
    (
        "Label the sample data",
        "Label each example and document the reason for its label.",
    ),
    (
        "Prepare training and test data",
        "Split data by source to reduce overlap between training and testing.",
    ),
    (
        "Build text preprocessing",
        "Prepare a repeatable process for cleaning and normalizing text.",
    ),
    (
        "Create a baseline classifier",
        "Train a simple TF-IDF and logistic regression model for comparison.",
    ),
    (
        "Evaluate a transformer model",
        "Train or evaluate a transformer model using the prepared data.",
    ),
    (
        "Measure model performance",
        "Calculate precision, recall, F1 score, and a confusion matrix.",
    ),
    (
        "Review false positives",
        "Check how often human-written work is incorrectly flagged.",
    ),
    (
        "Set confidence thresholds",
        "Choose thresholds that send uncertain results for human review.",
    ),
    (
        "Build the prediction endpoint",
        "Create an endpoint that accepts text and returns a model result.",
    ),
    (
        "Add result explanations",
        "Show confidence and explain that results need human review.",
    ),
    (
        "Write limitations and tests",
        "Document known limitations and add tests for important edge cases.",
    ),
]

created_count = 0
existing_count = 0

with transaction.atomic():
    for number, (title, description) in enumerate(task_data, start=1):
        _, created = Task.objects.get_or_create(
            project=project,
            title=f"AI Detection {number:02d}: {title}",
            defaults={
                "description": description,
                "completed": False,
                "organization": project.organization,
                "owner": owner,
            },
        )

        if created:
            created_count += 1
        else:
            existing_count += 1

print(f"Project: {project.name} ({project.organization.name})")
print(f"Owner: {owner.username}")
print(f"Created: {created_count}; already existed: {existing_count}")
print(f"Total tasks for this project: {Task.objects.filter(project=project).count()}")
