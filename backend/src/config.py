import os
import json
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

def load_config():
    """
    Load configuration from .env files and AWS SSM Parameter Store.
    
    Priority:
    1. Environment Variables (already set or from .env)
    2. AWS SSM Parameter Store (Individual Parameters)
    
    This allows local development to override SSM values using .env,
    while production (EC2) relies on SSM.
    """
    # 1. Load .env file (if exists) - useful for local dev
    load_dotenv()
    
    # 2. Try to load from AWS SSM
    aws_region = os.getenv("AWS_REGION", "us-east-1")
    
    try:
        # Create SSM client
        ssm = boto3.client('ssm', region_name=aws_region)
        
        REQUIRED_PARAMS = [
            "DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME", "DB_PORT",
            "S3_BUCKET_NAME", "SQS_TRANSCRIPTION_QUEUE_URL",
            "ANTHROPIC_API_KEY"
        ]
        
        # print(f"Attempting to fetch individual parameters from SSM (Region: {aws_region})...")
        
        # We can fetch multiple parameters at once to be efficient
        response = ssm.get_parameters(
            Names=REQUIRED_PARAMS,
            WithDecryption=True
        )
        
        found_count = 0
        loaded_count = 0
        
        for param in response.get('Parameters', []):
            found_count += 1
            key = param['Name']
            # If the parameter name matches our env var name (e.g. "DB_HOST")
            if key in REQUIRED_PARAMS:
                # Only set if not already in environment (allow .env override)
                if key not in os.environ:
                    os.environ[key] = param['Value']
                    loaded_count += 1
        
        if loaded_count > 0:
            print(f"Successfully loaded {loaded_count} individual parameters from SSM.")
        elif found_count > 0:
            print(f"Found {found_count} parameters in SSM (using local .env overrides).")
        else:
            # This is expected if running locally without AWS credentials or if params don't exist
            print("No individual parameters found in SSM matching expected names.")
            print("Falling back to local environment variables.")
            
    except ClientError as e:
        print(f"Warning: Could not load parameters from SSM: {e}")
        print("Falling back to local environment variables.")
    except Exception as e:
        print(f"Warning: Unexpected error loading from SSM: {e}")

# Automatically load config when module is imported
load_config()
