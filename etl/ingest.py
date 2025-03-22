import argparse
import json
import logging
import os
from pathlib import Path

import polars as pl
import structlog
from alerts import AlertHandler
from decouple import config
from load import DataLoader
from sftp_client import SFTPClientManager
from tenacity import RetryError
from transform import DataTransformer

logging.basicConfig(format="%(message)s", level=logging.INFO, handlers=[logging.StreamHandler()])

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)

logger = structlog.get_logger()

LOG_DIR = "logs"  # We could move this to .env. Keeping it here for simplicity
DOWNLOAD_DIR = "downloads"  # We could move this to .env. Keeping it here for simplicity
TRANSFORMED_DIR = "transformed"  # We could move this to .env. Keeping it here for simplicity

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(TRANSFORMED_DIR, exist_ok=True)


class DataIngestor:
    def __init__(self, download_dir=DOWNLOAD_DIR, transformed_dir=TRANSFORMED_DIR, alert_handler=None):
        self.download_dir = download_dir
        self.transformed_dir = transformed_dir
        self.alert_handler = alert_handler or AlertHandler()
        self.transformer = DataTransformer()
        self.loader = DataLoader()

    def _save_cleaned(self, base_filename: str, df: pl.DataFrame, original_extension: str):
        try:
            output_path = os.path.join(self.transformed_dir, f"{base_filename}_transformed{original_extension}")

            if original_extension.lower() == ".json":
                df.write_json(output_path)
            elif original_extension.lower() == ".csv":
                df.write_csv(output_path)
            else:
                self.alert_handler.alert("unsupported_output_format", format=original_extension)
                return

            logger.info("cleaned_file_saved", output_file=output_path, records=df.shape[0])
            self.loader.load_to_db(df)

        except Exception as e:
            self.alert_handler.alert("transformed_file_save_failed", file=base_filename, error=str(e))

    def parse_csv(self, file_path: Path):
        try:
            df = pl.read_csv(file_path)
            logger.info("csv_parsed", file=file_path.name, rows=df.shape[0])

            cleaned_df = self.transformer.transform(df, source_file=file_path.name)
            self._save_cleaned(file_path.stem, cleaned_df, original_extension=".csv")

        except Exception as e:
            self.alert_handler.alert("csv_parse_error", file=file_path.name, error=str(e))

    def parse_json(self, file_path: Path):
        try:
            with open(file_path, encoding="utf-8") as f:
                records = json.load(f)

            flattened = [self.transformer.flatten(r) for r in records]

            df = pl.DataFrame(flattened)
            logger.info("json_parsed", file=file_path.name, records=df.shape[0])

            cleaned_df = self.transformer.transform(df, source_file=file_path.name)
            self._save_cleaned(file_path.stem, cleaned_df, original_extension=".json")

        except Exception as e:
            self.alert_handler.alert("json_parse_error", file=file_path.name, error=str(e))

    def process_downloaded_files(self):
        for file_path in Path(self.download_dir).glob("*"):
            if file_path.suffix.lower() == ".csv":
                self.parse_csv(file_path)
            elif file_path.suffix.lower() == ".json":
                self.parse_json(file_path)
            else:
                logger.warning("unsupported_file_skipped", file=file_path.name)


class IngestionPipeline:
    def __init__(self, sftp_config: dict, alert_handler=None):
        self.alert_handler = alert_handler or AlertHandler()
        self.sftp_manager = SFTPClientManager(alert_handler=self.alert_handler, **sftp_config)
        self.data_ingestor = DataIngestor(alert_handler=self.alert_handler)

    def run(self, filename: str | None = None):
        try:
            logger.info("ingestion_started", filter=filename)
            self.sftp_manager.connect()

            files = [filename] if filename else self.sftp_manager.list_files()
            for file in files:
                local_path = os.path.join(self.data_ingestor.download_dir, file)
                self.sftp_manager.download_file(file, local_path)

            self.sftp_manager.disconnect()
            self.data_ingestor.process_downloaded_files()
            logger.info("ingestion_completed")

        except RetryError as retry_err:
            self.alert_handler.alert("retry_failed", error=str(retry_err))
        except Exception as e:
            self.alert_handler.alert("pipeline_failed", error=str(e))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SFTP ingestion pipeline")
    parser.add_argument("--filename", help="Name of the file to download from SFTP", required=False)

    args = parser.parse_args()
    host = config("SFTP_HOST")
    port = config("SFTP_PORT", cast=int, default=22)
    username = config("SFTP_USERNAME")
    password = config("SFTP_PASSWORD")
    remote_folder = config("REMOTE_FOLDER")

    SFTP_CONFIG = {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "remote_folder": remote_folder,
    }

    pipeline = IngestionPipeline(SFTP_CONFIG)
    pipeline.run(filename=args.filename)
