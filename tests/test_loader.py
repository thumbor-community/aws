# coding: utf-8

# Copyright (c) 2015, thumbor-community
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.

from unittest import TestCase

from thumbor.config import Config
from thumbor.context import Context

from tc_aws.loaders import _get_bucket, _get_bucket_and_key, _get_key
from .fixtures.storage_fixture import IMAGE_PATH


class LoaderTestCase(TestCase):
    def test_can_get_bucket_and_key(self):
        conf = Config(
            TC_AWS_LOADER_BUCKET=None,
            TC_AWS_LOADER_ROOT_PATH=''
        )

        ctx = Context(config=conf)

        path = 'some-bucket/some/image/path.jpg'
        bucket, key = _get_bucket_and_key(ctx, path)
        self.assertEqual(bucket, 'some-bucket')
        self.assertEqual(key, 'some/image/path.jpg')

    def test_can_detect_bucket(self):
        topic = _get_bucket('/'.join(['thumbor-images-test', IMAGE_PATH]))
        self.assertEqual(topic, 'thumbor-images-test')

    def test_can_detect_key(self):
        conf = Config(
            TC_AWS_LOADER_BUCKET=None,
            TC_AWS_LOADER_ROOT_PATH='',
        )
        context = Context(config=conf)
        key = _get_key(IMAGE_PATH, context)

        self.assertEqual(key, IMAGE_PATH)
