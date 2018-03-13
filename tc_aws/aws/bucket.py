# coding: utf-8

# Copyright (c) 2015, thumbor-community
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.

import botocore.session
from botocore.utils import fix_s3_host
from tornado_botocore.base import Botocore
from tornado.concurrent import return_future
from thumbor.utils import logger
from thumbor.engines import BaseEngine


class Bucket(object):
    """
    This handles all communication with AWS API
    """
    def __init__(self, bucket, region, endpoint):
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

        self._session = None
        self._get_client = None
        self._put_client = None
        self._delete_client = None

    @property
    def session(self):
        if self._session is None:
            self._session = botocore.session.get_session()
            if self._endpoint is not None:
                self._session.unregister('before-sign.s3', fix_s3_host)
        return self._session

    @property
    def get_client(self):
        if self._get_client is None:
            self._get_client = Botocore(service='s3', region_name=self._region,
                                        operation='GetObject', session=self.session,
                                        endpoint_url=self._endpoint)

        return self._get_client

    @property
    def put_client(self):
        if self._put_client is None:
            self._put_client = Botocore(service='s3', region_name=self._region,
                                        operation='PutObject', session=self.session,
                                        endpoint_url=self._endpoint)

        return self._put_client

    @property
    def delete_client(self):
        if self._delete_client is None:
            self._delete_client = Botocore(service='s3', region_name=self._region,
                                           operation='DeleteObject', session=self.session,
                                           endpoint_url=self._endpoint)

        return self._delete_client

    @return_future
    def get(self, path, callback=None):
        """
        Returns object at given path
        :param string path: Path or 'key' to retrieve AWS object
        :param callable callback: Callback function for once the retrieval is done
        """
        self.get_client.call(
            callback=callback,
            Bucket=self._bucket,
            Key=self._clean_key(path),
        )

    @return_future
    def get_url(self, path, method='GET', expiry=3600, callback=None):
        """
        Generates the presigned url for given key & methods
        :param string path: Path or 'key' for requested object
        :param string method: Method for requested URL
        :param int expiry: URL validity time
        :param callable callback: Called function once done
        """
        client = self.session.create_client('s3', region_name=self._region, endpoint_url=self._endpoint)

        url = client.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': self._bucket,
                'Key':    self._clean_key(path),
            },
            ExpiresIn=expiry,
            HttpMethod=method,
        )

        callback(url)

    @return_future
    def put(self, path, data, metadata={}, reduced_redundancy=False, encrypt_key=False, callback=None):
        """
        Stores data at given path
        :param string path: Path or 'key' for created/updated object
        :param bytes data: Data to write
        :param dict metadata: Metadata to store with this data
        :param bool reduced_redundancy: Whether to reduce storage redundancy or not?
        :param bool encrypt_key: Encrypt data?
        :param callable callback: Called function once done
        """
        storage_class = 'REDUCED_REDUNDANCY' if reduced_redundancy else 'STANDARD'
        content_type = BaseEngine.get_mimetype(data) or 'application/octet-stream'

        args = dict(
            callback=callback,
            Bucket=self._bucket,
            Key=self._clean_key(path),
            Body=data,
            ContentType=content_type,
            Metadata=metadata,
            StorageClass=storage_class,
        )

        if encrypt_key:
            args['ServerSideEncryption'] = 'AES256'

        self.put_client.call(**args)

    @return_future
    def delete(self, path, callback=None):
        """
        Deletes key at given path
        :param string path: Path or 'key' to delete
        :param callable callback: Called function once done
        """
        self.put_client.call(
            callback=callback,
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
