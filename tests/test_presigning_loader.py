# coding: utf-8

# Copyright (c) 2015, thumbor-community
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.

from urlparse import urlparse, parse_qs

import botocore.session
from derpconf.config import Config
from mock import patch
from thumbor.context import Context
from tornado.testing import gen_test

from fixtures.storage_fixture import IMAGE_PATH, IMAGE_BYTES, s3_bucket
from tc_aws.loaders import presigning_loader
from tests import S3MockedAsyncTestCase


class PreSigningLoaderTestCase(S3MockedAsyncTestCase):
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
            TC_AWS_LOADER_ROOT_PATH='root_path',
        )

        image = yield presigning_loader.load(Context(config=conf), IMAGE_PATH)
        self.assertEqual(image.buffer, IMAGE_BYTES)

    @patch('thumbor.loaders.http_loader.load_sync')
    @gen_test
    def test_should_use_http_loader(self, load_sync_patch):
        def cb(a, b, callback, *args, **kwargs):
            callback('foobar')
            return None

        load_sync_patch.side_effect = cb

        conf = Config(TC_AWS_ENABLE_HTTP_LOADER=True)
        presigning_loader.load(Context(config=conf), 'http://foo.bar')
        self.assertTrue(load_sync_patch.called)

    @gen_test
    def test_can_validate_buckets(self):
        conf = Config(
            TC_AWS_ALLOWED_BUCKETS=['whitelist_bucket'],
            TC_AWS_LOADER_BUCKET=None,
        )

        image = yield presigning_loader.load(Context(config=conf), '/'.join([s3_bucket, IMAGE_PATH]))
        self.assertIsNone(image)

    @gen_test
    def test_can_build_presigned_url(self):
        context = Context(config=(Config()))
        url = yield presigning_loader._generate_presigned_url(context, "bucket-name", "some-s3-key")

        url = urlparse(url)
        self.assertEqual(url.scheme[0:4], 'http')
        self.assertEqual(url.path, '/bucket-name/some-s3-key')

        url_params = parse_qs(url.query)
        # We can't test Expires & Signature values as they vary depending on the TZ
        self.assertIn('Expires', url_params)
        self.assertIn('Signature', url_params)

        self.assertDictContainsSubset({'AWSAccessKeyId': ['test-key'], 'x-amz-security-token': ['test-session-token']},
                                      url_params)
