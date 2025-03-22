from django.db import models


class Customer(models.Model):

    class Meta:
        db_table = "customer"
        ordering = ["-ingested_at"]

    index = models.IntegerField(primary_key=True)
    customer_id = models.CharField(max_length=64, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)

    phone_1 = models.CharField(max_length=50, blank=True, null=True)
    phone_2 = models.CharField(max_length=50, blank=True, null=True)

    email = models.EmailField(max_length=255)
    subscription_date = models.DateField()

    website = models.URLField(max_length=255, blank=True, null=True)

    source_file = models.CharField(max_length=255)
    ingested_at = models.DateTimeField()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.customer_id})"
