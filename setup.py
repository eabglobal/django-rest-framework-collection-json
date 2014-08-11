import os
from setuptools import setup, find_packages


def read(*paths):
    with open(os.path.join(*paths), 'r') as f:
        return f.read()

setup(
    name='djangorestframework-collection-json',
    version='0.0.1_dev_2',
    description='Collection+JSON support for Django REST Framework',
    long_description=read('README.rst'),
    author='Advisory Board Company',
    author_email='chris@chrismarinos.com',
    url='https://github.com/advisory/django-rest-framework-collection-json',
    license='MIT',
    packages=find_packages(exclude=['tests*']),
    install_requires=['djangorestframework'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
    ],
    include_package_data=True,
    test_suite='runtests.runtests.main',
)
