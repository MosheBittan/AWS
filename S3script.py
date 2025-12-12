import boto3
import logging
from botocore.exceptions import ClientError
import os
import json

def make_bucket_public(bucket_name):
    s3 = boto3.client('s3')

    # --- STEP 1: Disable "Block Public Access" ---
    # By default, new buckets block all public access. We must turn this off first.
    print(f"Disabling 'Block Public Access' for {bucket_name}...")
    try:
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': False,
                'IgnorePublicAcls': False,
                'BlockPublicPolicy': False,
                'RestrictPublicBuckets': False
            }
        )
    except ClientError as e:
        logging.error(f"Failed to unblock public access: {e}")
        return False

    # --- STEP 2: Apply the Public Read Policy ---
    # This policy allows anyone (Principal: *) to download (Action: s3:GetObject)
    # any file (Resource: .../*) from the bucket.
    
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/*"  # Note the /* at the end
            }
        ]
    }

    # Convert the dictionary to a JSON string
    policy_string = json.dumps(bucket_policy)

    print(f"Applying public policy to {bucket_name}...")
    try:
        s3.put_bucket_policy(
            Bucket=bucket_name,
            Policy=policy_string
        )
        print("Success! The bucket is now public.")
    except ClientError as e:
        logging.error(f"Failed to apply policy: {e}")
        return False
        
    return True

# --- Usage ---

def create_bucket(bucket_name, region=None):
    """Create an S3 bucket in a specified region

    If a region is not specified, the bucket is created in the S3 default
    region (us-east-1).
    """
    # Create bucket
    try:
        if region is None:
            s3_client = boto3.client('s3')
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client = boto3.client('s3', region_name=region)
            location = {'LocationConstraint': region}
            s3_client.create_bucket(Bucket=bucket_name,
                                    CreateBucketConfiguration=location)
        print(f"Success: Bucket '{bucket_name}' created.")
    except ClientError as e:
        logging.error(e)
        return False
    return True

def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload (local path)
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
        print(f"Success: '{file_name}' uploaded to '{bucket}/{object_name}'.")
    except ClientError as e:
        logging.error(e)
        return False
    return True

# --- Main Execution ---
if __name__ == '__main__':
    # Configuration
    MY_REGION = 'il-central-1' # Change this to your preferred region
    MY_BUCKET_NAME = 'my-unique-bucket-name-moshe-test1' # Must be globally unique
    FILE_TO_UPLOAD = 'test_file.txt' 

    # Create a dummy file for testing
    with open(FILE_TO_UPLOAD, "w") as f:
        f.write("Hello S3!")

    # 1. Create Bucket
    create_bucket(MY_BUCKET_NAME, MY_REGION)

    # 2. Upload File
    upload_file(FILE_TO_UPLOAD, MY_BUCKET_NAME)

    # 3. Upload File car
    upload_file("car.jpg", MY_BUCKET_NAME)

    BUCKET_NAME = 'my-unique-bucket-name-moshe-test1' # Replace with your bucket
    make_bucket_public(BUCKET_NAME)
