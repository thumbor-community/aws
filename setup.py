# coding: utf-8

from setuptools import setup, find_packages

setup(
    name='tc_aws',
    version='6.0.0b1',
    description='Thumbor AWS extensions',
    author='Thumbor-Community & William King',
    author_email='willtrking@gmail.com',
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(),
    install_requires=[
        'python-dateutil',
        'thumbor>=6.0.0b1',
        'tornado-botocore',
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
