# coding: utf-8

# Copyright (c) 2015, thumbor-community
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.

import aiobotocore.session
from botocore.client import Config
from thumbor.utils import logger
from thumbor.engines import BaseEngine


class Bucket(object):
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
        self._region = region
        self._endpoint = endpoint
        
        self._config = None
        if max_retry is not None:
            self._config = Config(
                retries=dict(
                    max_attempts=max_retry
                )
            )
        
        self._session = aiobotocore.session.get_session()

    def _create_client(self):
        """Create and return a client context manager"""
        return self._session.create_client(
            's3',
            region_name=self._region,
            endpoint_url=self._endpoint,
            config=self._config
        )

    async def exists(self, path):
        """
        Checks if an object exists at a given path
        :param string path: Path or 'key' to retrieve AWS object
        """
        try:
            async with self._create_client() as client:
                await client.head_object(
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
        async with self._create_client() as client:
            return await client.get_object(
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
        async with self._create_client() as client:
            url = await client.generate_presigned_url(
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

        async with self._create_client() as client:
            return await client.put_object(**args)

    async def delete(self, path):
        """
        Deletes key at given path
        :param string path: Path or 'key' to delete
        """
        async with self._create_client() as client:
            return await client.delete_object(
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
