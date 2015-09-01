Thumbor AWS
===========

[![Join the chat at https://gitter.im/thumbor-community/aws](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/thumbor-community/aws?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

[![Circle CI](https://circleci.com/gh/thumbor-community/aws.svg?style=svg)](https://circleci.com/gh/thumbor-community/aws)

Installation
------------

```bash
    pip install tc_aws
```

Origin story
------------

This is a fork of https://github.com/willtrking/thumbor_aws ; as this repository was not maintained anymore, 
we decided to maintain it under the ``thumbor-community`` organisation.

Features
--------

 * tc_aws.loaders.s3_loader
 * tc_aws.result_storages.s3_storage
 * tc_aws.storages.s3_storage

Additional Configuration values used:

	# the Amazon Web Services access key to use
    AWS_ACCESS_KEY = ""
    # the Amazon Web Services secret of the used access key
    AWS_SECRET_KEY = ""

    # Alternatively (recommended), use Role-based connection
    # http://docs.aws.amazon.com/IAM/latest/UserGuide/roles-assume-role.html
    AWS_ROLE_BASED_CONNECTION = True or False (Default: False)


    # configuration settings specific for the s3_loader

    # list of allowed buckets for the s3_loader
    S3_ALLOWED_BUCKETS = []

    # alternatively: set a fixed bucket, no need for bucket name in Image-Path
    S3_LOADER_BUCKET = 'thumbor-images'
    # A root path for loading images, useful if you share the bucket
    S3_LOADER_ROOT_PATH = 'source-images'

    # configuration settings specific for the storages

    STORAGE_BUCKET = 'thumbor-images'
    # A root path for the storage, useful if you share a bucket for loading / storing
    STORAGE_AWS_STORAGE_ROOT_PATH = 'storage'

    RESULT_STORAGE_BUCKET = 'thumbor-images'
    RESULT_STORAGE_AWS_STORAGE_ROOT_PATH = 'result'

    STORAGE_EXPIRATION_SECONDS

    # put data into S3 using the Server Side Encryption functionality to
    # encrypt data at rest in S3
    # https://aws.amazon.com/about-aws/whats-new/2011/10/04/amazon-s3-announces-server-side-encryption-support/
    S3_STORAGE_SSE = True or False (Default: False)

    # put data into S3 with Reduced Redundancy
    # https://aws.amazon.com/about-aws/whats-new/2010/05/19/announcing-amazon-s3-reduced-redundancy-storage/
    S3_STORAGE_RRS = True or False (Default: False)


    #Optional config value to enable the HTTP loader
    #This would allow you to load watermarks in over your images dynamically through a URI
    #E.g.
    #http://your-thumbor.com/unsafe/filters:watermark(http://example.com/watermark.png,0,0,50)/s3_bucket/photo.jpg
    AWS_ENABLE_HTTP_LOADER = True or False (Default: False)


    # Optional additional configuration for the Boto-Client used to access S3.
    # see http://boto.readthedocs.org/en/latest/ref/s3.html?highlight=boto.s3.connection.s3connection#boto.s3.connection.S3Connection
    # for all available config options
    BOTO_CONFIG = {
        'host': 'fakes3.local.dev',
        'is_secure': False
    }
