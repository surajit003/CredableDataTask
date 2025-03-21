import argparse
import logging
import os

import paramiko
import structlog
from decouple import config

# Set up structlog
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

# Load from .env using decouple
host = config("SFTP_HOST")
port = config("SFTP_PORT", cast=int, default=22)
username = config("SFTP_USERNAME")
password = config("SFTP_PASSWORD")

# Parse CLI arguments
parser = argparse.ArgumentParser(description="Upload a file to SFTP")
parser.add_argument("file", help="Path to the local file to upload")
args = parser.parse_args()

local_file = args.file
remote_path = f"/{os.path.basename(local_file)}"

try:
    transport = paramiko.Transport((host, port))
    transport.connect(username=username, password=password)

    sftp = paramiko.SFTPClient.from_transport(transport)
    logger.info("sftp_connected", host=host, port=port)

    sftp.put(local_file, remote_path)
    logger.info("file_uploaded", local_file=local_file, remote_path=remote_path)

    sftp.close()
    transport.close()
    logger.info("sftp_connection_closed")

except Exception as e:
    logger.error("sftp_upload_failed", error=str(e), file=local_file)
