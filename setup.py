#!/usr/bin/env python

from setuptools import setup
import versioneer

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name="fourpisky",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=['fourpisky', 'fourpisky.comms', 'fourpisky.triggers',
              'fourpisky.tests', 'fourpisky.tests.resources'],
    package_data={'fourpisky':[
        'tests/resources/*.xml',
       'templates/*.j2', 'templates/includes/*.j2'
    ]},
    description="Utility scripts for reacting to received VOEvent packets",
    author="Tim Staley",
    author_email="timstaley337@gmail.com",
    url="https://github.com/timstaley/fourpisky",
    install_requires=required
)
