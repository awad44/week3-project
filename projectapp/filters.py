from django_filters import rest_framework as filters

from .models import Project


class ProjectFilter(filters.FilterSet):
    name_contains = filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
    )
    created_after = filters.IsoDateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
    )
    created_before = filters.IsoDateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
    )

    class Meta:
        model = Project
        fields = []
