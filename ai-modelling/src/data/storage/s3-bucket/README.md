# AWS S3 Python Script Guide

A reference guide for setting up credentials and using the AWS S3 Python script with `boto3`.

---

## Prerequisites

- Python 3.7+
- An AWS account with S3 access
- IAM user or role with appropriate S3 permissions

---

## Installation

Install the `boto3` library using pip:

```bash
pip install boto3
```

To verify the installation:

```bash
python -c "import boto3; print(boto3.__version__)"
```

---

## Setting Up AWS Credentials

`boto3` supports several credential methods. They are evaluated in the order listed below — the first one found is used.

### Method 1: Environment Variables (Recommended for Dev/CI)

Set the following environment variables in your shell session or CI pipeline:

**macOS / Linux:**
```bash
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key
export AWS_DEFAULT_REGION=us-east-1
```

**Windows (Command Prompt):**
```cmd
set AWS_ACCESS_KEY_ID=your_access_key_id
set AWS_SECRET_ACCESS_KEY=your_secret_access_key
set AWS_DEFAULT_REGION=us-east-1
```

**Windows (PowerShell):**
```powershell
$env:AWS_ACCESS_KEY_ID = "your_access_key_id"
$env:AWS_SECRET_ACCESS_KEY = "your_secret_access_key"
$env:AWS_DEFAULT_REGION = "us-east-1"
```

> **Tip:** Add these to your `.bashrc`, `.zshrc`, or system environment settings to persist them across sessions.

---

### Method 2: AWS Credentials File

This is the standard method used by the AWS CLI and SDKs.

**Step 1:** Install the AWS CLI (optional but recommended):
```bash
pip install awscli
```

**Step 2:** Run the interactive configuration wizard:
```bash
aws configure
```

You will be prompted for:
```
AWS Access Key ID [None]: your_access_key_id
AWS Secret Access Key [None]: your_secret_access_key
Default region name [None]: us-east-1
Default output format [None]: json
```

This creates two files:

- `~/.aws/credentials` — stores your keys
- `~/.aws/config` — stores region and output format

**Credentials file format** (`~/.aws/credentials`):
```ini
[default]
aws_access_key_id = your_access_key_id
aws_secret_access_key = your_secret_access_key

[production]
aws_access_key_id = prod_access_key_id
aws_secret_access_key = prod_secret_access_key
```

To use a non-default profile in the script:
```python
boto3.client("s3", region_name="us-east-1")
# or set the profile via environment variable:
# export AWS_PROFILE=production
```

---

### Method 3: IAM Role (EC2 / Lambda / ECS)

When running on AWS infrastructure, no credentials are needed. Attach an IAM role to your compute resource and `boto3` picks up the temporary credentials automatically.

This is the most secure method for production workloads.

---

## Finding Your AWS Access Keys

