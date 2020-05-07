#!/usr/bin/env python

from distutils.core import setup

setup(
    name='targetd',
    version='0.8.11-pbit1',
    description='Linux remote storage API daemon',
    license='GPLv3',
    maintainer='Andy Grover',
    maintainer_email='andy@groveronline.com',
    url='http://github.com/open-iscsi/targetd',
    packages=['targetd'],
    install_requires=['setproctitle', 'yaml', 'rtslib_fb'],
    scripts=['scripts/targetd'],
    data_files = [('/usr/lib/systemd/system', ['targetd.service']),
              ('/etc/target', ['targetd.yaml'])
             ]
)
