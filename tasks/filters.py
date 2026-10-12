from django_filters import rest_framework as filters

from .models import Task


class TaskFilter(filters.FilterSet):
    # text filter
    title_contains = filters.CharFilter(field_name="title", lookup_expr="icontains")

    created_after = filters.IsoDateTimeFilter(
        field_name="created_at", lookup_expr="gte"
    )

    created_before = filters.IsoDateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = Task
        fields = ["completed"]
        # model = Task — This FilterSet works with Task records.
        # fields = ["completed"] — Automatically adds a filter for completed.
