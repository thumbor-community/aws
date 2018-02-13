#se!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from dateutil.tz import tzutc

from hashlib import sha1

from pyvows import Vows, expect

from thumbor.context import Context
from tc_aws import Config
from fixtures.storage_fixture import IMAGE_BYTES, get_server

from boto.s3.connection import S3Connection
from moto import mock_s3_deprecated as mock_s3

from tc_aws.result_storages.s3_storage import Storage

import logging
logging.getLogger('botocore').setLevel(logging.CRITICAL)

s3_bucket = 'thumbor-images-test'


class Request(object):
    url = None


@Vows.batch
class S3ResultStorageVows(Vows.Context):

    class CanStoreImage(Vows.Context):
        @Vows.async_topic
        @mock_s3
        def topic(self, callback):
            self.conn = S3Connection()
            self.conn.create_bucket(s3_bucket)

            config = Config(TC_AWS_RESULT_STORAGE_BUCKET=s3_bucket)
            ctx = Context(config=config, server=get_server('ACME-SEC'))
            ctx.request = Request
            ctx.request.url = 'my-image.jpg'

            storage = Storage(ctx)

            storage.put(IMAGE_BYTES, callback=callback)

        def should_be_in_catalog(self, topic):
            expect(topic.args[0]).to_equal('my-image.jpg')

    class CanStoreImageRandomly(Vows.Context):
        @Vows.async_topic
        @mock_s3
        def topic(self, callback):
            self.conn = S3Connection()
            self.conn.create_bucket(s3_bucket)

            config = Config(TC_AWS_RESULT_STORAGE_BUCKET=s3_bucket, TC_AWS_RANDOMIZE_KEYS=True)
            ctx = Context(config=config, server=get_server('ACME-SEC'))
            ctx.request = Request
            ctx.request.url = 'my-image.jpg'

            storage = Storage(ctx)

            storage.put(IMAGE_BYTES, callback=callback)

        def should_be_in_catalog(self, topic):
            expect(topic.args[0]).to_equal([sha1('my-image.jpg'.encode('utf8')).hexdigest(), 'my-image.jpg'].join('/'))

    class CanGetImage(Vows.Context):
        @Vows.async_topic
        @mock_s3
        def topic(self, callback):
            self.conn = S3Connection()
            self.conn.create_bucket(s3_bucket)

            config = Config(TC_AWS_RESULT_STORAGE_BUCKET=s3_bucket)
            ctx = Context(config=config, server=get_server('ACME-SEC'))
            ctx.request = Request
            ctx.request.url = 'my-image-2.jpg'

            storage = Storage(ctx)
            storage.put(IMAGE_BYTES)

            storage.get(callback=callback)

        def should_have_proper_bytes(self, topic):
            expect(topic.args[0]).not_to_be_null()
            expect(topic.args[0]).not_to_be_an_error()
            expect(topic.args[0]).to_equal(IMAGE_BYTES)

    class CanGetRandomizedImage(Vows.Context):
        @Vows.async_topic
        @mock_s3
        def topic(self, callback):
            self.conn = S3Connection()
            self.conn.create_bucket(s3_bucket)

            config = Config(TC_AWS_RESULT_STORAGE_BUCKET=s3_bucket, TC_AWS_RANDOMIZE_KEYS=True)
            ctx = Context(config=config, server=get_server('ACME-SEC'))
            ctx.request = Request
            ctx.request.url = 'my-image-2.jpg'

            storage = Storage(ctx)
            storage.put(IMAGE_BYTES)

            storage.get(callback=callback)

        def should_have_proper_bytes(self, topic):
            expect(topic.args[0]).not_to_be_null()
            expect(topic.args[0]).not_to_be_an_error()
            expect(topic.args[0]).to_equal(IMAGE_BYTES)

    class CanGetImageWithMetadata(Vows.Context):
        @Vows.async_topic
        @mock_s3
        def topic(self, callback):
            self.conn = S3Connection()
            self.conn.create_bucket(s3_bucket)

            config = Config(TC_AWS_RESULT_STORAGE_BUCKET=s3_bucket, TC_AWS_STORE_METADATA=True)
            ctx = Context(config=config, server=get_server('ACME-SEC'))
            ctx.headers = {'Content-Type': 'image/webp', 'Some-Other-Header': 'doge-header'}
            ctx.request = Request
            ctx.request.url = 'my-image-meta.jpg'

            storage = Storage(ctx)
            storage.put(IMAGE_BYTES)

            file_abspath = storage._normalize_path(ctx.request.url)
            storage.storage.get(file_abspath, callback=callback)

        def should_have_proper_bytes(self, topic):
            expect(topic.args[0].content_type).to_include('image/webp')
            expect(topic.args[0].metadata).to_include('some-other-header')
            expect(topic.args[0].content_type).to_equal(IMAGE_BYTES)

    class ExpiredVows(Vows.Context):
        class WhenExpiredEnabled(Vows.Context):
            def topic(self):
                return Storage(Context(config=Config(RESULT_STORAGE_EXPIRATION_SECONDS=3600)))

            def should_check_invalid_key(self, topic):
                expect(topic.is_expired(None)).to_be_true()
                expect(topic.is_expired(False)).to_be_true()
                expect(topic.is_expired(dict())).to_be_true()
                expect(topic.is_expired({'Error': ''})).to_be_true()

            def should_tell_when_not_expired(self, topic):
                key = {
                    'LastModified': datetime.now(tzutc()),
                    'Body': 'foobar',
                }
                expect(topic.is_expired(key)).to_be_false()

            def should_tell_when_expired(self, topic):
                key = {
                    'LastModified': (datetime.now(tzutc()) - timedelta(seconds=3601)),
                    'Body': 'foobar',
                }
                expect(topic.is_expired(key)).to_be_true()

        class WhenExpiredDisabled(Vows.Context):
            def topic(self):
                return Storage(Context(config=Config(RESULT_STORAGE_EXPIRATION_SECONDS=0)))

            def should_not_tell_when_expired(self, topic):
                key = {
                    'LastModified': (datetime.now(tzutc()) - timedelta(seconds=3601)),
                    'Body': 'foobar',
                }
                expect(topic.is_expired(key)).to_be_false()
    class HandlesStoragePrefix(Vows.Context):
        @mock_s3
        def topic(self):
            self.conn = S3Connection()
            self.conn.create_bucket(s3_bucket)

            config = Config(TC_AWS_RESULT_STORAGE_BUCKET=s3_bucket, TC_AWS_RESULT_STORAGE_ROOT_PATH='tata')
            ctx = Context(config=config, server=get_server('ACME-SEC'))

            storage = Storage(ctx)

            return storage._normalize_path('toto')

        def should_return_the_same(self, topic):
            expect(topic).to_equal("tata/toto")
