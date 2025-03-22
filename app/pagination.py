from rest_framework.pagination import CursorPagination


class CustomerCursorPagination(CursorPagination):
    page_size = 20
    ordering = "-ingested_at"
