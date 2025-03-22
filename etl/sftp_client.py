import paramiko
import structlog
from alerts import AlertHandler
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()


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
