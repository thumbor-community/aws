#se!/usr/bin/python
# -*- coding: utf-8 -*-

from pyvows import Vows, expect

from datetime import datetime, timedelta
from dateutil.tz import tzutc

from thumbor.context import Context, RequestParameters
from thumbor.config import Config
from fixtures.storage_fixture import IMAGE_URL, IMAGE_BYTES, get_server

from boto.s3.connection import S3Connection
from moto import mock_s3_deprecated as mock_s3

from tc_aws.storages.s3_storage import Storage

import logging
logging.getLogger('botocore').setLevel(logging.CRITICAL)

s3_bucket = 'thumbor-images-test'

@Vows.batch
class S3StorageVows(Vows.Context):

    class CanStoreImage(Vows.Context):
        @Vows.async_topic
        @mock_s3
        def topic(self, callback):
            self.conn = S3Connection()
            self.conn.create_bucket(s3_bucket)

            thumborId = IMAGE_URL % '1'
            config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket)
            storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
            storage.put(thumborId, IMAGE_BYTES)
            storage.get(thumborId, callback=callback)

        def should_be_in_catalog(self, topic):
            expect(topic.args[0]).not_to_be_null()
            expect(topic.args[0]).not_to_be_an_error()
            expect(topic.args[0]).to_equal(IMAGE_BYTES)

    class CanGetImage(Vows.Context):
        @Vows.async_topic
        @mock_s3
        def topic(self, callback):
            self.conn = S3Connection()
            self.conn.create_bucket(s3_bucket)

            config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket)
            storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
            storage.put(IMAGE_URL % '2', IMAGE_BYTES)
            storage.get(IMAGE_URL % '2', callback=callback)

        def should_not_be_null(self, topic):
            expect(topic.args[0]).not_to_be_null()
            expect(topic.args[0]).not_to_be_an_error()

        def should_have_proper_bytes(self, topic):
            expect(topic.args[0]).to_equal(IMAGE_BYTES)

    class CanGetImageExistance(Vows.Context):
        @Vows.async_topic
        @mock_s3
        def topic(self, callback):
            self.conn = S3Connection()
            self.conn.create_bucket(s3_bucket)

            config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket)
            storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
            storage.put(IMAGE_URL % '3', IMAGE_BYTES)
            storage.exists(IMAGE_URL % '3', callback=callback)

        def should_exists(self, topic):
            expect(topic.args[0]).to_equal(True)

    class CanGetImageInexistance(Vows.Context):
        @Vows.async_topic
        @mock_s3
        def topic(self, callback):
            self.conn = S3Connection()
            self.conn.create_bucket(s3_bucket)

            config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket)
            storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
            storage.exists(IMAGE_URL % '9999', callback)

        def should_not_exists(self, topic):
            expect(topic.args[0]).to_equal(False)

    class CanRemoveImage(Vows.Context):
        @Vows.async_topic
        @mock_s3
        def topic(self, callback):
            self.conn = S3Connection()
            self.conn.create_bucket(s3_bucket)

            config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket)
            storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
            storage.put(IMAGE_URL % '4', IMAGE_BYTES)   # 1: we put the image

            def check_created(created):
                expect(created).to_equal(True) # 2.1: assertion...

                def once_removed(rm):
                    storage.exists(IMAGE_URL % '4', callback=callback) #4: we check if the image exists

                storage.remove(IMAGE_URL % '4', callback=once_removed) # 3: we delete it

            storage.exists(IMAGE_URL % '4', callback=check_created) # 2: we check it exists

        def should_be_put_and_removed(self, topic):
            expect(topic.args[0]).to_equal(False)   # 4.1: assertion...

    class CanRemovethenPutImage(Vows.Context):
        @Vows.async_topic
        @mock_s3
        def topic(self, callback):
            self.conn = S3Connection()
            self.conn.create_bucket(s3_bucket)

            config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket)
            storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
            storage.put(IMAGE_URL % '5', IMAGE_BYTES)   # 1: we put the image

            def check_created(created):
                expect(created).to_equal(True) # 2.1: assertion...

                def once_removed(rm):

                    def check_created_2(exists):
                        expect(exists).to_equal(True) # 4.1: assertion...

                        storage.put(IMAGE_URL % '5')    # 5: we re-put it
                        storage.exists(IMAGE_URL % '5', callback=callback) #6: we check its existance again

                    storage.exists(IMAGE_URL % '5', callback=check_created_2) #4: we check if the image exists

                storage.remove(IMAGE_URL % '5', callback=once_removed) # 3: we delete it

            storage.exists(IMAGE_URL % '5', callback=check_created) # 2: we check it exists

        def should_be_put_and_removed(self, topic):
            expect(topic.args[0]).to_equal(True)

    class CanReturnPath(Vows.Context):
        @mock_s3
        def topic(self):
            self.conn = S3Connection()
            self.conn.create_bucket(s3_bucket)

            config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket)
            storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
            return storage.resolve_original_photo_path("toto")

        def should_return_the_same(self, topic):
            expect(topic).to_equal("toto")

    class HandlesStoragePrefix(Vows.Context):
        @mock_s3
        def topic(self):
            self.conn = S3Connection()
            self.conn.create_bucket(s3_bucket)

            config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket, TC_AWS_STORAGE_ROOT_PATH='tata')
            storage = Storage(Context(config=config, server=get_server('ACME-SEC')))

            return storage._normalize_path('toto')

        def should_return_the_same(self, topic):
            expect(topic).to_equal("tata/toto")

    class ShouldNormalize(Vows.Context):
        def topic(self):
            config = Config(TC_AWS_STORAGE_ROOT_PATH='')
            return Storage(Context(config=config))

        def should_normalize_slash(self, topic):
            expect(topic._normalize_path('/test')).to_equal('test')
            expect(topic._normalize_path('/test/')).to_equal('test/root_image')
            expect(topic._normalize_path('/test/image.png')).to_equal('test/image.png')

    class CryptoVows(Vows.Context):
        class RaisesIfInvalidConfig(Vows.Context):
            @Vows.capture_error
            @mock_s3
            def topic(self):
                self.conn = S3Connection()
                self.conn.create_bucket(s3_bucket)

                config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket, STORES_CRYPTO_KEY_FOR_EACH_IMAGE=True)
                storage = Storage(Context(config=config, server=get_server('')))
                storage.put(IMAGE_URL % '9999', IMAGE_BYTES)
                storage.put_crypto(IMAGE_URL % '9999')

            def should_be_an_error(self, topic):
                expect(topic).to_be_an_error_like(RuntimeError)
                expect(topic).to_have_an_error_message_of("STORES_CRYPTO_KEY_FOR_EACH_IMAGE can't be True if no SECURITY_KEY specified")

        class GettingCryptoForANewImageReturnsNone(Vows.Context):
            @Vows.async_topic
            @mock_s3
            def topic(self, callback):
                self.conn = S3Connection()
                self.conn.create_bucket(s3_bucket)

                config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket, STORES_CRYPTO_KEY_FOR_EACH_IMAGE=True)
                storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
                storage.get_crypto(IMAGE_URL % '9999', callback=callback)

            def should_be_null(self, topic):
                expect(topic.args[0]).to_be_null()

        class DoesNotStoreIfConfigSaysNotTo(Vows.Context):
            @Vows.async_topic
            @mock_s3
            def topic(self, callback):
                self.conn = S3Connection()
                self.conn.create_bucket(s3_bucket)

                config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket)
                storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
                storage.put(IMAGE_URL % '9998', IMAGE_BYTES)
                storage.put_crypto(IMAGE_URL % '9998')
                storage.get_crypto(IMAGE_URL % '9998', callback=callback)

            def should_be_null(self, topic):
                expect(topic.args[0]).to_be_null()

        class CanStoreCrypto(Vows.Context):
            @Vows.async_topic
            @mock_s3
            def topic(self, callback):
                self.conn = S3Connection()
                self.conn.create_bucket(s3_bucket)

                config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket, STORES_CRYPTO_KEY_FOR_EACH_IMAGE=True)
                storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
                storage.put(IMAGE_URL % '6', IMAGE_BYTES)
                storage.put_crypto(IMAGE_URL % '6')
                storage.get_crypto(IMAGE_URL % '6', callback=callback)

            def should_not_be_null(self, topic):
                expect(topic.args[0]).not_to_be_null()
                expect(topic.args[0]).not_to_be_an_error()
                expect(topic.args[0]).to_equal('ACME-SEC')

    class DetectorVows(Vows.Context):
        class CanStoreDetectorData(Vows.Context):
            @Vows.async_topic
            @mock_s3
            def topic(self, callback):
                self.conn = S3Connection()
                self.conn.create_bucket(s3_bucket)

                config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket)
                storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
                storage.put(IMAGE_URL % '7', IMAGE_BYTES)
                storage.put_detector_data(IMAGE_URL % '7', 'some-data')
                storage.get_detector_data(IMAGE_URL % '7', callback=callback)

            def should_not_be_null(self, topic):
                expect(topic.args[0]).not_to_be_null()
                expect(topic.args[0]).not_to_be_an_error()
                expect(topic.args[0]).to_equal('some-data')

        class ReturnsNoneIfNoDetectorData(Vows.Context):
            @Vows.async_topic
            @mock_s3
            def topic(self, callback):
                self.conn = S3Connection()
                self.conn.create_bucket(s3_bucket)

                config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket)
                storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
                storage.get_detector_data(IMAGE_URL % '9999', callback=callback)

            def should_not_be_null(self, topic):
                expect(topic.args[0]).to_be_null()

    class WebPVows(Vows.Context):
        class HasConfigRequest(Vows.Context):
            def topic(self):
                config  = Config(AUTO_WEBP=True)
                context = Context(config=config)
                context.request = RequestParameters(accepts_webp=True)
                return Storage(context)

            def should_be_webp(self, topic):
                expect(topic.is_auto_webp).to_be_true()

        class HasConfigNoRequest(Vows.Context):
            def topic(self):
                config  = Config(AUTO_WEBP=True)
                context = Context(config=config)
                return Storage(context)

            def should_be_webp(self, topic):
                expect(topic.is_auto_webp).to_be_false()

        class HasConfigRequestDoesNotAccept(Vows.Context):
            def topic(self):
                config  = Config(AUTO_WEBP=True)
                context = Context(config=config)
                context.request = RequestParameters(accepts_webp=False)
                return Storage(context)

            def should_be_webp(self, topic):
                expect(topic.is_auto_webp).to_be_false()

        class HasNotConfig(Vows.Context):
            def topic(self):
                config  = Config(AUTO_WEBP=False)
                context = Context(config=config)
                context.request = RequestParameters(accepts_webp=True)
                return Storage(context)

            def should_be_webp(self, topic):
                expect(topic.is_auto_webp).to_be_false()

    class ExpiredVows(Vows.Context):
        class WhenExpiredEnabled(Vows.Context):
            def topic(self):
                return Storage(Context(config=Config(STORAGE_EXPIRATION_SECONDS=3600)))

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
                return Storage(Context(config=Config(STORAGE_EXPIRATION_SECONDS=0)))

            def should_not_tell_when_expired(self, topic):
                key = {
                    'LastModified': (datetime.now(tzutc()) - timedelta(seconds=3601)),
                    'Body': 'foobar',
                }
                expect(topic.is_expired(key)).to_be_false()
