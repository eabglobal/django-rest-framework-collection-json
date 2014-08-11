import django
from django.utils import unittest


if django.VERSION[0] <= 1 and django.VERSION[1] <= 5:
    def suite():
        return unittest.TestLoader().discover("testapp", pattern="test_*.py")
