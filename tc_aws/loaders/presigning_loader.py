# coding: utf-8

from tornado.concurrent import return_future

import thumbor.loaders.http_loader as http_loader
import botocore.session
from botocore.client import Config

import urllib2

@return_future
def load(context, url, callback):
    """
    Loads image
    :param Context context: Thumbor's context
    :param string url: Path to load
    :param callable callback: Callback method once done
    """
    if _use_http_loader(context, url):
        http_loader.load_sync(context, url, callback, normalize_url_func=http_loader._normalize_url)
    else:
        bucket, key = _get_bucket_and_key(context, url)

        if _validate_bucket(context, bucket):
            def on_url_generated(generated_url):
                def noop(url):
                    return url
                http_loader.load_sync(context, generated_url, callback, normalize_url_func=noop)

            _generate_presigned_url(context, bucket, key, on_url_generated)
        else:
            callback(None)


@return_future
def get_url(bucket, region, path, config=None, endpoint_url=None, method='GET', expiry=3600, callback=None):
    """
    Generates the presigned url for given key & methods
    :param string path: Path or 'key' for requested object
    :param string method: Method for requested URL
    :param int expiry: URL validity time
    :param callable callback: Called function once done
    """
    session = botocore.session.get_session()

    if config is not None:
      config = Config(**config)

    client  = session.create_client('s3', region_name=region, endpoint_url=endpoint_url, config=config)

    url = client.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': bucket,
            'Key':    _clean_key(path),
        },
        ExpiresIn=expiry,
        HttpMethod=method,
    )

    callback(url)

@return_future
def _generate_presigned_url(context, bucket, key, callback):
    """
    Generates presigned URL
    :param Context context: Thumbor's context
    :param string bucket: Bucket name
    :param string key: Path to get URL for
    :param callable callback: Callback method once done
    """
    get_url(bucket, context.config.get('TC_AWS_REGION'), key, config=context.config.get('TC_AWS_CONFIG'), endpoint_url=context.config.get('TC_AWS_ENDPOINT_URL'), callback=callback)

def _clean_key(path):
    key = path
    while '//' in key:
        key = key.replace('//', '/')

    if '/' == key[0]:
        key = key[1:]

    return key

def _get_bucket_and_key(context, url):
    """
    Returns bucket and key from url
    :param Context context: Thumbor's context
    :param string url: The URL to parse
    :return: A tuple with the bucket and the key detected
    :rtype: tuple
    """
    url = urllib2.unquote(url)

    bucket = context.config.get('TC_AWS_LOADER_BUCKET')
    if bucket is None:
        bucket = _get_bucket(url)
        url = '/'.join(url.lstrip('/').split('/')[1:])

    key = _get_key(url, context)

    return bucket, key

def _get_bucket(url):
    """
    Retrieves the bucket based on the URL
    :param string url: URL to parse
    :return: bucket name
    :rtype: string
    """
    url_by_piece = url.lstrip("/").split("/")

    return url_by_piece[0]

def _get_key(path, context):
    """
    Retrieves key from path
    :param string path: Path to analyze
    :param Context context: Thumbor's context
    :return: Extracted key
    :rtype: string
    """
    root_path = context.config.get('TC_AWS_LOADER_ROOT_PATH')
    return '/'.join([root_path, path]) if root_path is not '' else path

def _validate_bucket(context, bucket):
    """
    Checks that bucket is allowed
    :param Context context: Thumbor's context
    :param string bucket: Bucket name
    :return: Whether bucket is allowed or not
    :rtype: bool
    """
    allowed_buckets = context.config.get('TC_AWS_ALLOWED_BUCKETS', default=None)
    return not allowed_buckets or bucket in allowed_buckets

def _use_http_loader(context, url):
    """
    Should we use HTTP Loader with given path? Based on configuration as well.
    :param Context context: Thumbor's context
    :param string url: URL to analyze
    :return: Whether we should use HTTP Loader or not
    :rtype: bool
    """
    enable_http_loader = context.config.get('TC_AWS_ENABLE_HTTP_LOADER', default=False)
    return enable_http_loader and url.startswith('http')