1. Sign in to the [AWS Management Console](https://console.aws.amazon.com/)
2. Click your account name (top right) → **Security credentials**
3. Scroll to **Access keys** → click **Create access key**
4. Copy the **Access Key ID** and **Secret Access Key** — the secret is only shown once

> **Security note:** Never commit credentials to source control. Use `.gitignore` to exclude `.env` files and `~/.aws/` is already outside your project directory.

---

## Required IAM Permissions

The IAM user or role needs the following S3 permissions depending on which operations you use:

| Operation | Required Permission |
|---|---|
| List buckets | `s3:ListAllMyBuckets` |
| List objects | `s3:ListBucket` |
| Upload file | `s3:PutObject` |
| Download file | `s3:GetObject` |
| Delete object | `s3:DeleteObject` |
| Generate pre-signed URL | `s3:GetObject` |

A minimal IAM policy for full script access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListAllMyBuckets",
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name",
        "arn:aws:s3:::your-bucket-name/*"
      ]
    }
  ]
}
```

---

## Script Configuration

Before running the script, update these two constants at the top of the file:

```python
AWS_REGION = "us-east-1"      # Your bucket's AWS region
BUCKET_NAME = "your-bucket-name"  # Your S3 bucket name
```

Common AWS regions:

| Region | Code |
|---|---|
| US East (N. Virginia) | `us-east-1` |
| US West (Oregon) | `us-west-2` |
| EU (Ireland) | `eu-west-1` |
| Asia Pacific (Sydney) | `ap-southeast-2` |

---

## Usage

### Running the Script

```bash
python s3_script.py
```

### Available Functions

| Function | Description | Example |
|---|---|---|
| `list_buckets(s3)` | List all buckets in your account | `list_buckets(s3)` |
| `list_objects(s3, bucket, prefix)` | List objects, optionally filtered by prefix | `list_objects(s3, "my-bucket", "data/")` |
| `upload_file(s3, local_path, bucket, s3_key)` | Upload a local file to S3 | `upload_file(s3, "report.pdf", "my-bucket", "reports/report.pdf")` |
| `download_file(s3, bucket, s3_key, local_path)` | Download an S3 object to disk | `download_file(s3, "my-bucket", "reports/report.pdf", "local.pdf")` |
| `upload_string(s3, content, bucket, s3_key)` | Write a string directly to S3 | `upload_string(s3, "hello", "my-bucket", "hello.txt")` |
| `read_object(s3, bucket, s3_key)` | Read an S3 object into memory | `read_object(s3, "my-bucket", "hello.txt")` |
| `delete_object(s3, bucket, s3_key)` | Delete an object from S3 | `delete_object(s3, "my-bucket", "hello.txt")` |
| `generate_presigned_url(s3, bucket, s3_key, expiry)` | Create a temporary shareable URL | `generate_presigned_url(s3, "my-bucket", "report.pdf", 3600)` |

### Example: Upload and Read Back a File

```python
s3 = get_s3_client()

# Upload a local CSV
upload_file(s3, "data.csv", "my-bucket", "exports/data.csv")

# Read it back into memory
content = read_object(s3, "my-bucket", "exports/data.csv")
print(content)
```

### Example: List Objects Under a Folder Prefix

```python
s3 = get_s3_client()
objects = list_objects(s3, "my-bucket", prefix="exports/")
# Returns: ['exports/data.csv', 'exports/report.pdf', ...]
```

### Example: Share a File via Pre-signed URL

```python
s3 = get_s3_client()
url = generate_presigned_url(s3, "my-bucket", "reports/q4.pdf", expiry_seconds=86400)
# URL is valid for 24 hours — share with anyone, no AWS account needed
```

---

## Common Errors

### `NoCredentialsError`
```
Error: AWS credentials not found.
```
**Fix:** Ensure `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set as environment variables, or that `~/.aws/credentials` exists and is correctly formatted.

### `ClientError: Access Denied`
```
AWS error: Access Denied
```
**Fix:** The IAM user or role lacks the required S3 permission for that operation. Review and update the attached IAM policy.

### `ClientError: NoSuchBucket`
```
AWS error: The specified bucket does not exist
```
**Fix:** Check that `BUCKET_NAME` in the script matches an existing bucket in the correct region.

### `ClientError: InvalidRegion`
**Fix:** Ensure `AWS_REGION` in the script matches the region where your bucket was created.

---

## Security Best Practices

- **Never hardcode credentials** in the script — always use environment variables or the credentials file.
- **Use IAM roles** instead of long-lived access keys when running on AWS infrastructure.
- **Rotate access keys** regularly via the AWS console.
- **Apply least-privilege permissions** — only grant the S3 actions the script actually uses.
- **Add `.env` to `.gitignore`** if storing credentials in a local env file.
- **Enable S3 bucket versioning** to protect against accidental deletions.

---

## Further Reading

- [boto3 S3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [S3 Bucket Policies](https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-policies.html)
- [AWS CLI Configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html)