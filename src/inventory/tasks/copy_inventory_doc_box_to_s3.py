import boto3
from io import (BytesIO, BufferedReader)
from requests import  request
from django.conf import settings
from django.utils import timezone

from botocore import (UNSIGNED,)
from botocore.config import (Config,)
from botocore.exceptions import ClientError
from core.celery import (app,)
from integration.box import get_file_obj
from inventory.models import Documents, Inventory

CACHE_CONTROL = 'max-age=604800'
extra_args_video = {'ACL':'public-read', 'ContentType': 'video/mp4'}
extra_args_img = {'CacheControl': CACHE_CONTROL, 'ACL': 'public-read', 'ContentType': 'image/jpeg'}

S3 = boto3.resource(
    's3',
    aws_access_key_id=settings.AWS_CLIENT_ID,
    aws_secret_access_key=settings.AWS_CLIENT_SECRET,
    # region=settings.AWS_REGION,
)

s3_unsigned_config = Config(signature_version=UNSIGNED)
S3_client_unsigned = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_CLIENT_ID,
    aws_secret_access_key=settings.AWS_CLIENT_SECRET,
    # region=settings.AWS_REGION,
    config=s3_unsigned_config,
)

transfer_config_img = boto3.s3.transfer.TransferConfig(
    multipart_threshold=8388608,
    max_concurrency=10,
    multipart_chunksize=8388608,
    num_download_attempts=5,
    max_io_queue=100,
    io_chunksize=262144,
    use_threads=True
)

def get_s3_output_url_unsigned(key):
    return S3_client_unsigned.generate_presigned_url('get_object', ExpiresIn=0, Params={'Bucket': settings.AWS_OUTPUT_BUCKET, 'Key': key})


