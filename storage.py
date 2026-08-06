from io import BytesIO
import pandas as pd

def save_parquet(df: pd.DataFrame, key: str, s3, bucket):
    buffer = BytesIO()

    df.to_parquet(buffer, index=True, engine='pyarrow')
    buffer.seek(0)

    s3.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue(), ContentType='application/octet-stream')



def load_parquet(key: str, s3, bucket) -> pd.DataFrame:
    response = s3.get_object(Bucket=bucket, Key=key)

    buffer = BytesIO(response['Body'].read())

    return pd.read_parquet(buffer)