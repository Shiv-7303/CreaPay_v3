import os
import boto3
from botocore.exceptions import ClientError
from flask import current_app
import io

def get_r2_client():
    return boto3.client(
        's3',
        endpoint_url=current_app.config.get('R2_ENDPOINT_URL') or os.environ.get('R2_ENDPOINT_URL'),
        aws_access_key_id=current_app.config.get('R2_ACCESS_KEY_ID') or os.environ.get('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=current_app.config.get('R2_SECRET_ACCESS_KEY') or os.environ.get('R2_SECRET_ACCESS_KEY'),
        region_name='auto'
    )

def upload_pdf_to_r2(pdf_bytes, filename):
    # During testing we might not have R2 credentials, mock it out
    if current_app.config.get('TESTING'):
        return f"https://mock-r2.com/{filename}"
        
    bucket_name = current_app.config.get('R2_BUCKET_NAME') or os.environ.get('R2_BUCKET_NAME')
    public_url = current_app.config.get('R2_PUBLIC_URL') or os.environ.get('R2_PUBLIC_URL')
    
    if not bucket_name or bucket_name == 'creapay-invoices':
        # Don't crash for users running locally without Cloudflare R2 API keys
        print("WARNING: R2_BUCKET_NAME is empty or default. Mocking PDF upload.")
        return f"https://mock-r2.com/local-dev/{filename}"

    s3 = get_r2_client()
    try:
        s3.upload_fileobj(
            io.BytesIO(pdf_bytes),
            bucket_name,
            filename,
            ExtraArgs={'ContentType': 'application/pdf'}
        )
        return f"{public_url}/{filename}" if public_url else f"https://r2.cloudflare.com/{filename}"
    except Exception as e:
        print(f"Error uploading to R2: {e}")
        return f"https://mock-r2.com/error-fallback/{filename}"

def delete_from_r2(file_url):
    if current_app.config.get('TESTING'):
        return True
        
    bucket_name = current_app.config.get('R2_BUCKET_NAME') or os.environ.get('R2_BUCKET_NAME')
    if not bucket_name or bucket_name == 'creapay-invoices':
        return True
        
    # Extract filename from URL (assumes standard R2 public URL format)
    filename = file_url.split('/')[-1]
    
    s3 = get_r2_client()
    try:
        s3.delete_object(Bucket=bucket_name, Key=filename)
        return True
    except Exception as e:
        print(f"Error deleting from R2: {e}")
        return False

def upload_image_to_r2(image_bytes, filename, content_type):
    if current_app.config.get('TESTING'):
        return f"https://mock-r2.com/logos/{filename}"
        
    bucket_name = current_app.config.get('R2_BUCKET_NAME') or os.environ.get('R2_BUCKET_NAME')
    public_url = current_app.config.get('R2_PUBLIC_URL') or os.environ.get('R2_PUBLIC_URL')
    
    if not bucket_name or bucket_name == 'creapay-invoices':
        print("WARNING: R2_BUCKET_NAME is empty or default. Mocking Image upload.")
        return f"https://mock-r2.com/local-dev/logos/{filename}"

    s3 = get_r2_client()
    try:
        s3.upload_fileobj(
            io.BytesIO(image_bytes),
            bucket_name,
            filename,
            ExtraArgs={'ContentType': content_type}
        )
        return f"{public_url}/{filename}" if public_url else f"https://r2.cloudflare.com/{filename}"
    except Exception as e:
        print(f"Error uploading to R2: {e}")
        # In a real app, integrate Sentry logging here
        return f"https://mock-r2.com/error-fallback/logos/{filename}"
