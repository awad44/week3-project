from rest_framework.pagination import (
    CursorPagination,
    LimitOffsetPagination,
    PageNumberPagination,
)


# 1. Page Number Pagination
class TaskPageNumberPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 20


# 2. Limit Offset Pagination
class TaskLimitOffsetPagination(LimitOffsetPagination):
    default_limit = 5
    max_limit = 20


# 3. Cursor Pagination
class TaskCursorPagination(CursorPagination):
    page_size = 5
    ordering = "-id"
