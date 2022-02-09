# se!/usr/bin/python
# -*- coding: utf-8 -*-
# coding: utf-8

# Copyright (c) 2015, thumbor-community
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.

from datetime import datetime, timedelta
from unittest import TestCase
from pytest import raises

from dateutil.tz import tzutc
from thumbor.config import Config
from thumbor.context import Context, RequestParameters
from tornado.testing import gen_test

from .fixtures.storage_fixture import IMAGE_URL, IMAGE_BYTES, get_server, s3_bucket
from tc_aws.storages.s3_storage import Storage
from tests import S3MockedAsyncTestCase


class S3StorageTestCase(S3MockedAsyncTestCase):

    @gen_test
    async def test_can_store_image(self):
        config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket)
        storage = Storage(Context(config=config, server=get_server('ACME-SEC')))

        await storage.put(IMAGE_URL % '1', IMAGE_BYTES)
        topic = await storage.get(IMAGE_URL % '1')

        self.assertEqual(topic, IMAGE_BYTES)

    @gen_test
    async def test_can_get_image_existance(self):
        config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket)
        storage = Storage(Context(config=config, server=get_server('ACME-SEC')))

        await storage.put(IMAGE_URL % '3', IMAGE_BYTES)
        topic = await storage.exists(IMAGE_URL % '3')

        self.assertTrue(topic)

    @gen_test
    async def test_can_get_image_inexistance(self):
        config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket)
        storage = Storage(Context(config=config, server=get_server('ACME-SEC')))

        topic = await storage.exists(IMAGE_URL % '9999')

        self.assertFalse(topic)

    @gen_test
    async def test_can_remove_instance(self):
        config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket,TC_AWS_STORAGE_ROOT_PATH='nana')
        storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
        await storage.put(IMAGE_URL % '4', IMAGE_BYTES)
        await storage.remove(IMAGE_URL % '4')
        topic = await storage.exists(IMAGE_URL % '4')

        self.assertFalse(topic)

    @gen_test
    async def test_can_remove_then_put_image(self):
        config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket)
        storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
        await storage.put(IMAGE_URL % '5', IMAGE_BYTES)

        created = await storage.exists(IMAGE_URL % '5')
        self.assertTrue(created)

        await storage.remove(IMAGE_URL % '5')
        exists = await storage.exists(IMAGE_URL % '5')
        self.assertFalse(exists)

        await storage.put(IMAGE_URL % '5', IMAGE_BYTES)
        exists = await storage.exists(IMAGE_URL % '5')
        self.assertTrue(exists)

    def test_should_return_storage_prefix(self):
        config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket, TC_AWS_STORAGE_ROOT_PATH='tata')
        storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
        topic = storage._normalize_path('toto')
        self.assertEqual(topic, "tata/toto")

    def should_normalize_slash(self):
        config = Config(TC_AWS_STORAGE_ROOT_PATH='', TC_AWS_ROOT_IMAGE_NAME='root_image')
        storage = Storage(Context(config=config))
        self.assertEqual(storage._normalize_path('/test'), 'test')
        self.assertEqual(storage._normalize_path('/test/'), 'test/root_image')
        self.assertEqual(storage._normalize_path('/test/image.png'), 'test/image.png')


