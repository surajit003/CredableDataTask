from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "index",
        "customer_id",
        "first_name",
        "last_name",
        "email",
        "company",
        "city",
        "country",
        "subscription_date",
    )
    search_fields = ("first_name", "last_name", "email", "company", "customer_id")
    list_filter = ("country", "subscription_date", "ingested_at")
    readonly_fields = ("ingested_at", "source_file")
    ordering = ("-ingested_at",)
