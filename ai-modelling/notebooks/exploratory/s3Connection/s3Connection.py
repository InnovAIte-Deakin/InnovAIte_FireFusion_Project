import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import os

# --- Configuration ---
AWS_REGION = "us-east-1"
BUCKET_NAME = "your-bucket-name"


def get_s3_client():
    """
    Create and return an S3 client.
    Credentials are loaded from environment variables, ~/.aws/credentials,
    or IAM role (if running on EC2/Lambda).
    """
    return boto3.client("s3", region_name=AWS_REGION)


# --- Core Operations ---

def list_buckets(s3_client):
    """List all S3 buckets in the account."""
    response = s3_client.list_buckets()
    buckets = [b["Name"] for b in response.get("Buckets", [])]
    print(f"Buckets: {buckets}")
    return buckets


def list_objects(s3_client, bucket_name, prefix=""):
    """List objects in a bucket, optionally filtered by prefix."""
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    objects = [obj["Key"] for obj in response.get("Contents", [])]
    print(f"Objects in '{bucket_name}': {objects}")
    return objects


def upload_file(s3_client, local_path, bucket_name, s3_key=None):
    """Upload a local file to S3."""
    s3_key = s3_key or os.path.basename(local_path)
    s3_client.upload_file(local_path, bucket_name, s3_key)
    print(f"Uploaded '{local_path}' → s3://{bucket_name}/{s3_key}")


def download_file(s3_client, bucket_name, s3_key, local_path=None):
    """Download a file from S3 to a local path."""
    local_path = local_path or os.path.basename(s3_key)
    s3_client.download_file(bucket_name, s3_key, local_path)
    print(f"Downloaded s3://{bucket_name}/{s3_key} → '{local_path}'")


def upload_string(s3_client, content, bucket_name, s3_key):
    """Upload a string/bytes directly to S3 (no local file needed)."""
    s3_client.put_object(Bucket=bucket_name, Key=s3_key, Body=content)
    print(f"Uploaded content → s3://{bucket_name}/{s3_key}")


def read_object(s3_client, bucket_name, s3_key):
    """Read an S3 object's content directly into memory."""
    response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
    content = response["Body"].read().decode("utf-8")
    print(f"Read {len(content)} chars from s3://{bucket_name}/{s3_key}")
    return content


def delete_object(s3_client, bucket_name, s3_key):
    """Delete an object from S3."""
    s3_client.delete_object(Bucket=bucket_name, Key=s3_key)
    print(f"Deleted s3://{bucket_name}/{s3_key}")


def generate_presigned_url(s3_client, bucket_name, s3_key, expiry_seconds=3600):
    """Generate a pre-signed URL for temporary public access to an object."""
    url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": s3_key},
        ExpiresIn=expiry_seconds,
    )
    print(f"Pre-signed URL (expires in {expiry_seconds}s): {url}")
    return url


# --- Main ---

if __name__ == "__main__":
    try:
        s3 = get_s3_client()

        # List all buckets
        list_buckets(s3)

        # List objects in a specific bucket
        list_objects(s3, BUCKET_NAME)

        # Upload a file
        # upload_file(s3, "local_file.txt", BUCKET_NAME, "folder/remote_file.txt")

        # Upload a string directly
        upload_string(s3, "Hello from Python!", BUCKET_NAME, "hello.txt")

        # Read it back
        content = read_object(s3, BUCKET_NAME, "hello.txt")
        print(f"Content: {content}")

        # Generate a pre-signed URL
        generate_presigned_url(s3, BUCKET_NAME, "hello.txt")

        # Clean up
        delete_object(s3, BUCKET_NAME, "hello.txt")

    except NoCredentialsError:
        print("Error: AWS credentials not found.")
        print("Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env vars, or configure ~/.aws/credentials")
    except ClientError as e:
        print(f"AWS error: {e.response['Error']['Message']}")