# coding: utf-8

# Copyright (c) 2015, thumbor-community
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.

from tornado.concurrent import return_future

import thumbor.loaders.http_loader as http_loader

from . import *
from ..aws.bucket import Bucket

@return_future
def _generate_presigned_url(context, bucket, key, callback):
    """
    Generates presigned URL
    :param Context context: Thumbor's context
    :param string bucket: Bucket name
    :param string key: Path to get URL for
    :param callable callback: Callback method once done
    """
    Bucket(bucket, context.config.get('TC_AWS_REGION'), context.config.get('TC_AWS_PRIVATE_HOST')).get_url(key, callback=callback)


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
                http_loader.load_sync(context, generated_url, callback, normalize_url_func=http_loader._normalize_url)

            _generate_presigned_url(context, bucket, key, on_url_generated)
        else:
            callback(None)
