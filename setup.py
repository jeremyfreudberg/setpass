#!/usr/bin/env python

from distutils.core import setup

setup(
    name='setpass',
    version='1.0',
    description='SetPass for OpenStack',
    author='Kristi Nikolla',
    author_email='knikolla@bu.edu',
    url='https://github.com/knikolla/setpass',
    packages=['setpass', 'setpass.templates'],
    package_data={'setpass.templates':['*']}
)
