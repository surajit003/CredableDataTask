# Generated by Django 5.1.7 on 2025-03-21 20:33

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("index", models.IntegerField(primary_key=True, serialize=False)),
                ("customer_id", models.CharField(max_length=64, unique=True)),
                ("first_name", models.CharField(max_length=100)),
                ("last_name", models.CharField(max_length=100)),
                ("company", models.CharField(max_length=255)),
                ("city", models.CharField(max_length=100)),
                ("country", models.CharField(max_length=100)),
                ("phone_1", models.CharField(blank=True, max_length=50, null=True)),
                ("phone_2", models.CharField(blank=True, max_length=50, null=True)),
                ("email", models.EmailField(max_length=255)),
                ("subscription_date", models.DateField()),
                ("website", models.URLField(blank=True, max_length=255, null=True)),
                ("source_file", models.CharField(max_length=255)),
                ("ingested_at", models.DateTimeField()),
            ],
            options={
                "db_table": "customer",
                "ordering": ["-ingested_at"],
            },
        ),
    ]
