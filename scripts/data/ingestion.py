import argparse
import csv
import json
import logging
import os
from pathlib import Path

import paramiko
import structlog
from decouple import config
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential

# Setup structlog
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
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


class AlertHandler:
    @staticmethod
    def alert(event: str, **kwargs):
        logger.error(event, **kwargs)
        # Extend this for Slack, Email, Sentry, etc.


class SFTPClientManager:
    def __init__(self, host: str, port: int, username: str, password: str, remote_folder=".", alert_handler=None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.remote_folder = remote_folder
        self.client: paramiko.SFTPClient | None = None
        self.alert_handler = alert_handler or AlertHandler()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2), reraise=True)
    def connect(self):
        transport = paramiko.Transport((self.host, self.port))
        transport.connect(username=self.username, password=self.password)
        self.client = paramiko.SFTPClient.from_transport(transport)
        logger.info("sftp_connected", host=self.host)

    def disconnect(self):
        if self.client:
            self.client.close()
            logger.info("sftp_disconnected")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2), reraise=True)
    def list_files(self) -> list[str]:
        return self.client.listdir(self.remote_folder)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2), reraise=True)
    def download_file(self, remote_file: str, local_path: str):
        self.client.get(f"{self.remote_folder}/{remote_file}", local_path)
        logger.info("file_downloaded", remote_file=remote_file, local_path=local_path)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2), reraise=True)
    def upload_file(self, local_file: str, remote_file: str = None):
        remote_file = remote_file or os.path.basename(local_file)
        self.client.put(local_file, f"{self.remote_folder}/{remote_file}")
        logger.info("file_uploaded", local_file=local_file, remote_file=remote_file)


class DataIngestor:
    def __init__(self, download_dir=DOWNLOAD_DIR, alert_handler=None):
        self.download_dir = download_dir
        self.alert_handler = alert_handler or AlertHandler()

    def parse_csv(self, file_path: Path):
        try:
            with open(file_path, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
                logger.info("csv_parsed", file=file_path.name, rows=len(rows))
        except Exception as e:
            self.alert_handler.alert("csv_parse_error", file=file_path.name, error=str(e))

    def parse_json(self, file_path: Path):
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
                logger.info("json_parsed", file=file_path.name, records=len(data))
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
