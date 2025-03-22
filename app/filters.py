import django_filters

from app.models import Customer


class CustomerFilter(django_filters.FilterSet):

    class Meta:
        model = Customer
        fields = ["start_date", "end_date", "city", "country"]

    start_date = django_filters.DateFilter(field_name="ingested_at", lookup_expr="gte")
    end_date = django_filters.DateFilter(field_name="ingested_at", lookup_expr="lte")
    city = django_filters.CharFilter(lookup_expr="icontains")
    country = django_filters.CharFilter(lookup_expr="icontains")
