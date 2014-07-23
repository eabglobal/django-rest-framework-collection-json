from setuptools import setup, find_packages

setup(
    name='djangorestframework_collection_json',
    version='0.0.1_dev_2',
    description='Collection+JSON support for Django REST Framework',
    author='Advisory Board Company',
    packages=find_packages(exclude=['']),
    install_requires=['djangorestframework'],
    classifiers=['Private  :: Do Not Upload to PyPI'],
    include_package_data=True,
    test_suite='tests.runtests.main',
)
