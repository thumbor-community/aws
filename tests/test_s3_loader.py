# coding: utf-8

# Copyright (c) 2015, thumbor-community
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.

import botocore.session
from derpconf.config import Config
from mock import patch, MagicMock
from thumbor.context import Context
from tornado.testing import gen_test

from fixtures.storage_fixture import IMAGE_PATH, IMAGE_BYTES, s3_bucket
from tc_aws.loaders import s3_loader
from tests import S3MockedAsyncTestCase


class S3LoaderTestCase(S3MockedAsyncTestCase):

    @gen_test
    def test_can_load_image(self):
        client = botocore.session.get_session().create_client('s3')
        client.create_bucket(Bucket=s3_bucket)

        client.put_object(
            Bucket=s3_bucket,
            Key=''.join(['root_path', IMAGE_PATH]),
            Body=IMAGE_BYTES,
            ContentType='image/jpeg', )

        conf = Config(
            TC_AWS_LOADER_BUCKET=s3_bucket,
            TC_AWS_LOADER_ROOT_PATH='root_path'
        )

        image = yield s3_loader.load(Context(config=conf), IMAGE_PATH)
        self.assertEqual(image, IMAGE_BYTES)

    @gen_test
    def test_can_validate_buckets(self):
        conf = Config(
            TC_AWS_ALLOWED_BUCKETS=['whitelist_bucket'],
            TC_AWS_LOADER_BUCKET=None,
        )

        image = yield s3_loader.load(Context(config=conf), '/'.join([s3_bucket, IMAGE_PATH]))
        self.assertIsNone(image.buffer)

    @patch('thumbor.loaders.http_loader.load_sync')
    @gen_test
    def test_should_use_http_loader(self, load_sync_patch):
        def cb(a, b, callback, *args, **kwargs):
            callback('foobar')
            return None

        load_sync_patch.side_effect = cb

        conf = Config(TC_AWS_ENABLE_HTTP_LOADER=True)
        s3_loader.load(Context(config=conf), 'http://foo.bar')
        self.assertTrue(load_sync_patch.called)

    @patch('thumbor.loaders.http_loader.load_sync')
    @gen_test
    def test_should_not_use_http_loader_if_not_prefixed_with_scheme(self, load_sync_patch):
        conf = Config(TC_AWS_ENABLE_HTTP_LOADER=True)
        yield s3_loader.load(Context(config=conf), 'foo/bar')
        self.assertFalse(load_sync_patch.called)

    def test_datafunc_loader(self):
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
            max_retry=3
        )

        func(file_key)
        self.assertEqual(self.call_count, 3)
