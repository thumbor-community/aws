# coding: utf-8

# Copyright (c) 2015, thumbor-community
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.

import thumbor.loaders.http_loader as http_loader
from thumbor.utils import logger
from thumbor.loaders import LoaderResult

from tornado.concurrent import return_future

from . import *
from ..aws.bucket import Bucket

def validate(context, url, normalize_url_func=http_loader._normalize_url):
    return _validate(context, url, normalize_url_func)

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
        return

    bucket, key = _get_bucket_and_key(context, url)

    if not _validate_bucket(context, bucket):
        result = LoaderResult(successful=False,
                              error=LoaderResult.ERROR_NOT_FOUND)
        callback(result)
        return

    bucket_loader = Bucket(bucket, context.config.get('TC_AWS_REGION'),
                           context.config.get('TC_AWS_ENDPOINT'))

    handle_data = HandleDataFunc.as_func(key,
                                         callback=callback,
                                         bucket_loader=bucket_loader,
                                         context=context)

    bucket_loader.get(key, callback=handle_data)


class HandleDataFunc(object):

    def __init__(self, key, callback=None,
                 bucket_loader=None, context=None):
        self.key = key
        self.bucket_loader = bucket_loader
        self.callback = callback
        self.context = context
        self.limit_max_retries = context.config.get('TC_AWS_MAX_RETRIES')
        self.max_retries_counter = 0

    @classmethod
    def as_func(cls, *init_args, **init_kwargs):
        """
            Method to transform this class to a callback function
            that will use for getObject from s3
        """

        def handle_data(file_key):
            instance = cls(*init_args, **init_kwargs)
            instance.dispatch(file_key)

        handle_data.init_args = init_args
        handle_data.init_kwargs = init_kwargs

        return handle_data

    def __increment_retry_counter(self):
        self.max_retries_counter = self.max_retries_counter + 1

    def dispatch(self, file_key):
        """ Callback method for getObject from s3 """
        if not file_key or 'Error' in file_key or 'Body' not in file_key:

            logger.error(
                "ERROR retrieving image from S3 {0}: {1}".
                format(self.key, str(file_key)))

            # If we got here, there was a failure.
            # We will return 404 if S3 returned a 404, otherwise 502.
            result = LoaderResult()
            result.successful = False

            if not file_key:
                result.error = LoaderResult.ERROR_UPSTREAM
                self.callback(result)
                return

            response_metadata = file_key.get('ResponseMetadata', {})
            status_code = response_metadata.get('HTTPStatusCode')

            if status_code == 404:
                result.error = LoaderResult.ERROR_NOT_FOUND
                self.callback(result)
                return

            if self.max_retries_counter < self.limit_max_retries:
                self.__increment_retry_counter()
                self.bucket_loader.get(self.key,
                                       callback=self.dispatch)
            else:
                result.error = LoaderResult.ERROR_UPSTREAM
                self.callback(result)
        else:
            self.callback(file_key['Body'].read())
