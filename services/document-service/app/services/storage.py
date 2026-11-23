
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings


from io import BytesIO



s3_client = boto3.client(
    "s3",
    endpoint_url=settings.s3_endpoint_url,
    aws_access_key_id=settings.s3_access_key,
    aws_secret_access_key=settings.s3_secret_key,
    region_name=settings.s3_region,
    config=Config(
        signature_version="s3v4",
        s3={"addressing_style": "path"},
    ),
)


def ensure_bucket_exists() -> None:
    bucket = settings.s3_bucket

    try:
        s3_client.head_bucket(Bucket=bucket)
        print(f"Bucket '{bucket}' already exists.")

    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")

        if error_code in ("404", "NoSuchBucket", "NotFound"):
            s3_client.create_bucket(Bucket=bucket)
            print(f"Bucket '{bucket}' created successfully.")
        else:
            raise

def upload_file(file_path: str, object_key: str) -> None:
    s3_client.upload_file(
        file_path,
        settings.s3_bucket,
        object_key,
    )

def download_file(object_key: str, destination_path: str) -> None:
    s3_client.download_file(
        settings.s3_bucket,
        object_key,
        destination_path,
    )


def upload_bytes(content: bytes, object_key: str, content_type: str) -> None:
    s3_client.upload_fileobj(
        BytesIO(content),
        settings.s3_bucket,
        object_key,
        ExtraArgs={"ContentType": content_type},
    )


def delete_object(object_key: str) -> None:
    s3_client.delete_object(
        Bucket=settings.s3_bucket,
        Key=object_key,
    )

def get_object(object_key: str) -> dict:
    return s3_client.get_object(
        Bucket=settings.s3_bucket,
        Key=object_key,
    )