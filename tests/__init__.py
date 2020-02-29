# coding: utf-8

# Copyright (c) 2015, thumbor-community
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.

import logging
import os
import signal
import subprocess as sp
import sys
import time

import botocore.session
import mock
import requests
from aiobotocore.session import AioSession
from tornado.testing import AsyncTestCase

from tc_aws.aws.bucket import Bucket
from tests.fixtures.storage_fixture import s3_bucket

logging.basicConfig(level=logging.CRITICAL)

os.environ["TEST_SERVER_MODE"] = "true"

_proxy_bypass = {
    "http": None,
    "https": None,
}


def start_service(host, port):
    args = [sys.executable, "-m", "moto.server", "-H", host,
            "-p", str(port)]

    process = sp.Popen(args, stderr=sp.PIPE)
    url = "http://{host}:{port}".format(host=host, port=port)

    for i in range(0, 30):
        if process.poll() is not None:
            process.communicate()
            break

        try:
            # we need to bypass the proxies due to monkeypatches
            requests.get(url, timeout=0.5)
            break
        except requests.exceptions.ConnectionError:
            time.sleep(0.5)
    else:
        stop_process(process)

    return process


def stop_process(process):
    try:
        process.send_signal(signal.SIGTERM)
        process.communicate()
    except Exception:
        process.kill()
        outs, errors = process.communicate()
        exit_code = process.returncode
        msg = "Child process finished {} not in clean way: {} {}" \
            .format(exit_code, outs, errors)
        raise RuntimeError(msg)


class FakeSession(AioSession):

    def create_client(self, *args, **kwargs):
        if kwargs['endpoint_url'] is None:
            kwargs['endpoint_url'] = "http://localhost:5000"
        return super(FakeSession, self).create_client(*args, **kwargs)


class S3MockedAsyncTestCase(AsyncTestCase):
    _process = None

    @classmethod
    def setUpClass(cls):
        super(S3MockedAsyncTestCase, cls).setUpClass()
        cls._process = start_service("localhost", 5000)

        os.environ['AWS_SHARED_CREDENTIALS_FILE'] = ''
        os.environ['AWS_ACCESS_KEY_ID'] = 'test-key'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test-secret-key'
        os.environ['AWS_SESSION_TOKEN'] = 'test-session-token'

    @classmethod
    def tearDownClass(cls):
        super(S3MockedAsyncTestCase, cls).tearDownClass()
        stop_process(cls._process)

    def setUp(self):
        super(S3MockedAsyncTestCase, self).setUp()

        requests.post("http://localhost:5000/moto-api/reset")

        client = botocore.session.get_session().create_client('s3', endpoint_url='http://localhost:5000/')
        client.create_bucket(Bucket=s3_bucket)

        client_patcher = mock.patch('aiobotocore.session.AioSession', FakeSession)
        client_patcher.start()

        self.addCleanup(client_patcher.stop)

    def tearDown(self):
        super(S3MockedAsyncTestCase, self).tearDown()
        # singleton Bucket holds old IOLoop instance which closed after each test
        # this cleans singleton
        Bucket._instances = {}
