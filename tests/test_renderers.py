import json

from django.conf.urls import patterns, include
from django.db.models import Model, CharField
from django.test import TestCase

from rest_framework import status
from rest_framework.routers import DefaultRouter
from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.viewsets import ReadOnlyModelViewSet
from pytest import fixture

from rest_framework_cj.renderers import CollectionJsonRenderer


class Dummy(Model):
    name = CharField(max_length='100')


class DummyHyperlinkedModelSerializer(HyperlinkedModelSerializer):
    class Meta(object):
        model = Dummy
        fields = ('url', 'name')


class DummyReadOnlyModelViewSet(ReadOnlyModelViewSet):
    renderer_classes = (CollectionJsonRenderer, )
    queryset = Dummy.objects.all()
    serializer_class = DummyHyperlinkedModelSerializer

router = DefaultRouter()
router.register('dummy', DummyReadOnlyModelViewSet)
urlpatterns = patterns(
    '',
    (r'^rest-api/', include(router.urls)),
)


@fixture
def cj_renderer(request):
    return CollectionJsonRenderer()


class TestCollectionJsonRenderer(TestCase):
    urls = 'tests.test_renderers'

    def setUp(self):
        Dummy.objects.create(name='Yolo McSwaggerson')
        self.response = self.client.get('/rest-api/dummy/')
        self.content = json.loads(self.response.content)

    def test_it_has_the_right_response_code(self):
        self.assertEqual(self.response.status_code, status.HTTP_200_OK)

    def test_it_has_the_right_content_type(self):
        content_type = self.response['Content-Type']
        self.assertEqual(content_type, 'application/vnd.collection+json')

    def test_it_has_the_version_number(self):
        self.assertEqual(self.content['collection']['version'], '1.0')

    def test_it_has_an_href(self):
        href = self.content['collection']['href']
        self.assertEqual(href, 'http://testserver/rest-api/dummy/')

    def get_dummy(self):
        return self.content['collection']['items'][0]

    def test_the_dummy_item_has_an_href(self):
        href = self.get_dummy()['href']
        self.assertEqual(href, 'http://testserver/rest-api/dummy/1/')

    def get_dummy_attribute(self, attribute_name):
        data = self.get_dummy()['data']
        return next(x for x in data if x['name'] == attribute_name)

    def test_the_dummy_item_contains_name(self):
        name = self.get_dummy_attribute('name')['value']
        self.assertEqual(name, 'Yolo McSwaggerson')
