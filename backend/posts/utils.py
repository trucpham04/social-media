import os
import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile, UploadedFile
import uuid
from datetime import datetime


def get_s3_client():
    """Initialize and return S3 client"""
    return boto3.client(
        "s3",
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        region_name=os.environ.get("AWS_DEFAULT_REGION"),
    )


def upload_file_to_s3(file: UploadedFile, folder: str = "posts") -> str:
    """
    Upload a file to S3 and return the URL
    
    Args:
        file: The file to upload (UploadedFile or InMemoryUploadedFile)
        folder: The folder in S3 bucket (default: 'posts')
    
    Returns:
        str: The S3 URL of the uploaded file
    
    Raises:
        ClientError: If upload fails
    """
    s3_client = get_s3_client()
    bucket_name = os.environ.get("AWS_S3_BUCKET_NAME")

    if not bucket_name:
        raise ValueError("AWS_S3_BUCKET_NAME is not set in environment variables")

    # Generate unique filename
    file_extension = os.path.splitext(file.name)[1] if file.name else ""
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    s3_key = f"{folder}/{datetime.now().strftime('%Y/%m/%d')}/{unique_filename}"

    # Get content type
    content_type = getattr(file, "content_type", None)
    if not content_type:
        # Try to guess from extension
        if file_extension.lower() in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            content_type = "image/jpeg"
        elif file_extension.lower() in [".mp4", ".avi", ".mov", ".webm"]:
            content_type = "video/mp4"
        else:
            content_type = "application/octet-stream"

    try:
        # Reset file pointer to beginning
        if hasattr(file, "seek"):
            file.seek(0)
        
        # Upload file
        extra_args = {"ContentType": content_type}
        s3_client.upload_fileobj(
            file,
            bucket_name,
            s3_key,
            ExtraArgs=extra_args,
        )

        # Generate URL
        region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"

        return url
    except ClientError as e:
        raise Exception(f"Failed to upload file to S3: {str(e)}")


def delete_file_from_s3(url: str) -> bool:
    """
    Delete a file from S3 given its URL
    
    Args:
        url: The S3 URL of the file to delete
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        s3_client = get_s3_client()
        bucket_name = os.environ.get("AWS_S3_BUCKET_NAME")

        if not bucket_name:
            return False

        # Extract key from URL
        # Format: https://bucket-name.s3.region.amazonaws.com/key
        # Or: https://bucket-name.s3.amazonaws.com/key
        # Or: https://s3.region.amazonaws.com/bucket-name/key
        if ".amazonaws.com/" in url:
            # Extract everything after .amazonaws.com/
            parts = url.split(".amazonaws.com/")
            if len(parts) > 1:
                s3_key = parts[1]
            else:
                return False
        elif bucket_name in url:
            # Try to extract key after bucket name
            parts = url.split(f"{bucket_name}/")
            if len(parts) > 1:
                s3_key = parts[1]
            else:
                return False
        else:
            return False

        s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
        return True
    except Exception as e:
        print(f"Error deleting file from S3: {str(e)}")
        return False
