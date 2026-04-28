import boto3
import os
from dotenv import load_dotenv

load_dotenv()

BUCKET = 'firefusion-training-data'
REGION = 'ap-southeast-2'

s3 = boto3.client(
    's3',
    region_name=REGION,
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

def upload_file(local_path, s3_key):
    """Upload a local file to S3"""
    s3.upload_file(local_path, BUCKET, s3_key)
    print(f"Uploaded {local_path} to s3://{BUCKET}/{s3_key}")

def download_file(s3_key, local_path):
    """Download a file from S3"""
    s3.download_file(BUCKET, s3_key, local_path)
    print(f"Downloaded {s3_key} to {local_path}")

def list_files(prefix=''):
    """List all files in bucket"""
    response = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)
    files = response.get('Contents', [])
    if not files:
        print("Bucket is empty")
        return
    for obj in files:
        print(obj['Key'])

if __name__ == '__main__':
    print("Testing S3 connection...")
    list_files()
    print("Connection successful!")