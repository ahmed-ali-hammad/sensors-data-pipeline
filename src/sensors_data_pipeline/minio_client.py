import logging

from minio import Minio

_logger = logging.getLogger(__name__)


class MinioManager:
    """
    A wrapper class to initialize and provide access to a MinIO client.
    """

    minio_client: Minio | None = None

    def __init__(
        self,
        minio_endpoint: str,
        minio_access_key: str,
        minio_secret_key: str,
        is_secure: bool,
    ) -> None:
        self.minio_endpoint = minio_endpoint
        self.minio_access_key = minio_access_key
        self.minio_secret_key = minio_secret_key
        self.is_secure = is_secure

    def get_minio_client(self) -> Minio:
        """
        Returns a singleton instance of the MinIO client.
        Initializes it if not already done.
        """
        if MinioManager.minio_client is None:
            _logger.info("Initializing new Minio client instance")

            MinioManager.minio_client = Minio(
                endpoint=self.minio_endpoint,
                access_key=self.minio_access_key,
                secret_key=self.minio_secret_key,
                secure=self.is_secure,
            )

            _logger.info("Minio client has been initialized..")
        return MinioManager.minio_client
