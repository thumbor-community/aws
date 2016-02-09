# coding: utf-8

# Copyright (c) 2015, thumbor-community
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.

import session as session_handler
from tornado_botocore import Botocore
from tornado.concurrent import return_future
from botocore.utils import fix_s3_host
from thumbor.utils import logger


class Bucket(object):
    """
    This handles all communication with AWS API
    """
    _bucket       = None
    _region       = None
    _private_host = None
    _local_cache  = dict()

    def __init__(self, bucket, region, private_host):
        """
        Constructor
        :param string bucket: The bucket name
        :param string region: The AWS API region to use
        :param string private_host: The AWS API VPC host to use
        :return: The created bucket
        """
        self._bucket = bucket
        self._region = region
        self._private_host = private_host

    @return_future
    def get(self, path, callback=None):
        """
        Returns object at given path
        :param string path: Path or 'key' to retrieve AWS object
        :param callable callback: Callback function for once the retrieval is done
        """
        my_session = session_handler.get_session()
        session = Botocore(service='s3', region_name=self._region,
                           operation='GetObject', session=my_session)
        session.call(
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
        session = session_handler.get_session()
        if self._private_host:
            client = session.create_client('s3', region_name=self._region, endpoint_url=self._private_host)
            client.meta.events.unregister('before-sign.s3', fix_s3_host)
        else:
            client = session.create_client('s3', region_name=self._region)

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

        args = dict(
            callback=callback,
            Bucket=self._bucket,
            Key=self._clean_key(path),
            Body=data,
            Metadata=metadata,
            StorageClass=storage_class,
        )

        if encrypt_key:
            args['ServerSideEncryption'] = 'AES256'

        my_session = session_handler.get_session()
        session = Botocore(service='s3', region_name=self._region,
                           operation='PutObject', session=my_session)
        session.call(**args)

    @return_future
    def delete(self, path, callback=None):
        """
        Deletes key at given path
        :param string path: Path or 'key' to delete
        :param callable callback: Called function once done
        """
        my_session = session_handler.get_session()
        session = Botocore(service='s3', region_name=self._region,
                           operation='DeleteObject', session=my_session)
        session.call(
            callback=callback,
            Bucket=self._bucket,
            Key=self._clean_key(path),
        )

    def _clean_key(self, path):
        logger.debug('Cleaning key: {path}'.format(path=path))
        key = path
        while '//' in key:
            logger.debug(key)
            key = key.replace('//', '/')

        if '/' == key[0]:
            key = key[1:]

        logger.debug('Cleansed key: {key}'.format(key=key))
        return key
