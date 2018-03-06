# coding: utf-8

# Copyright (c) 2015-2016, thumbor-community
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.

from json import loads, dumps
from os.path import join, splitext
from datetime import datetime
from dateutil.tz import tzutc
from hashlib import sha1

from tornado.concurrent import return_future
from thumbor.utils import logger

from .bucket import Bucket

class AwsStorage():
    """
    Base storage class
    """
    @property
    def is_auto_webp(self):
        """
        Determines based on context whether we automatically use webp or not
        :return: Use WebP?
        :rtype: bool
        """
        return self.context.config.AUTO_WEBP and hasattr(self.context, 'request') and self.context.request.accepts_webp

    @property
    def storage(self):
        """
        Instantiates bucket based on configuration
        :return: The bucket
        :rtype: Bucket
        """
        return Bucket(self._get_config('BUCKET'), self.context.config.get('TC_AWS_REGION'),
                      self.context.config.get('TC_AWS_ENDPOINT'))

    def __init__(self, context, config_prefix):
        """
        Constructor
        :param Context context: An instance of thumbor's context
        :param string config_prefix: Prefix used to load configuration values
        """
        self.config_prefix = config_prefix
        self.context = context

    @return_future
    def get(self, path, callback):
        """
        Gets data at path
        :param string path: Path for data
        :param callable callback: Callback function for once the retrieval is done
        """
        file_abspath = self._normalize_path(path)

        self.storage.get(file_abspath, callback=callback)

    @return_future
    def set(self, bytes, abspath, callback=None):
        """
        Stores data at given path
        :param bytes bytes: Data to store
        :param string abspath: Path to store the data at
        :return: Path where the data is stored
        :rtype: string
        """
        metadata = {}

        if self.config_prefix is 'TC_AWS_RESULT_STORAGE' and self.context.config.get('TC_AWS_STORE_METADATA'):
            metadata = dict(self.context.headers)

        self.storage.put(
            abspath,
            bytes,
            metadata=metadata,
            reduced_redundancy=self.context.config.get('TC_AWS_STORAGE_RRS', False),
            encrypt_key=self.context.config.get('TC_AWS_STORAGE_SSE', False),
            callback=callback,
        )

    def remove(self, path):
        """
        Deletes data at path
        :param string path: Path to delete
        :return: Whether deletion is successful or not
        :rtype: bool
        """
        yield self.storage.delete(path)
        return

    @return_future
    def exists(self, path, callback):
        """
        Tells if data exists at given path
        :param string path: Path to check
        :param callable callback: Callback function for once the check is done
        """
        file_abspath = self._normalize_path(path)

        def return_data(file_key):
            if not file_key or self._get_error(file_key):
                callback(False)
            else:
                callback(True)

        self.storage.get(file_abspath, callback=return_data)

    def is_expired(self, key):
        """
        Tells whether key has expired
        :param string key: Path to check
        :return: Whether it is expired or not
        :rtype: bool
        """
        if key and self._get_error(key) is None and 'LastModified' in key:
            expire_in_seconds = self.storage_expiration_seconds

            # Never expire
            if expire_in_seconds is None or expire_in_seconds == 0:
                return False

            timediff = datetime.now(tzutc()) - key['LastModified']

            return timediff.seconds > expire_in_seconds
        else:
            #If our key is bad just say we're expired
            return True

    @return_future
    def last_updated(self, callback):
        """
        Tells when the image has last been updated
        :param callable callback: Callback function for once the retrieval is done
        """
        path = self.context.request.url
        file_abspath = self._normalize_path(path)

        def on_file_fetched(file):
            if not file or self._get_error(file) or self.is_expired(file) or 'LastModified' not in file:
                logger.warn("[AwsStorage] s3 key not found at %s" % file_abspath)
                callback(None)
            else:
                callback(file['LastModified'])

        self.storage.get(file_abspath, callback=on_file_fetched)

    @return_future
    def get_crypto(self, path, callback):
        """
        Retrieves crypto data at path
        :param string path: Path to search for crypto data
        :param callable callback: Callback function for once the retrieval is done
        """
        file_abspath = self._normalize_path(path)
        crypto_path = "%s.txt" % (splitext(file_abspath)[0])

        def return_data(file_key):
            if not file_key or self._get_error(file_key) or self.is_expired(file_key) or 'Body' not in file_key:
                logger.warn("[STORAGE] s3 key not found at %s" % crypto_path)
                callback(None)
            else:
                callback(file_key['Body'])

        self.storage.get(crypto_path, callback=return_data)

    def put_crypto(self, path):
        """
        Stores crypto data at given path
        :param string path: Path to store the data at
        :return: Path where the crypto data is stored
        """
        if not self.context.config.STORES_CRYPTO_KEY_FOR_EACH_IMAGE:
            return

        if not self.context.server.security_key:
            raise RuntimeError("STORES_CRYPTO_KEY_FOR_EACH_IMAGE can't be True if no SECURITY_KEY specified")

        file_abspath = self._normalize_path(path)
        crypto_path = '%s.txt' % splitext(file_abspath)[0]

        self.set(self.context.server.security_key, crypto_path)

        return crypto_path

    @return_future
    def get_detector_data(self, path, callback):
        """
        Retrieves detector data from storage
        :param string path: Path where the data is stored
        :param callable callback: Callback function for once the retrieval is done
        """
        file_abspath = self._normalize_path(path)
        path = '%s.detectors.txt' % splitext(file_abspath)[0]

        def return_data(file_key):
            if not file_key or self._get_error(file_key) or self.is_expired(file_key) or 'Body' not in file_key:
                logger.warn("[AwsStorage] s3 key not found at %s" % path)
                callback(None)
            else:
                callback(loads(file_key['Body'].read()))

        self.storage.get(path, callback=return_data)

    def put_detector_data(self, path, data):
        """
        Stores detector data at given path
        :param string path: Path to store the data at
        :param bytes data:  Data to store
        :return: Path where the data is stored
        :rtype: string
        """
        file_abspath = self._normalize_path(path)

        path = '%s.detectors.txt' % splitext(file_abspath)[0]

        self.set(dumps(data), path)

        return path

    def _get_error(self, response):
        """
        Returns error in response if it exists
        :param dict response: AWS Response
        :return: Error message if present, None otherwise
        :rtype: string
        """
        if 'Error' in response:
            return response['Error']['Message'] if 'Message' in response['Error'] else response['Error']

        return None

    def _handle_error(self, response):
        """
        Logs error if necessary
        :param dict response: AWS Response
        """
        if self._get_error(response):
            logger.warn("[STORAGE] error occured while storing data: %s" % self._get_error(response))

    def _get_config(self, config_key, default=None):
        """
        Retrieve specific config based on prefix
        :param string config_key: Requested config
        :param default: Default value if not found
        :return: Resolved config value
        """
        return getattr(self.context.config, '%s_%s' % (self.config_prefix, config_key))

    def _normalize_path(self, path):
        """
        Adapts path based on configuration (root_path for instance)
        :param string path: Path to adapt
        :return: Adapted path
        :rtype: string
        """
        path = path.lstrip('/')  # Remove leading '/'
        path_segments = [path]

        root_path = self._get_config('ROOT_PATH')
        if root_path and root_path is not '':
            path_segments.insert(0, root_path)

        if self.is_auto_webp:
            path_segments.append("webp")

        if self._should_randomize_key():
            path_segments.insert(0, self._generate_digest(path_segments))

        normalized_path = join(path_segments[0], *path_segments[1:]).lstrip('/') if len(path_segments) > 1 else path_segments[0]
        if normalized_path.endswith('/'):
            normalized_path += self.context.config.TC_AWS_ROOT_IMAGE_NAME

        return normalized_path

    def _should_randomize_key(self):
        return self.context.config.TC_AWS_RANDOMIZE_KEYS

    def _generate_digest(self, segments):
        return sha1(".".join(segments).encode('utf-8')).hexdigest()
