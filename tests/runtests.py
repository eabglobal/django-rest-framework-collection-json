#!/usr/bin/env python
"""
Useful tool to run the test suite and generate a coverage report.
Shamelessly adapted from https://github.com/tomchristie/django-rest-framework/blob/master/rest_framework/runtests/runcoverage.py
"""

import os
import sys

# fix sys path so we don't need to setup PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'


def main():
    """Run the tests for rest_framework and generate a coverage report."""

    from django.conf import settings
    from django.test.utils import get_runner
    TestRunner = get_runner(settings)

    test_runner = TestRunner()
    failures = test_runner.run_tests(['tests'])
    sys.exit(failures)

if __name__ == '__main__':
    main()
