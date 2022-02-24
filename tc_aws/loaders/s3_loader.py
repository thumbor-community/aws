# coding: utf-8

# Copyright (c) 2015, thumbor-community
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.
from urllib.parse import unquote

import thumbor.loaders.http_loader as http_loader
from botocore.exceptions import ClientError
from thumbor.utils import logger
from thumbor.loaders import LoaderResult

from ..aws.bucket import Bucket


async def load(context, url):
    """
    Loads image
    :param Context context: Thumbor's context
    :param string url: Path to load
    """
    if _use_http_loader(context, url):
        return await http_loader.load(context, url)

    bucket, key = _get_bucket_and_key(context, url)

    if not _validate_bucket(context, bucket):
        result = LoaderResult(successful=False,
                              error=LoaderResult.ERROR_NOT_FOUND)
        return result

    loader = Bucket(
        bucket,
        context.config.get('TC_AWS_REGION'),
        context.config.get('TC_AWS_ENDPOINT'),
        context.config.get('TC_AWS_MAX_RETRY')
    )

    result = LoaderResult()

    try:
        file_key = await loader.get(key)
    except ClientError as err:
        logger.error(
            "ERROR retrieving image from S3 {0}: {1}".
                format(key, str(err.response)))

        # If we got here, there was a failure.
        # We will return 404 if S3 returned a 404, otherwise 502.
        result.successful = False

        if not err.response:
            result.error = LoaderResult.ERROR_UPSTREAM
            return result

        status_code = err.response.get('ResponseMetadata', {}).get('HTTPStatusCode')

        if status_code == 404:
            result.error = LoaderResult.ERROR_NOT_FOUND
            return result

        result.error = LoaderResult.ERROR_UPSTREAM
        return result

    result.successful = True
    async with file_key['Body'] as stream:
        result.buffer = await stream.read()

    result.metadata.update(
        size=file_key['ContentLength'],
        updated_at=file_key['LastModified'],
    )

    return result


def _get_bucket_and_key(context, url):
    """
    Returns bucket and key from url
    :param Context context: Thumbor's context
    :param string url: The URL to parse
    :return: A tuple with the bucket and the key detected
    :rtype: tuple
    """
    url = unquote(url)

    bucket = context.config.get('TC_AWS_LOADER_BUCKET')
    if not bucket:
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
