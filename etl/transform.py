import datetime

import polars as pl


class DataTransformer:

    @staticmethod
    def _normalize_key(key: str) -> str:
        return key.strip().lower().replace(" ", "_")

    def transform(self, df: pl.DataFrame, source_file: str) -> pl.DataFrame:
        # Normalize column names
        df = df.rename({col: self._normalize_key(col) for col in df.columns})

        # Trim string fields
        df = df.with_columns([pl.col(col).str.strip_chars() for col in df.columns if df[col].dtype == pl.Utf8])

        # Cast numeric-like columns (optional)
        numeric_candidates = ["index"]
        for col in numeric_candidates:
            if col in df.columns:
                df = df.with_columns([pl.col(col).cast(pl.Int64)])

        # Parse date columns
        datetime_candidates = ["subscription_date"]
        for col in datetime_candidates:
            if col in df.columns and df[col].dtype == pl.Utf8:
                df = df.with_columns([pl.col("subscription_date").str.strptime(pl.Datetime, format="%Y-%m-%d")])

        # Drop nulls
        df = df.drop_nulls()

        # Remove duplicates
        df = df.unique()

        # Add metadata
        df = df.with_columns(
            [
                pl.lit(source_file).alias("source_file"),
                pl.lit(datetime.datetime.utcnow().isoformat()).alias("ingested_at"),
            ]
        )

        return df

    @staticmethod
    def flatten(record: dict, parent_key: str = "", sep: str = "_") -> dict:
        """Recursively flattens nested dictionaries"""
        items = {}
        for k, v in record.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(DataTransformer.flatten(v, new_key, sep=sep))
            else:
                items[new_key] = v
        return items
