from io import BytesIO
import os
import json
import boto3
import pandas as pd
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()
ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')


s3 = boto3.client(
    service_name="s3",
    endpoint_url="https://f2050c9eff5c17ffb10f5e72a0a973b2.r2.cloudflarestorage.com",
    aws_access_key_id=ACCESS_KEY_ID,
    aws_secret_access_key=SECRET_ACCESS_KEY,
    region_name="auto",
)


def check_file_in_bucket(bucket: str, key: str, ticker: str, file_type: str):
    try:
        response = s3.head_object(Bucket=bucket, Key=f'{key}/{ticker}.{file_type}')
        return True, response['LastModified']
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            print(f'{ticker}.{file_type} NOT found in R2')
        elif error_code == '403':
            print('Error: Access denied')
        else:
            print('An unexpected error occurred')
        return False, None


def save_parquet(bucket: str, key: str, df: pd.DataFrame):
    buffer = BytesIO()

    df.to_parquet(buffer, index=True, engine='pyarrow')
    buffer.seek(0)

    s3.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue(), ContentType='application/octet-stream')


def load_parquet(bucket: str, key: str) -> pd.DataFrame:
    response = s3.get_object(Bucket=bucket, Key=key)

    buffer = BytesIO(response['Body'].read())

    return pd.read_parquet(buffer)


def save_json(bucket, key, body):
    s3.put_object(Bucket=bucket, Key=key, Body=body, ContentType='application/json')


def load_json(bucket, key):
    response = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(response['Body'].read().decode('utf-8'))