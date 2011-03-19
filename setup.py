#-*- coding:utf-8 -*-
import setuptools

version = '0.0.1'

setuptools.setup(
    name='rsc',
    packages=['rsc'],
    install_requires=[
        'lxml',
        'tweepy',
        ],
    version=version)