class CryptoS3StorageTestCase(S3MockedAsyncTestCase):

    @gen_test
    async def test_should_raise_on_invalid_config(self):
        config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket, STORES_CRYPTO_KEY_FOR_EACH_IMAGE=True)
        storage = Storage(Context(config=config, server=get_server('')))

        await storage.put(IMAGE_URL % '9999', IMAGE_BYTES)

        with raises(RuntimeError, match='STORES_CRYPTO_KEY_FOR_EACH_IMAGE can\'t be True if no SECURITY_KEY specified'):
            await storage.put_crypto(IMAGE_URL % '9999')

    @gen_test
    async def test_getting_crypto_for_a_new_image_returns_none(self):
        config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket, STORES_CRYPTO_KEY_FOR_EACH_IMAGE=True)
        storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
        topic = await storage.get_crypto(IMAGE_URL % '9999')
        self.assertIsNone(topic)

    @gen_test
    async def test_does_not_store_if_config_says_not_to(self):
        config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket, STORES_CRYPTO_KEY_FOR_EACH_IMAGE=False)
        storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
        await storage.put(IMAGE_URL % '9998', IMAGE_BYTES)
        await storage.put_crypto(IMAGE_URL % '9998')
        topic = await storage.get_crypto(IMAGE_URL % '9998')
        self.assertIsNone(topic)

    @gen_test
    async def test_can_store_crypto(self):
        config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket, STORES_CRYPTO_KEY_FOR_EACH_IMAGE=True)
        storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
        await storage.put(IMAGE_URL % '6', IMAGE_BYTES)
        await storage.put_crypto(IMAGE_URL % '6')
        topic = await storage.get_crypto(IMAGE_URL % '6')

        self.assertIsNotNone(topic)
        self.assertNotIsInstance(topic, BaseException)
        self.assertEqual(topic, 'ACME-SEC')


class DetectorS3StorageTestCase(S3MockedAsyncTestCase):

    @gen_test
    async def test_can_store_detector_data(self):
        config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket)
        storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
        await storage.put(IMAGE_URL % '7', IMAGE_BYTES)
        await storage.put_detector_data(IMAGE_URL % '7', 'some-data')
        topic = await storage.get_detector_data(IMAGE_URL % '7')

        self.assertEqual(topic, 'some-data')

    @gen_test
    async def test_returns_none_if_no_detector_data(self):
        config = Config(TC_AWS_STORAGE_BUCKET=s3_bucket)
        storage = Storage(Context(config=config, server=get_server('ACME-SEC')))
        topic = await storage.get_detector_data(IMAGE_URL % '9999')

        self.assertIsNone(topic)


class WebpS3StorageTestCase(TestCase):

    def test_has_config_request(self):
        config = Config(AUTO_WEBP=True)
        context = Context(config=config)
        context.request = RequestParameters(accepts_webp=True)
        storage = Storage(context)
        self.assertTrue(storage.is_auto_webp)

    def test_has_config_no_request(self):
        config = Config(AUTO_WEBP=True)
        context = Context(config=config)
        storage = Storage(context)
        self.assertFalse(storage.is_auto_webp)

    def test_has_config_request_does_not_accept(self):
        config = Config(AUTO_WEBP=True)
        context = Context(config=config)
        context.request = RequestParameters(accepts_webp=False)
        storage = Storage(context)
        self.assertFalse(storage.is_auto_webp)

    def test_has_no_config(self):
        config = Config(AUTO_WEBP=False)
        context = Context(config=config)
        context.request = RequestParameters(accepts_webp=True)
        storage = Storage(context)
        self.assertFalse(storage.is_auto_webp)


class ExpiredTestCase(TestCase):

    @property
    def expired_enabled(self):
        return Storage(Context(config=Config(STORAGE_EXPIRATION_SECONDS=3600)))

    def test_should_check_invalid_key(self):
        self.assertTrue(self.expired_enabled.is_expired(None))
        self.assertTrue(self.expired_enabled.is_expired(False))
        self.assertTrue(self.expired_enabled.is_expired(dict()))
        self.assertTrue(self.expired_enabled.is_expired({'Error': ''}))

    def test_should_tell_when_not_expired(self):
        key = {
            'LastModified': datetime.now(tzutc()),
            'Body': 'foobar',
        }
        self.assertFalse(self.expired_enabled.is_expired(key))

    def test_should_tell_when_expired(self):
        key = {
            'LastModified': (datetime.now(tzutc()) - timedelta(seconds=3601)),
            'Body': 'foobar',
        }
        self.assertTrue(self.expired_enabled.is_expired(key))

    def test_expire_disabled_should_not_tell_when_expired(self):
        topic = Storage(Context(config=Config(STORAGE_EXPIRATION_SECONDS=0)))
        key = {
            'LastModified': (datetime.now(tzutc()) - timedelta(seconds=3601)),
            'Body': 'foobar',
        }
        self.assertFalse(topic.is_expired(key))
