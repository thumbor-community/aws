# coding: utf-8

from thumbor.config import Config

Config.define('TC_AWS_REGION',                    'eu-west-1', 'S3 region', 'S3')

Config.define('TC_AWS_ENDPOINT_URL',               None,       'Endpoint URL to use (mainly for testing)', 'S3')
Config.define('TC_AWS_CONFIG',                     None,       'Additional config to pass to the client', 'S3')
Config.define('TC_AWS_LOADER_BUCKET',              None,       'S3 bucket for loader', 'S3')
Config.define('TC_AWS_LOADER_ROOT_PATH',           '',         'S3 path prefix for Loader bucket', 'S3')

Config.define('TC_AWS_ENABLE_HTTP_LOADER',         False,      'Enable HTTP Loader as well?', 'S3')
Config.define('TC_AWS_ALLOWED_BUCKETS',            False,      'List of allowed buckets to be requested', 'S3')
