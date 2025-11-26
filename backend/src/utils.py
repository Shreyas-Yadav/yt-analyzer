import os
import boto3
import json
from botocore.exceptions import ClientError

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
SQS_QUEUE_URL = os.getenv('SQS_TRANSCRIPTION_QUEUE_URL')

# Initialize AWS Clients
try:
    if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
        s3 = boto3.client(
            's3',
            region_name=AWS_REGION,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN')
        )
        sqs = boto3.client(
            'sqs',
            region_name=AWS_REGION,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN')
        )
    else:
        s3 = boto3.client('s3', region_name=AWS_REGION)
        sqs = boto3.client('sqs', region_name=AWS_REGION)
        
    USE_S3 = bool(S3_BUCKET_NAME)
except Exception as e:
    print(f"Warning: AWS clients not initialized in utils - {e}")
    USE_S3 = False
    s3 = None
    sqs = None

def upload_to_s3(local_path: str, s3_key: str) -> str:
    """Upload file to S3 and return S3 URI"""
    if not USE_S3:
        return local_path
    
    try:
        s3.upload_file(local_path, S3_BUCKET_NAME, s3_key)
        return f"s3://{S3_BUCKET_NAME}/{s3_key}"
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        raise

def delete_from_s3(s3_uri: str):
    """Delete file from S3 given its URI"""
    if not USE_S3 or not s3_uri.startswith("s3://"):
        return
    
    try:
        parts = s3_uri.replace("s3://", "").split("/", 1)
        if len(parts) < 2:
            return
        
        bucket = parts[0]
        key = parts[1]
        
        s3.delete_object(Bucket=bucket, Key=key)
        print(f"Deleted from S3: {key}")
    except Exception as e:
        print(f"Error deleting from S3: {e}")

def read_file_content(file_path: str) -> str:
    """Read content from local file or S3"""
    if file_path.startswith("s3://"):
        if not USE_S3:
            raise Exception("S3 not configured but file path is S3 URI")
        
        try:
            parts = file_path.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1]
            
            response = s3.get_object(Bucket=bucket, Key=key)
            return response['Body'].read().decode('utf-8')
        except Exception as e:
            print(f"Error reading from S3: {e}")
            raise
    else:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

def send_to_sqs(message_body: dict):
    """Send message to SQS queue"""
    if not SQS_QUEUE_URL:
        print("Warning: SQS_QUEUE_URL not set, skipping SQS message")
        return
    
    try:
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(message_body)
        )
        print(f"Sent message to SQS: {message_body}")
    except Exception as e:
        print(f"Error sending to SQS: {e}")
        raise
