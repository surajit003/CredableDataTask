import unittest
from datetime import datetime

import polars as pl

from scripts.etl.transform import DataTransformer


class TestDataTransformer(unittest.TestCase):
    def setUp(self):
        self.transformer = DataTransformer()

    def test_transform_basic_cleaning(self):
        df = pl.DataFrame(
            {
                " Customer Id ": ["  ABC123  ", " XYZ456 "],
                "First Name": [" Alice ", "Bob"],
                "Subscription Date": ["2023-12-01", "2023-12-02"],
                "index": ["1", "2"],
            }
        )

        result = self.transformer.transform(df, source_file="test.csv")

        # Check column names normalized
        expected_columns = {"customer_id", "first_name", "subscription_date", "index", "source_file", "ingested_at"}
        self.assertTrue(expected_columns.issubset(set(result.columns)))

        # Check string trimming
        self.assertIn("ABC123", result["customer_id"].to_list())
        self.assertIn("Alice", result["first_name"].to_list())

        # Check datetime parsing
        self.assertTrue(all(isinstance(val, datetime) for val in result["subscription_date"]))

        # Check metadata columns
        self.assertTrue(all(val == "test.csv" for val in result["source_file"]))
        self.assertTrue(all(isinstance(val, str) for val in result["ingested_at"]))

    def test_flatten(self):
        nested = {"id": 1, "user": {"name": "Alice", "contact": {"email": "alice@example.com", "phone": "123456789"}}}

        flattened = self.transformer.flatten(nested)
        expected_keys = {"id", "user_name", "user_contact_email", "user_contact_phone"}

        self.assertSetEqual(set(flattened.keys()), expected_keys)
        self.assertEqual(flattened["user_name"], "Alice")
        self.assertEqual(flattened["user_contact_email"], "alice@example.com")


if __name__ == "__main__":
    import unittest

    unittest.main()
