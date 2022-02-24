# coding: utf-8

# Copyright (c) 2015, thumbor-community
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.

import aiobotocore
from botocore.client import Config
from thumbor.utils import logger
from thumbor.engines import BaseEngine


class Bucket(object):
    _client = None
    _instances = {}

    @staticmethod
    def __new__(cls, bucket, region, endpoint, *args, **kwargs):
        key = (bucket, region, endpoint) + args + tuple(kwargs.items())

        if not cls._instances.get(key):
            cls._instances[key] = super(Bucket, cls).__new__(cls)

        return cls._instances[key]

    """
    This handles all communication with AWS API
    """
    def __init__(self, bucket, region, endpoint, max_retry=None):
        """
        Constructor
        :param string bucket: The bucket name
        :param string region: The AWS API region to use
        :param string endpoint: A specific endpoint to use
        :return: The created bucket
        """
        self._bucket = bucket

        config = None
        if max_retry is not None:
            config = Config(
                retries=dict(
                    max_attempts=max_retry
                )
            )

        if self._client is None:
            self._client = aiobotocore.get_session().create_client(
                's3',
                region_name=region,
                endpoint_url=endpoint,
                config=config
            )

    async def exists(self, path):
        """
        Checks if an object exists at a given path
        :param string path: Path or 'key' to retrieve AWS object
        """
        try:
            await self._client.head_object(
                Bucket=self._bucket,
                Key=self._clean_key(path),
            )
        except Exception:
            return False
        return True

    async def get(self, path):
        """
        Returns object at given path
        :param string path: Path or 'key' to retrieve AWS object
        """

        return await self._client.get_object(
            Bucket=self._bucket,
            Key=self._clean_key(path),
        )

    async def get_url(self, path, method='GET', expiry=3600):
        """
        Generates the presigned url for given key & methods
        :param string path: Path or 'key' for requested object
        :param string method: Method for requested URL
        :param int expiry: URL validity time
        """

        url = await self._client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': self._bucket,
                'Key': self._clean_key(path),
            },
            ExpiresIn=expiry,
            HttpMethod=method,
        )

        return url

    async def put(self, path, data, metadata=None, reduced_redundancy=False, encrypt_key=False):
        """
        Stores data at given path
        :param string path: Path or 'key' for created/updated object
        :param bytes data: Data to write
        :param dict metadata: Metadata to store with this data
        :param bool reduced_redundancy: Whether to reduce storage redundancy or not?
        :param bool encrypt_key: Encrypt data?
        """
        storage_class = 'REDUCED_REDUNDANCY' if reduced_redundancy else 'STANDARD'
        content_type = BaseEngine.get_mimetype(data) or 'application/octet-stream'

        args = dict(
            Bucket=self._bucket,
            Key=self._clean_key(path),
            Body=data,
            ContentType=content_type,
            StorageClass=storage_class,
        )

        if encrypt_key:
            args['ServerSideEncryption'] = 'AES256'

        if metadata is not None:
            args['Metadata'] = metadata

        return await self._client.put_object(**args)

    async def delete(self, path):
        """
        Deletes key at given path
        :param string path: Path or 'key' to delete
        """
        return await self._client.delete_object(
            Bucket=self._bucket,
            Key=self._clean_key(path),
        )

    def _clean_key(self, path):
        logger.debug('Cleaning key: {path!r}'.format(path=path))
        key = path
        while '//' in key:
            logger.debug(key)
            key = key.replace('//', '/')

        if '/' == key[0]:
            key = key[1:]

        logger.debug('Cleansed key: {key!r}'.format(key=key))
        return key
