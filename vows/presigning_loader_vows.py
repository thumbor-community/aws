# se!/usr/bin/python
# -*- coding: utf-8 -*-

from urlparse import urlparse, parse_qs

from mock import Mock

from pyvows import Vows, expect
from mock import patch

from thumbor.context import Context
from derpconf.config import Config

import boto
from boto.s3.key import Key

from moto import mock_s3_deprecated as mock_s3

from fixtures.storage_fixture import IMAGE_PATH, IMAGE_BYTES

from tc_aws.loaders import presigning_loader

import logging
logging.getLogger('botocore').setLevel(logging.CRITICAL)

s3_bucket = 'thumbor-images-test'

@Vows.batch
class PresigningLoaderVows(Vows.Context):

    class CanLoadImage(Vows.Context):

        @mock_s3
        def topic(self):
            conn = boto.connect_s3()
            bucket = conn.create_bucket(s3_bucket)

            k = Key(bucket)
            k.key = IMAGE_PATH
            k.set_contents_from_string(IMAGE_BYTES)

            conf = Config()
            conf.define('TC_AWS_LOADER_BUCKET', s3_bucket, '')
            conf.define('TC_AWS_LOADER_ROOT_PATH', 'root_path', '')

            return Context(config=conf)

        def should_load_from_s3(self, topic):
            image = yield presigning_loader.load(topic, '/'.join(['root_path', IMAGE_PATH]))
            expect(image).to_equal(IMAGE_BYTES)

    class ValidatesBuckets(Vows.Context):

        @mock_s3
        def topic(self):
            conf = Config()
            conf.define('TC_AWS_ALLOWED_BUCKETS', [], '')

            return Context(config=conf)

        def should_load_from_s3(self, topic):
            image = yield presigning_loader.load(topic, '/'.join([s3_bucket, IMAGE_PATH]))
            expect(image).to_equal(None)

    class HandlesHttpLoader(Vows.Context):

        @mock_s3
        def topic(self):
            conf = Config()
            conf.define('TC_AWS_ENABLE_HTTP_LOADER', True, '')

            return Context(config=conf)

        @patch('thumbor.loaders.http_loader.load_sync')
        def should_redirect_to_http(self, topic, load_sync_patch):
            def callback(*args):
                pass

            presigning_loader.load(topic, 'http://foo.bar', callback)
            expect(load_sync_patch.called).to_be_true()

    class CanBuildPresignedUrl(Vows.Context):

        @Vows.async_topic
        @mock_s3
        def topic(self, callback):
            conf = Config()
            context = Context(config=conf)
            presigning_loader._generate_presigned_url(context, "bucket-name", "some-s3-key", callback)

        def should_generate_presigned_urls(self, topic):
            url = urlparse(topic.args[0])
            expect(url.scheme).to_equal('https')
            expect(url.hostname).to_equal('bucket-name.s3.amazonaws.com')
            expect(url.path).to_equal('/some-s3-key')
            url_params = parse_qs(url.query)
            # We can't test Expires & Signature values as they vary depending on the TZ
            expect(url_params).to_include('Expires')
            expect(url_params).to_include('Signature')
            expect(url_params['AWSAccessKeyId'][0]).to_equal('test-key')
            expect(url_params['x-amz-security-token'][0]).to_equal('test-session-token')
