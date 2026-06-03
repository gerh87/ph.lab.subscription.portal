from functools import cached_property
from typing import BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings


class StorageConfigError(RuntimeError):
    pass


class S3Storage:
    def _required(self, value: str | None, name: str) -> str:
        if not value:
            raise StorageConfigError(f"{name} is not configured")
        return value

    @cached_property
    def bucket(self) -> str:
        return self._required(settings.S3_BUCKET, "S3_BUCKET")

    @cached_property
    def client(self):
        endpoint_url = self._required(settings.S3_ENDPOINT, "S3_ENDPOINT")
        access_key = self._required(settings.S3_ACCESS_KEY, "S3_ACCESS_KEY")
        secret_key = self._required(settings.S3_SECRET_KEY, "S3_SECRET_KEY")

        return boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=settings.S3_REGION,
            use_ssl=settings.S3_USE_SSL,
            config=Config(signature_version="s3v4"),
        )

    def bucket_exists(self) -> bool:
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return True
        except ClientError as exc:
            code = exc.response.get("Error", {}).get("Code")
            if code in {"404", "NoSuchBucket"}:
                return False
            raise

    def upload_fileobj(self, fileobj: BinaryIO, key: str, content_type: str | None = None):
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        if extra_args:
            self.client.upload_fileobj(fileobj, self.bucket, key, ExtraArgs=extra_args)
        else:
            self.client.upload_fileobj(fileobj, self.bucket, key)

    def get_object(self, key: str):
        return self.client.get_object(Bucket=self.bucket, Key=key)

    def delete_object(self, key: str):
        self.client.delete_object(Bucket=self.bucket, Key=key)


storage_client = S3Storage()
