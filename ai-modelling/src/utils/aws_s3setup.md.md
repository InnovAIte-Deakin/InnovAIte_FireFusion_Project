# 🔥 FireFusion AI Modelling

## 📦 AWS S3 Bucket Setup

  Field         Value
  ------------- ----------------------------
  Bucket Name   `firefusion-training-data`
  Region        `ap-southeast-2 (Sydney)`

------------------------------------------------------------------------

## 📁 Folder Structure

    firefusion-training-data/
    ├── raw/                # Raw input data
    ├── processed/          # Cleaned / transformed data
    ├── models/             # Saved ML models
    ├── splits/             # Train/validation/test splits
    │   ├── train/
    │   ├── val/
    │   └── test/
    └── logs/               # Training logs

------------------------------------------------------------------------

## ⚙️ Setup for Team Members

### 🔑 Step 1: Get AWS Credentials

DM Juveria Nishath on Microsoft Teams to get: - AWS_ACCESS_KEY_ID -
AWS_SECRET_ACCESS_KEY

⚠️ Never share keys in group chats or GitHub

------------------------------------------------------------------------

### 📄 Step 2: Create `.env` File

    AWS_ACCESS_KEY_ID=your_access_key
    AWS_SECRET_ACCESS_KEY=your_secret_key
    AWS_DEFAULT_REGION=ap-southeast-2
    S3_BUCKET_NAME=firefusion-training-data

------------------------------------------------------------------------

### 📦 Step 3: Install Dependencies

    pip install boto3 python-dotenv

------------------------------------------------------------------------

### ✅ Step 4: Test S3 Connection

    python src/utils/s3_utils.py

------------------------------------------------------------------------

## 🧠 How to Use S3 in Code

``` python
from src.utils.s3_utils import upload_file, download_file, list_files

upload_file('data/fire.csv', 'raw/fire_ignition/fire.csv')
download_file('processed/fire/clean.csv', 'local/clean.csv')
list_files('raw/')
```

------------------------------------------------------------------------

## 🔒 Security Best Practices

-   NEVER commit `.env`
-   NEVER hardcode keys
-   Always use environment variables

------------------------------------------------------------------------

## 📦 Requirements

-   Python 3.8+
-   boto3
-   python-dotenv
