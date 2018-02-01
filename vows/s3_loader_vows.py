# -*- coding: utf-8 -*-
from mock import Mock

from pyvows import Vows, expect
from mock import patch, MagicMock

from thumbor.context import Context
from derpconf.config import Config

import boto
from boto.s3.key import Key

from moto import mock_s3_deprecated as mock_s3

from fixtures.storage_fixture import IMAGE_PATH, IMAGE_BYTES

from tc_aws.loaders import s3_loader

import logging
logging.getLogger('botocore').setLevel(logging.CRITICAL)

s3_bucket = 'thumbor-images-test'

@Vows.batch
class S3LoaderVows(Vows.Context):

    class CanLoadImage(Vows.Context):
        @Vows.async_topic
        @mock_s3
        def topic(self, callback):
            conn = boto.connect_s3()
            bucket = conn.create_bucket(s3_bucket)

            k = Key(bucket)
            k.key = '/'.join(['root_path', IMAGE_PATH])
            k.set_contents_from_string(IMAGE_BYTES)

            conf = Config()
            conf.define('TC_AWS_LOADER_BUCKET', s3_bucket, '')
            conf.define('TC_AWS_LOADER_ROOT_PATH', 'root_path', '')

            context = Context(config=conf)

            s3_loader.load(context, IMAGE_PATH, callback)

        def should_load_from_s3(self, data):
            image = data.args[0]
            expect(image).to_equal(IMAGE_BYTES)

    class ValidatesBuckets(Vows.Context):
        @Vows.async_topic
        @mock_s3
        def topic(self, callback):
            conf = Config()
            conf.define('TC_AWS_ALLOWED_BUCKETS', [], '')

            context = Context(config=conf)
            s3_loader.load(context, '/'.join([s3_bucket, IMAGE_PATH]), callback)

        def should_load_from_s3(self, data):
            image = data.args[0]
            expect(image).to_equal(None)

    class HandlesHttpLoader(Vows.Context):

        def topic(self):
            conf = Config()
            conf.define('TC_AWS_ENABLE_HTTP_LOADER', True, '')

            return Context(config=conf)

        @patch('thumbor.loaders.http_loader.load_sync')
        def should_redirect_to_http(self, topic, load_sync_patch):
            def callback(*args):
                pass

            s3_loader.load(topic, 'http://foo.bar', callback)
            expect(load_sync_patch.called).to_be_true()

        @mock_s3
        @patch('thumbor.loaders.http_loader.load_sync')
        def should_not_redirect_to_http_if_not_prefixed_with_scheme(self, topic, load_sync_patch):
            def callback(*args):
                pass

            s3_loader.load(topic, 'foo.bar', callback)
            expect(load_sync_patch.called).to_be_false()

    class HandleDataFuncLoader(Vows.Context):

        def topic(self):

            conf = Config()
            conf.define('TC_AWS_MAX_RETRIES', 3, '')
            return Context(config=conf)

        def should_call_twice(self, topic):

            def callback(*args, **kwargs):
                pass

            file_key = {
                'Error': 'Error',
                'ResponseMetadata': {
                    'HTTPStatusCode': 502
                }
            }

            self.call_count = 0
            def get(key, callback=None):
                self.call_count += 1
                callback(file_key)

            mock_bucket_loader = MagicMock()
            mock_bucket_loader.get = get
            func = s3_loader.HandleDataFunc.as_func(
                '/'.join([s3_bucket, IMAGE_PATH]),
                callback=callback,
                bucket_loader=mock_bucket_loader,
                context=topic
            )

            func(file_key)
            expect(self.call_count).to_equal(3)
