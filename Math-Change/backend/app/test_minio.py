"""
Test MinIO/S3 Connection
Prueba la conexión con el bucket S3/MinIO configurado en variables de entorno.

Uso:
  docker compose exec backend python -m app.test_minio
"""

import os
import boto3
from botocore.client import Config
from dotenv import load_dotenv

load_dotenv()


def test_minio_connection():
    endpoint = os.getenv("S3_ENDPOINT_URL")
    access_key = os.getenv("S3_ACCESS_KEY")
    secret_key = os.getenv("S3_SECRET_KEY")
    bucket = os.getenv("S3_BUCKET_NAME", "math-avatars")

    if not all([endpoint, access_key, secret_key]):
        print("❌ ERROR: Missing S3 environment variables (S3_ENDPOINT_URL, S3_ACCESS_KEY, S3_SECRET_KEY)")
        return False

    print("=" * 50)
    print("MinIO/S3 Connection Test")
    print("=" * 50)
    print(f"  Endpoint: {endpoint}")
    print(f"  Access Key: {access_key[:5]}...")
    print(f"  Bucket: {bucket}")
    print("-" * 50)

    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4'),
            region_name=os.getenv("S3_REGION", "us-east-1")
        )

        # Test 1: List buckets
        print("\n[TEST 1] Listing buckets...")
        response = s3_client.list_buckets()
        buckets = [b['Name'] for b in response.get('Buckets', [])]
        print(f"  ✅ Found {len(buckets)} bucket(s): {buckets}")

        # Test 2: Check if our bucket exists
        print(f"\n[TEST 2] Checking bucket '{bucket}'...")
        if bucket in buckets:
            print(f"  ✅ Bucket '{bucket}' exists!")
        else:
            print(f"  ⚠️ Bucket '{bucket}' not found. Creating...")
            s3_client.create_bucket(Bucket=bucket)
            print(f"  ✅ Bucket '{bucket}' created!")

        # Test 3: Upload test file
        print(f"\n[TEST 3] CREATE - Uploading test file...")
        test_content = b"Hello from Math Challenge - Connection test successful!"
        test_key = "test_connection_file.txt"
        s3_client.put_object(
            Bucket=bucket,
            Key=test_key,
            Body=test_content,
            ContentType='text/plain'
        )
        print(f"  ✅ File '{test_key}' uploaded successfully!")

        # Test 4: Read test file
        print(f"\n[TEST 4] READ - Reading test file...")
        response = s3_client.get_object(Bucket=bucket, Key=test_key)
        content = response['Body'].read()
        print(f"  Content: {content.decode()}")
        print(f"  ✅ File read successfully!")

        # Test 5: List objects
        print(f"\n[TEST 5] LIST - Listing objects in bucket...")
        response = s3_client.list_objects_v2(Bucket=bucket, MaxKeys=10)
        objects = response.get('Contents', [])
        for obj in objects:
            print(f"    - {obj['Key']} ({obj['Size']} bytes)")
        print(f"  ✅ Listed {len(objects)} object(s)")

        # Test 6: Delete test file
        print(f"\n[TEST 6] DELETE - Removing test file...")
        s3_client.delete_object(Bucket=bucket, Key=test_key)
        print(f"  ✅ File '{test_key}' deleted successfully!")

        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED! MinIO/S3 connection is working.")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ Connection FAILED!")
        print(f"  Error Type: {type(e).__name__}")
        print(f"  Error Message: {e}")
        return False

    return True


if __name__ == "__main__":
    test_minio_connection()
