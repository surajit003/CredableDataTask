from datetime import datetime

import polars as pl
import psycopg2
import structlog
from decouple import config

logger = structlog.get_logger()

# PostgreSQL Connection Config
DATABASE_CONFIG = {
    "NAME": config("DB_NAME", default="creadable_db"),
    "USER": config("DB_USER", default="postgres"),
    "PASSWORD": config("DB_PASSWORD", default="mom12345"),
    "HOST": config("DB_HOST", default="localhost"),
    "PORT": config("DB_PORT", default="5432"),
}


def get_db_connection():
    """Establish connection to PostgreSQL"""
    return psycopg2.connect(
        dbname=DATABASE_CONFIG["NAME"],
        user=DATABASE_CONFIG["USER"],
        password=DATABASE_CONFIG["PASSWORD"],
        host=DATABASE_CONFIG["HOST"],
        port=DATABASE_CONFIG["PORT"],
    )


class DataLoader:
    def load_to_db(self, df: pl.DataFrame | None):
        if df is None or df.is_empty():
            logger.warning("no_data_to_insert")
            return

        # Convert to list of tuples for DB insert
        try:
            values = [
                (
                    int(row["index"]),
                    row["customer_id"],
                    row["first_name"],
                    row["last_name"],
                    row["company"],
                    row["city"],
                    row["country"],
                    row.get("phone_1"),
                    row.get("phone_2"),
                    row["email"],
                    row["subscription_date"],
                    row.get("website"),
                    row.get("source_file", "unknown.csv"),
                    datetime.fromisoformat(row["ingested_at"]),
                )
                for row in df.to_dicts()
            ]
        except Exception as e:
            logger.error("dataframe_row_parse_failed", error=str(e))
            return

        # Perform DB insert
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.executemany(
                """
                INSERT INTO customer (
                    index, customer_id, first_name, last_name, company, city, country,
                    phone_1, phone_2, email, subscription_date, website, source_file, ingested_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (index) DO NOTHING;
            """,
                values,
            )

            conn.commit()
            cursor.close()
            conn.close()

            logger.info("records_loaded_to_db", count=len(values))

        except Exception as e:
            logger.error("sql_bulk_insert_failed", error=str(e))
