from datetime import date, datetime

import pytz
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from app.models import Customer


class CustomerListViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("customer-list-view")

        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.token = Token.objects.create(user=self.user)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.customer1 = Customer.objects.create(
            index=1,
            customer_id="CUST001",
            first_name="Alice",
            last_name="Smith",
            company="Alpha Corp",
            city="Berlin",
            country="Germany",
            phone_1="123456789",
            phone_2="987654321",
            email="alice@example.com",
            subscription_date=date(2024, 5, 1),
            website="https://alice.com",
            source_file="customers.csv",
            ingested_at=datetime(2025, 3, 21, tzinfo=pytz.UTC),
        )

        self.customer2 = Customer.objects.create(
            index=2,
            customer_id="CUST002",
            first_name="Bob",
            last_name="Johnson",
            company="Beta Inc",
            city="Munich",
            country="Germany",
            phone_1="223456789",
            phone_2="887654321",
            email="bob@example.com",
            subscription_date=date(2024, 6, 15),
            website="https://bob.com",
            source_file="customers.csv",
            ingested_at=datetime(2025, 3, 22, tzinfo=pytz.UTC),
        )

    def test_get_all_customers(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_filter_by_city(self):
        response = self.client.get(f"{self.url}?city=Berlin")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["first_name"], "Alice")

    def test_search_by_first_name(self):
        response = self.client.get(f"{self.url}?search=Bob")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["email"], "bob@example.com")

    def test_ordering_by_subscription_date(self):
        response = self.client.get(f"{self.url}?ordering=subscription_date")
        self.assertEqual(response.status_code, 200)
        results = response.data["results"]
        self.assertLess(results[0]["subscription_date"], results[1]["subscription_date"])

    def test_filter_by_date_range(self):
        response = self.client.get(f"{self.url}?start_date=2025-03-22")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["first_name"], "Bob")
