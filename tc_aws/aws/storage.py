# coding: utf-8

# Copyright (c) 2015-2016, thumbor-community
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.

from os.path import join
from datetime import datetime
from dateutil.tz import tzutc
from hashlib import sha1

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

    async def get(self, path):
        """
        Gets data at path
        :param string path: Path for data
        """
        file_abspath = self._normalize_path(path)

        return await self.storage.get(file_abspath)

    def is_expired(self, key):
        """
        Tells whether key has expired
        :param  key: Path to check
        :return: Whether it is expired or not
        :rtype: bool
        """
        if key and 'LastModified' in key:
            expire_in_seconds = self.storage_expiration_seconds

            # Never expire
            if expire_in_seconds is None or expire_in_seconds == 0:
                return False

            timediff = datetime.now(tzutc()) - key['LastModified']

            return timediff.seconds > expire_in_seconds
        else:
            #If our key is bad just say we're expired
            return True

    async def _put_object(self, object_data, path, metadata=None):
        """
        Stores data at given path
        :param bytes bytes: Data to store
        :param string abspath: Path to store the data at
        :return: Path where the data is stored
        :rtype: string
        """

        return await self.storage.put(
            path,
            object_data,
            metadata=metadata,
            reduced_redundancy=self.context.config.get('TC_AWS_STORAGE_RRS', False),
            encrypt_key=self.context.config.get('TC_AWS_STORAGE_SSE', False),
        )

    def _get_config(self, config_key):
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
