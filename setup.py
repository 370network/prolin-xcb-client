#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
  name='prolin-xcb-client',
  version='1.0',
  entry_points = {
      'console_scripts': ['paxclient=main:main'],
  }
)
