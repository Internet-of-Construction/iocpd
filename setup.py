# -*- coding: utf-8 -*-
"""
Created on Thu Jul 28 14:31:18 2022

@author: GarlefHupfer
"""

from setuptools import find_packages, setup
setup(
    name='iocpd',
    packages=find_packages(include=['iocpd']),
    version='0.1.0',
    description='IoC Project Dashboard',
    author='Garlef Hupfer',
    license='IoC',
    install_requires=[],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='tests',
)