# se!/usr/bin/python
# -*- coding: utf-8 -*-

from urlparse import urlparse, parse_qs

from mock import Mock
from mock import patch
from moto import mock_s3
from pyvows import Vows, expect

from thumbor.context import Context
from derpconf.config import Config

from tc_aws.aws.bucket import Bucket

import logging
logging.getLogger('botocore').setLevel(logging.CRITICAL)

s3_bucket = 'thumbor-images-test'
s3_region = 'us-east-1'
s3_path = '/some/image.jpg'

@Vows.batch
class BucketVows(Vows.Context):

    class CanBuildPresignedUrl(Vows.Context):

        def topic(self):
            bucket = Bucket(s3_bucket, s3_region)
            return bucket

        def should_generate_presigned_urls(self, bucket):
            def assert_it(url):
                url = urlparse(url)
                expect(url.scheme).to_equal('https')
                expect(url.hostname).to_equal('thumbor-images-test.s3.amazonaws.com')
                expect(url.path).to_equal(s3_path)
                url_params = parse_qs(url.query)
                # We can't test Expires & Signature values as they vary depending on the TZ
                expect(url_params).to_include('Expires')
                expect(url_params).to_include('Signature')
                # expect(url_params['AWSAccessKeyId'][0]).to_equal('test-key')
                # expect(url_params['x-amz-security-token'][0]).to_equal('test-session-token')

            bucket.get_url(s3_path, callback=assert_it)
