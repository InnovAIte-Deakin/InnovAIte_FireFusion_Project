import boto3
from src.utils.config import S3_CONFIG

BUCKET = S3_CONFIG["S3_BUCKET_NAME"]

s3 = boto3.client(
    "s3",
    region_name=S3_CONFIG["AWS_DEFAULT_REGION"],
    aws_access_key_id=S3_CONFIG["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=S3_CONFIG["AWS_SECRET_ACCESS_KEY"]
)


def upload_file(local_path, s3_key):
    """Upload a local file to S3"""
    try:
        s3.upload_file(local_path, BUCKET, s3_key)
        print(f"Uploaded {local_path} to s3://{BUCKET}/{s3_key}")
    except Exception as e:
        print("Upload failed:", e)


def download_file(s3_key, local_path):
    """Download a file from S3"""
    try:
        s3.download_file(BUCKET, s3_key, local_path)
        print(f"Downloaded {s3_key} to {local_path}")
    except Exception as e:
        print("Download failed:", e)


def list_files(prefix=""):
    """List files in S3 bucket"""
    try:
        response = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
        files = response.get("Contents", [])

        if not files:
            print("Bucket is empty")
            return

        for obj in files:
            print(obj["Key"])

    except Exception as e:
        print("Error connecting to S3:", e)


if __name__ == "__main__":
    print("Testing S3 connection...")
    list_files()
    print("Connection test completed.")