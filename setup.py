#!/usr/bin/env python

from setuptools import setup, find_packages
import versioneer

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
        name="fourpisky",
        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),
        packages=find_packages(),
        include_package_data=True,
        description="Utility scripts for reacting to received VOEvent packets",
        author="Tim Staley",
        author_email="timstaley337@gmail.com",
        url="https://github.com/timstaley/fourpisky",
        install_requires=required,
        entry_points='''
            [console_scripts]
            fps_process_voevent=fourpisky.scripts.process_voevent:main
        ''',
)
