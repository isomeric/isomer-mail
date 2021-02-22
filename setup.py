#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# Isomer - The distributed application framework
# ==============================================
# Copyright (C) 2011-2019 Heiko 'riot' Weinen <riot@c-base.org> and others.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

__author__ = "Heiko 'riot' Weinen"
__license__ = "AGPLv3"

from setuptools import setup, find_namespace_packages

setup(
    name="isomer-mail",
    version="0.0.2",
    description="isomer-mail",
    author="Isomer Community",
    author_email="riot@c-base.org",
    url="https://github.com/isomeric/isomer-mail",
    license="GNU Affero General Public License v3",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        # 'Framework :: Isomer :: 1',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Communications :: Email'
    ],
    packages=find_namespace_packages(),
    package_data={'isomer-mail': ['../docs/*', '../frontend/*']},
    include_package_data=True,
    long_description="""Isomer - Mail support
=====================

E-mail support package for isomer instances.

Contains mail receiver and transmitter components.

This software package is a plugin module for isomer.
""",
    dependency_links=[],
    install_requires=[
        'isomer>=1.1.4'
    ],
    entry_points="""[isomer.components]
    mail-receiver=isomer.mail.receiver:MailReceiver
    mail-transmitter=isomer.mail.transmitter:MailTransmitter
    """,
    test_suite="tests.main.main",
)


