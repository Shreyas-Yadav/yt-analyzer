import os
import sys
import boto3
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_db_connection():
    print("Testing Database Connection...")
    
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME")
    
    if not all([db_user, db_host, db_name]):
        print("❌ Missing DB environment variables (DB_USER, DB_HOST, DB_NAME)")
        return False

    # Handle special characters in password
    from urllib.parse import quote_plus
    if db_password:
        db_password = quote_plus(db_password)

    db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    print(f"Constructed URL: mysql+pymysql://{db_user}:****@{db_host}:{db_port}/{db_name}")

    try:
        # Try to connect to the target database
        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"✅ Database connection successful to '{db_name}'!")
            return True
    except Exception as e:
        # Check if error is "Unknown database" (1049)
        if "1049" in str(e) or "Unknown database" in str(e):
            print(f"⚠️  Target database '{db_name}' does not exist yet.")
            print("   Attempting to connect to system 'mysql' database to verify credentials...")
            
            # Try connecting to 'mysql' system db
            system_db_url = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/mysql"
            try:
                engine = create_engine(system_db_url)
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    print("✅ Connection to RDS server successful! (Credentials are correct)")
                    print(f"   The application will automatically create the '{db_name}' database on startup.")
                    return True
            except Exception as sys_e:
                print(f"❌ Connection to RDS server failed: {sys_e}")
                return False
        else:
            print(f"❌ Database connection failed: {e}")
            return False

def test_s3_connection():
    print("\nTesting S3 Connection...")
    bucket_name = os.getenv("S3_BUCKET_NAME")
    if not bucket_name:
        print("❌ S3_BUCKET_NAME not found in .env")
        return False

    try:
        s3 = boto3.client(
            's3',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN')
        )
        # Try to list objects (lightweight check)
        s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        print(f"✅ S3 connection successful! (Bucket: {bucket_name})")
        return True
    except Exception as e:
        print(f"❌ S3 connection failed: {e}")
        return False

def test_sqs_connection():
    print("\nTesting SQS Connection...")
    queue_url = os.getenv("SQS_TRANSCRIPTION_QUEUE_URL")
    if not queue_url:
        print("⚠️  SQS_TRANSCRIPTION_QUEUE_URL not found in .env (Skipping SQS test)")
        return True # Not a failure if not configured yet

    try:
        sqs = boto3.client(
            'sqs',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN')
        )
        # Try to get queue attributes
        sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['ApproximateNumberOfMessages'])
        print(f"✅ SQS connection successful! (Queue: {queue_url})")
        return True
    except Exception as e:
        print(f"❌ SQS connection failed: {e}")
        return False

if __name__ == "__main__":
    print("--- YT Analyzer Connection Test ---\n")
    db_ok = test_db_connection()
    s3_ok = test_s3_connection()
    sqs_ok = test_sqs_connection()
    
    if db_ok and s3_ok and sqs_ok:
        print("\n✅ All connections look good!")
        sys.exit(0)
    else:
        print("\n❌ Some connections failed. Please check your .env file and AWS settings.")
        sys.exit(1)
