# coding: utf-8

import os
import sys
import re

from setuptools import setup, find_packages
from setuptools.command.install import install

def version():
    """retrieve version from tag name"""
    tag = os.getenv('CIRCLE_TAG', '1')

    if re.match('\d+(\.\d+)*', tag):
        return tag

    info = "Git tag: {0} does not match the version pattern of this app".format(
        tag
    )
    sys.exit(info)

def readme():
    """print long description"""
    with open('Readme.md') as f:
        return f.read()

setup(
    name='tc_aws',
    version=version(),
    description='Thumbor AWS extensions',
    long_description=readme(),
    author='Thumbor-Community & William King',
    author_email='h.briand@gmail.com',  # Original author email is: willtrking@gmail.com
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
    ],
    keywords='thumbor aws',
    install_requires=[
        'python-dateutil',
        'thumbor>=6.0.0,<7',
        'tornado-botocore>=1.3.1',
    ],
    extras_require={
        'tests': [
            'pyvows',
            'coverage',
            'tornado_pyvows',
            'boto',
            'moto',
            'mock',
        ],
    },
)
