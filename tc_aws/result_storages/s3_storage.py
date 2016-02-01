#coding: utf-8

# Copyright (c) 2015, thumbor-community
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.

from tornado.concurrent import return_future
from thumbor.result_storages import BaseStorage, ResultStorageResult

from ..aws.storage import AwsStorage

from thumbor.utils import logger


class Storage(AwsStorage, BaseStorage):
    """
    S3 Result Storage
    """
    def __init__(self, context):
        """
        Constructor
        :param Context context: Thumbor's context
        """
        BaseStorage.__init__(self, context)
        AwsStorage.__init__(self, context, 'TC_AWS_RESULT_STORAGE')

    def put(self, bytes):
        """
        Stores image
        :param bytes bytes: Data to store
        :return: Path where data is stored
        :rtype: string
        """
        path = self._normalize_path(self.context.request.url)

        self.set(bytes, path)

        return path

    @return_future
    def get(self, path=None, callback=None):
        """
        Retrieves data
        :param string path: Path to load data (defaults to request URL)
        :param callable callback: Method called once done
        """
        if path is None:
            path = self.context.request.url

        def return_result(key):
            if key is None or self._get_error(key) or self.is_expired(key):
                callback(None)
            else:
                result = ResultStorageResult()
                result.buffer     = key['Body'].read()
                result.successful = True
                result.metadata   = key.copy()
                result.metadata.pop('Body')

                logger.debug(str(result.metadata))

                callback(result)

        super(Storage, self).get(path, callback=return_result)
