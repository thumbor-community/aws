# Thumbor AWS

[![Join the chat at https://gitter.im/thumbor-community/aws](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/thumbor-community/aws?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![Circle CI](https://circleci.com/gh/thumbor-community/aws.svg?style=svg)](https://circleci.com/gh/thumbor-community/aws)

## Installation

```bash
    pip install tc_aws
```

### Authentication

Authentication is handled by botocore, see [Boto3 documentation](https://boto3.readthedocs.org/en/latest/guide/quickstart.html#configuration).

## Origin story

This is a fork of [willtrking thumbor_aws](https://github.com/willtrking/thumbor_aws); as this repository was not maintained anymore,
we decided to maintain it under the [thumbor-community](https://github.com/thumbor-community) organization.

## Contribution

First you need to fork this project.
Clone your repo at your computer
Next, inside a folder for project:

```bash
    make setup
    make test
```

If all test passed, you have an environment ready to start.
We recommend to use python-virtualevn (virtualenv and virtualenv-wrapper)

## Features

 * *tc_aws.loaders.s3_loader* - takes a S3 key path and optional bucket name, and downloads the file through the S3 API.
 * *tc_aws.loaders.presigning_loader* - instead of downloading via the API, generates a signed link to the file on S3, then feeds it to the Thumbor's regular http loader. This will likely be more performant, as it avoids async issues with the boto library (see [#22](https://github.com/thumbor-community/aws/pull/22) and [#14](https://github.com/thumbor-community/aws/issues/14).
 * *tc_aws.result_storages.s3_storage*
 * *tc_aws.storages.s3_storage*

### What is the purpose of the S3 loader?

You might ask yourself why the S3 loaders are necessary? Aren't files on S3 already available through HTTP already? Why wouldn't you just give the S3 url of your file to Thumbor and let it query the file through HTTP?

If your S3 assets are not public, you'll need to generate a signed URL. This url will be different everytime you sign it. Thumbor will be unable to understand that these urls all refer to the same file, and thus won be able to cache it.

The S3 loader avoids this problem, since you'll only be including the S3 key name in the Thumbor url. Thumbor itself will have the AWS authorization keys to fetch the file.

## Additional Configuration values used:

### General settings

```.ini
# AWS Region the bucket is located in.
TC_AWS_REGION='eu-west-1'
# A custom AWS endpoint.
TC_AWS_ENDPOINT=''
```

###  Loader settings

When using either ``tc_aws.loaders.s3_loader`` or ``tc_aws.loaders.presigning_loader``.

```.ini
TC_AWS_STORAGE_BUCKET='' # S3 bucket for Storage
TC_AWS_STORAGE_ROOT_PATH='' # S3 path prefix for Storage bucket

# S3 bucket for Loader. If given, source urls are interpreted as keys
# within this bucket. If not given, source urls are expected to contain
# the bucket name, such as 's3-bucket/keypath'.
TC_AWS_LOADER_BUCKET=''

# S3 path prefix for Loader bucket. If given, this is prefixed to
# all S3 keys.
TC_AWS_LOADER_ROOT_PATH=''

# Enable HTTP Loader as well?
# This would allow you to load watermarks in over your images dynamically through a URI
# E.g.
# http://your-thumbor.com/unsafe/filters:watermark(http://example.com/watermark.png,0,0,50)/s3_bucket/photo.jpg
TC_AWS_ENABLE_HTTP_LOADER=False

TC_AWS_ALLOWED_BUCKETS=False # List of allowed bucket to be requested
```

###  Storage settings

When ``tc_aws.storages.s3_storage`` is enabled.

```.ini
TC_AWS_STORAGE_BUCKET='' # S3 bucket for Storage
TC_AWS_STORAGE_ROOT_PATH='' # S3 path prefix for Storage bucket

# put data into S3 using the Server Side Encryption functionality to
# encrypt data at rest in S3
# https://aws.amazon.com/about-aws/whats-new/2011/10/04/amazon-s3-announces-server-side-encryption-support/
TC_AWS_STORAGE_SSE=False

# put data into S3 with Reduced Redundancy
# https://aws.amazon.com/about-aws/whats-new/2010/05/19/announcing-amazon-s3-reduced-redundancy-storage/
TC_AWS_STORAGE_RRS=False
```

###  Result storage settings

When ``tc_aws.result_storages.s3_storage`` is enabled.

```.ini
TC_AWS_RESULT_STORAGE_BUCKET='' # S3 bucket for result Storage
TC_AWS_RESULT_STORAGE_ROOT_PATH='' # S3 path prefix for Result storage bucket
TC_AWS_MAX_RETRY=0 # Max retries for get image from S3 Bucket. Default is 0

TC_AWS_STORE_METADATA=False # Store result with metadata (for instance content-type)
```

### Key settings

```.ini
TC_AWS_RANDOMIZE_KEYS=False # Adds some randomization in the S3 keys for the Storage and Result Storage. Defaults to False for Backwards Compatibility, set it to True for performance.
TC_AWS_ROOT_IMAGE_NAME='root_image' # Sets a default name for requested images ending with a trailing /. Those images will be stored in result_storage and storage under the name set in this configuration.
```

## Troubleshooting

### Check your configuration

You may have errors due to unproperly formatted configuration. For instance, if you've set the value "None" or "", this will default to the string value, and not the False or None value exepected, which can lead to issues later on. So if you're running into issues, try to re-read the configuration, taking care of the formatting.

### Make it work with riak

You'll need to tweak a bit your aws configuration (see boto doc), which should in the end look as follows:

```
[default]
aws_access_key_id = (KEY)
aws_secret_access_key =(SECRET)
s3 =
    signature_version = s3
```
