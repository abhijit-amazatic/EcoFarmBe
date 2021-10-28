"""
Aws module.
"""
import boto3
from botocore.client import (Config, UNSIGNED)
from botocore.exceptions import ClientError
from core.settings import (AWS_CLIENT_ID, AWS_CLIENT_SECRET, AWS_REGION, AWS_OUTPUT_BUCKET)


def get_boto_resource_s3(
        aws_access_key_id=AWS_CLIENT_ID,
        aws_secret_access_key=AWS_CLIENT_SECRET,
        **kwargs,
    ):
    """
    Return aws resource S3.

    @aws_access_key_id: access key.
    @aws_secret_access_key: secret key.
    """
    return boto3.resource(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        **kwargs,
    )


def get_boto_client(
        resource,
        aws_access_key_id=AWS_CLIENT_ID,
        aws_secret_access_key=AWS_CLIENT_SECRET,
        region=AWS_REGION,
        **kwargs,
    ):
    """
    Return aws client for resource.

    @param resource: aws resource name.
    @aws_access_key_id: access key.
    @aws_secret_access_key: secret key.
    """
    return boto3.client(
        resource,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=region,
        **kwargs,
    )

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

def create_presigned_url(bucket_name, object_name, expiration=604800):
    """
    Generate a presigned URL to share an S3 object

    @param bucket_name: string
    @param object_name: string
    @param expiration: Time in seconds for the presigned URL to remain valid
    @return: Presigned URL as string. If error, returns None.
    """
    s3_client = get_boto_client('s3')
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




def get_s3_output_url_unsigned(key, Bucket):
    s3_unsigned_config = Config(signature_version=UNSIGNED)
    S3_unsigned = boto3.client('s3', config=s3_unsigned_config)
    return S3_unsigned.generate_presigned_url('get_object', ExpiresIn=0, Params={'Bucket': Bucket, 'Key': key})


def upload_compressed_file_stream_to_s3(file_obj, key):
    S3 = get_boto_resource_s3()
    S3_bucket = S3.Bucket(AWS_OUTPUT_BUCKET)
    file_obj.seek(0)
    S3_bucket.put_object(Key=key, Body=file_obj, CacheControl='max-age=86400', ACL='public-read')
    s3_url = get_s3_output_url_unsigned(key, AWS_OUTPUT_BUCKET)
    return  s3_url
