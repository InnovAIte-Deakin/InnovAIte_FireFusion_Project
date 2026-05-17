import os
from dotenv import load_dotenv

load_dotenv()

S3_CONFIG = {
    "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID", "RANDOM_ACCESS_KEY_12345"),
    "AWS_SECRET_ACCESS_KEY": os.getenv("AWS_SECRET_ACCESS_KEY", "RANDOM_SECRET_KEY_ABCDE"),
    "AWS_DEFAULT_REGION": os.getenv("AWS_DEFAULT_REGION", "ap-southeast-2"),
    "S3_BUCKET_NAME": os.getenv("S3_BUCKET_NAME", "firefusion-training-data")
}