from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics

from app.filters import CustomerFilter
from app.models import Customer
from app.pagination import CustomerCursorPagination
from app.serializers import CustomerSerializer


class CustomerListView(generics.ListAPIView):
    queryset = Customer.objects.all()
    authentication_classes = []
    permission_classes = []
    serializer_class = CustomerSerializer
    pagination_class = CustomerCursorPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
        filters.SearchFilter,
    ]
    filterset_class = CustomerFilter
    ordering_fields = ["ingested_at", "subscription_date", "city", "first_name"]
    search_fields = ["first_name", "last_name", "email", "company", "city", "country"]
