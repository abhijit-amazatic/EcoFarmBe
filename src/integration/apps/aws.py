"""
Aws module.
"""
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from core.settings import (AWS_CLIENT_ID, AWS_CLIENT_SECRET, AWS_REGION)

def get_boto_client(resource,
                    aws_access_key_id=AWS_CLIENT_ID,
                    aws_secret_access_key=AWS_CLIENT_SECRET,
                    region=AWS_REGION,
                    config=None):
    """
    Return aws client for resource.
    
    @param resource: aws resource name.
    @aws_access_key_id: access key.
    @aws_secret_access_key: secret key.
    """
    return boto3.client(resource,
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        region_name=region,
                        config=config)

def create_presigned_post(bucket_name, object_name, expiration=3600):
    """
    Generate a presigned URL S3 POST request to upload a file
    """
    s3_client = get_boto_client('s3')
    try:
        response = s3_client.generate_presigned_url('put_object',
                                             Params={
                                                 'Bucket': bucket_name,
                                                 'Key': object_name,
                                                 'ACL': 'private'},
                                             ExpiresIn=expiration)
    except ClientError as exc:
        return {'error': f'Error while creating presigned url - {exc}',
                'status_code': 1}
    return {'status_code': 0, 'url': response}

def create_presigned_url(bucket_name, object_name, expiration=3600):
    """
    Generate a presigned URL to share an S3 object

    @param bucket_name: string
    @param object_name: string
    @param expiration: Time in seconds for the presigned URL to remain valid
    @return: Presigned URL as string. If error, returns None.
    """
    config = Config(s3={'addressing_style': 'path'}, signature_version='s3v4')
    s3_client = get_boto_client('s3', config=config)
    try:
        response = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name,
                    'Key': object_name},
            ExpiresIn=expiration)
    except ClientError as exc:
        return {'error': f'Error while creating presigned url - {exc}',
                'status_code': 1}
    return {'status_code': 0, 'response': response}