@app.task(queue="general")
def inv_img_box_to_s3_task():

    uploaded = 0.0
    def cb(bites):
        nonlocal uploaded
        uploaded += bites
        if uploaded < 1000:
            print("\r{0:.03f} B".format(uploaded), end='')
        elif uploaded < 1000000:
            print("\r{0:.03f} KB".format(uploaded/1024), end='')
        else :
            print("\r{0:.03f} MB".format(uploaded/(1024*1024)), end='')


    from django.contrib.contenttypes.models import ContentType
    ct = ContentType.objects.get_for_model(Inventory)
    qs = Documents.objects.filter(content_type=ct)

    video_qs = qs.filter(file_type__startswith='video', status='AVAILABLE')
    for doc in video_qs:
        if  not doc.S3_url and doc.box_id:
            try:
                file_obj = get_file_obj(doc.box_id)
                file_name = file_obj.name
                file_name_split = file_name.split('.')
                # file_ = BufferedReader(BytesIO(file_obj.content()))
                # file_ = BufferedReader(file_obj.content())
                s3_key = '/'.join(('inventory', doc.sku, str(doc.id), file_name))
                print(s3_key)
                # S3.Bucket(settings.AWS_OUTPUT_BUCKET).put_object(Key=s3_key, Body=bytes_obj, CacheControl='max-age=86400',)
                try:
                    # s3_obj = S3.get_object(Bucket=settings.AWS_OUTPUT_BUCKET, Key=s3_key,)
                    obj = S3.Bucket(settings.AWS_OUTPUT_BUCKET).Object(s3_key)
                    obj.get()
                except ClientError as ex:
                    if ex.response['Error']['Code'] == 'NoSuchKey':
                        r = request('get', file_obj.get_download_url(), stream=True)
                        if r.status_code == 200:
                            uploaded = 0.0
                            S3.Bucket(settings.AWS_OUTPUT_BUCKET).upload_fileobj(r.raw, s3_key, extra_args_video, Callback=cb)
                            # obj.put(Body=file_obj.content(), CacheControl=CACHE_CONTROL, ACL='public-read')
                            # S3.put_object(Bucket=settings.AWS_OUTPUT_BUCKET, Key=s3_key, CacheControl='max-age=86400', ACL='public-read')
                            print()
                    else:
                        raise ex
                else:
                    obj.copy_from(
                        ACL='public-read',
                        CopySource={'Bucket': settings.AWS_OUTPUT_BUCKET, 'Key': obj.key},
                        CacheControl=CACHE_CONTROL,
                        MetadataDirective='REPLACE',
                    )
                    print(' file present.')
                s3_url = get_s3_output_url_unsigned(s3_key)
                doc.S3_url = s3_url
                doc.save()

                if not doc.s3_thumbnail_url and doc.thumbnail_url:
                    # r = request('get', doc.thumbnail_url)
                    r = request('get', doc.thumbnail_url, stream=True)
                    if r.status_code == 200:
                        print('thumbnail:')
                        # bytes_obj = r.content
                        file_name = file_name_split[0] + '-thumbnail.jpg'
                        s3_key = '/'.join(('inventory', doc.sku, str(doc.id), file_name))
                        uploaded = 0.0
                        S3.Bucket(settings.AWS_OUTPUT_BUCKET).upload_fileobj(r.raw, s3_key, extra_args_img, Callback=cb)
                        print()
                        # S3.Bucket(settings.AWS_OUTPUT_BUCKET).put_object(Key=s3_key, Body=bytes_obj, CacheControl=CACHE_CONTROL, ACL='public-read')
                        s3_thumbnail_url = get_s3_output_url_unsigned(s3_key)
                        doc.s3_thumbnail_url = s3_thumbnail_url
                        doc.save()

            except Exception as e:
                print('Error:', e)


    image_qs = qs.filter(file_type__startswith='image', status='AVAILABLE')
    for doc in image_qs:
        if  not doc.S3_url and doc.box_id:
            try:
                file_obj = get_file_obj(doc.box_id)
                file_name = file_obj.name
                file_name = file_name.replace('-main', '')
                file_name_split = file_name.split('.')
                s3_key = '/'.join(('inventory', doc.sku, str(doc.id), file_name))
                print(s3_key)
                # r = request('get', file_obj.get_download_url(), stream=True)
                # if r.status_code == 200:
                # file_content = file_obj.content()
                # bytes_obj = BytesIO(file_obj.content())
                # file_ = BufferedReader(r.raw)

                r = request('get', file_obj.get_download_url(), stream=True)
                if r.status_code == 200:
                    uploaded = 0.0
                    S3.Bucket(settings.AWS_OUTPUT_BUCKET).upload_fileobj(r.raw, s3_key, extra_args_img, Callback=cb)
                    # obj.put(Body=file_obj.content(), CacheControl=CACHE_CONTROL, ACL='public-read')
                    # S3.put_object(Bucket=settings.AWS_OUTPUT_BUCKET, Key=s3_key, CacheControl='max-age=86400', ACL='public-read')
                    # S3.Bucket(settings.AWS_OUTPUT_BUCKET).put_object(Key=s3_key, Body=file_content, CacheControl=CACHE_CONTROL, ACL='public-read')
                    print()
                    # S3.Bucket(settings.AWS_OUTPUT_BUCKET).put_object(Key=s3_key, Body=r.raw, CacheControl=CACHE_CONTROL, ACL='public-read')
                    s3_url = get_s3_output_url_unsigned(s3_key)
                    doc.S3_url = s3_url

                if not doc.S3_mobile_url and doc.mobile_url:
                    # r = request('get', doc.mobile_url)
                    r = request('get', doc.mobile_url, stream=True)
                    if r.status_code == 200:
                        print('mobile:')
                        # bytes_obj = r.content
                        file_name = file_name_split[0] + '-mobile.' + file_name_split[1]
                        s3_key = '/'.join(('inventory', doc.sku, str(doc.id), file_name))
                        uploaded = 0.0
                        S3.Bucket(settings.AWS_OUTPUT_BUCKET).upload_fileobj(r.raw, s3_key, extra_args_img, Callback=cb)
                        print()
                        # S3.Bucket(settings.AWS_OUTPUT_BUCKET).put_object(Key=s3_key, Body=bytes_obj, CacheControl=CACHE_CONTROL, ACL='public-read')
                        S3_mobile_url = get_s3_output_url_unsigned(s3_key)
                        doc.S3_mobile_url = S3_mobile_url

                if not doc.s3_thumbnail_url and doc.thumbnail_url:
                    # r = request('get', doc.thumbnail_url)
                    r = request('get', doc.thumbnail_url, stream=True)
                    if r.status_code == 200:
                        print('thumbnail:')
                        # bytes_obj = r.content
                        file_name = file_name_split[0] + '-thumbnail.jpg'
                        s3_key = '/'.join(('inventory', doc.sku, str(doc.id), file_name))
                        uploaded = 0.0
                        S3.Bucket(settings.AWS_OUTPUT_BUCKET).upload_fileobj(r.raw, s3_key, extra_args_img, Callback=cb)
                        print()
                        # S3.Bucket(settings.AWS_OUTPUT_BUCKET).put_object(Key=s3_key, Body=bytes_obj, CacheControl=CACHE_CONTROL, ACL='public-read')
                        s3_thumbnail_url = get_s3_output_url_unsigned(s3_key)
                        doc.s3_thumbnail_url = s3_thumbnail_url
                doc.save()
            except Exception as e:
                print('Error:', e)

