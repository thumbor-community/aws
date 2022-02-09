#coding: utf-8

# Copyright (c) 2015-2016, thumbor-community
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.
from botocore.exceptions import BotoCoreError, ClientError
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
        self.storage_expiration_seconds = context.config.get('RESULT_STORAGE_EXPIRATION_SECONDS', 3600)

    async def put(self, image_bytes):
        """
        Stores image
        :param bytes image_bytes: Data to store
        """
        path = self._normalize_path(self.context.request.url)

        metadata = {}

        if self.context.config.get('TC_AWS_STORE_METADATA'):
            metadata = dict(self.context.headers)

        try:
            return await self._put_object(image_bytes, path, metadata)
        except BotoCoreError as err:
            logger.exception('Unable to store result image object: %s', err)
            return None

    async def get(self, path = None):
        """
        Retrieves data
        :param string path: Path to load data (defaults to request URL)
        """
        if path is None:
            path = self.context.request.url


        try:
            key = await super(Storage, self).get(path)
        except ClientError:
            return None

        if key is None or self.is_expired(key):
            return None

        result = ResultStorageResult()
        result.buffer = await key['Body'].read()
        result.successful = True

        result.metadata = {
            "LastModified": key.get('LastModified'),
            "ContentLength": key.get('ContentLength', None),
            "ContentType": key.get('ContentType'),
        }

        result.metadata.update(key.get('Metadata'))

        logger.debug(str(result.metadata))

        return result
