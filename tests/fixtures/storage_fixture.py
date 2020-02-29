# coding: utf-8

# Copyright (c) 2015, thumbor-community
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.

from os.path import join, abspath, dirname

from thumbor.context import ServerParameters

s3_bucket = 'thumbor-images-test'

IMAGE_URL = 's.glbimg.com/some/image_%s.jpg'
IMAGE_PATH = join(abspath(dirname(__file__)), 'image.jpg')

with open(IMAGE_PATH, 'rb') as img:
    IMAGE_BYTES = img.read()


def get_server(key=None):
    server_params = ServerParameters(8888, 'localhost', 'thumbor.conf', None, 'info', None)
    server_params.security_key = key
    return server_params
