# Thumbor Community - AWS: Changelog

This file will describe the changes in each version, noticeable the BC Breaks that may have append

## 6.2 - S3 Keys randomization

You can now randomize the keys for the storages to improve performance. To do that, update the configuration:

``TC_AWS_RANDOMIZE_KEYS=True``

This is set to False by default to preserve backwards compatibility.

**Warning**: enabling this option will result in re-generating all your cached files on your storages.

## 6.1 - Custom endpoint

You can now specify a custom AWS API endpoint by setting this in the configuration:

``TC_AWS_ENDPOINT=http://your.endpoint.url/``

## 2.0 - Async Connection

Switched connection from Boto 2.0 to botocore, in order to handle tornado async connections. This update leads to some major BC Breaks.

* [BC BREAK] Authentication is now handled by botocore directly, the following configuration values are no more used:
    * AWS_ROLE_BASED_CONNECTION
    * AWS_ACCESS_KEY
    * AWS_SECRET_KEY
    * BOTO_CONFIG
    You'll need to use boto's configuration file directly to handle your server's authentication to S3, or role-based connection. See <https://github.com/boto/boto3>
* [BC BREAK] A new option has been added to configure the AWS region, named ``TC_AWS_REGION``; it defaults to ``eu-west-1``
* [BC BREAK] Option's names have been uniformized as well, here's the old to new options' names mapping:

| Old option | New option |
| ---------- | ---------- |
| STORAGE_BUCKET | TC_AWS_STORAGE_BUCKET |
| RESULT_STORAGE_BUCKET | TC_AWS_RESULT_STORAGE_BUCKET |
| S3_LOADER_BUCKET | TC_AWS_LOADER_BUCKET |
| S3_LOADER_ROOT_PATH | TC_AWS_LOADER_ROOT_PATH |
| STORAGE_AWS_STORAGE_ROOT_PATH | TC_AWS_STORAGE_ROOT_PATH |
| RESULT_STORAGE_AWS_STORAGE_ROOT_PATH | TC_AWS_RESULT_STORAGE_ROOT_PATH |
| S3_STORAGE_SSE | TC_AWS_STORAGE_SSE |
| S3_STORAGE_RRS | TC_AWS_STORAGE_RRS |
| S3_ALLOWED_BUCKETS | TC_AWS_ALLOWED_BUCKETS |
| RESULT_STORAGE_S3_STORE_METADATA | TC_AWS_STORE_METADATA |
| AWS_ENABLE_HTTP_LOADER | TC_AWS_ENABLE_HTTP_LOADER |
| AWS_ACCESS_KEY | N/A |
| AWS_SECRET_KEY | N/A |
| AWS_ROLE_BASED_CONNECTION | N/A |
| BOTO_CONFIG | N/A |
