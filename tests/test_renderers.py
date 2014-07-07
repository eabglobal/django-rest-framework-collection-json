import json

from django.conf.urls import patterns, include
from django.db.models import Model, CharField, ForeignKey
from django.test import TestCase

from collection_json import Collection
from rest_framework import status
from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.serializers import HyperlinkedModelSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from pytest import fixture

from rest_framework_cj.renderers import CollectionJsonRenderer
from rest_framework_cj.fields import LinkField


class Moron(Model):
    name = CharField(max_length='100')


class MoronHyperlinkedModelSerializer(HyperlinkedModelSerializer):
    class Meta(object):
        model = Moron
        fields = ('url', 'name')


class MoronReadOnlyModelViewSet(ReadOnlyModelViewSet):
    renderer_classes = (CollectionJsonRenderer, )
    queryset = Moron.objects.all()
    serializer_class = MoronHyperlinkedModelSerializer


class Dummy(Model):
    name = CharField(max_length='100')
    moron = ForeignKey('Moron')


class DummyHyperlinkedModelSerializer(HyperlinkedModelSerializer):
    other_stuff = LinkField('get_other_link')
    some_link = HyperlinkedIdentityField(view_name='moron-detail')

    class Meta(object):
        model = Dummy
        fields = ('url', 'name', 'moron', 'other_stuff', 'some_link')

    def get_other_link(self, obj):
        return 'http://other-stuff.com/'


class DummyReadOnlyModelViewSet(ReadOnlyModelViewSet):
    renderer_classes = (CollectionJsonRenderer, )
    queryset = Dummy.objects.all()
    serializer_class = DummyHyperlinkedModelSerializer


class NoSerializerView(APIView):
    renderer_classes = (CollectionJsonRenderer, )

    def get(self, request):
        return Response({'foo': '1'})


class PaginatedDataView(APIView):
    renderer_classes = (CollectionJsonRenderer, )

    def get(self, request):
        return Response({
            'next': 'http://test.com/colleciton/next',
            'previous': 'http://test.com/colleciton/previous',
            'results': [{'foo': 1}],
        })


class NonePaginatedDataView(APIView):
    renderer_classes = (CollectionJsonRenderer, )

    def get(self, request):
        return Response({
            'next': None,
            'previous': None,
            'results': [{'foo': 1}],
        })


router = DefaultRouter()
router.register('dummy', DummyReadOnlyModelViewSet)
router.register('moron', MoronReadOnlyModelViewSet)
urlpatterns = patterns(
    '',
    (r'^rest-api/', include(router.urls)),
    (r'^rest-api/no-serializer/', NoSerializerView.as_view()),
    (r'^rest-api/paginated/', PaginatedDataView.as_view()),
    (r'^rest-api/none-paginated/', NonePaginatedDataView.as_view()),
)


@fixture
def cj_renderer(request):
    return CollectionJsonRenderer()


class SimpleGetTest(TestCase):
    urls = 'tests.test_renderers'
    endpoint = ''

    def setUp(self):
        response = self.client.get(self.endpoint)
        self.collection = Collection.from_json(response.content)


class TestCollectionJsonRenderer(TestCase):
    urls = 'tests.test_renderers'

    def setUp(self):
        bob = Moron.objects.create(name='Bob LawLaw')
        Dummy.objects.create(name='Yolo McSwaggerson', moron=bob)
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

    def get_attribute(self, data, attribute_name):
        return next(x for x in data if x['name'] == attribute_name)

    def get_dummy_attribute(self, attribute_name):
        data = self.get_dummy()['data']
        return self.get_attribute(data, attribute_name)

    def test_the_dummy_item_contains_name(self):
        name = self.get_dummy_attribute('name')['value']
        self.assertEqual(name, 'Yolo McSwaggerson')

    def get_dummy_link(self, rel):
        links = self.get_dummy()['links']
        return next(x for x in links if x['rel'] == rel)

    def test_the_dummy_item_links_to_child_elements(self):
        href = self.get_dummy_link('moron')['href']
        self.assertEqual(href, 'http://testserver/rest-api/moron/1/')

    def test_link_fields_are_rendered_as_links(self):
        href = self.get_dummy_link('other_stuff')['href']
        self.assertEqual(href, 'http://other-stuff.com/')

    def test_attribute_links_are_rendered_as_links(self):
        href = self.get_dummy_link('some_link')['href']
        self.assertEqual(href, 'http://testserver/rest-api/moron/1/')

    def test_views_without_a_serializer_work(self):
        response = self.client.get('/rest-api/no-serializer/')
        content = json.loads(response.content)
        data = content['collection']['items'][0]['data']
        item = self.get_attribute(data, 'foo')
        self.assertEqual(item['value'], '1')


class TestCollectionJsonRendererPagination(SimpleGetTest):
    endpoint = '/rest-api/paginated/'

    def test_paginated_views_display_data(self):
        foo = self.collection.items[0].find(name='foo')[0]
        self.assertEqual(foo.value, 1)

    def test_paginated_views_display_next(self):
        next_link = self.collection.links.find(rel='next')[0]
        self.assertEqual(next_link.href, 'http://test.com/colleciton/next')

    def test_paginated_views_display_previous(self):
        next_link = self.collection.links.find(rel='previous')[0]
        self.assertEqual(next_link.href, 'http://test.com/colleciton/previous')


class TestCollectionJsonRendererPaginationWithnone(SimpleGetTest):
    endpoint = '/rest-api/none-paginated/'

    def test_paginated_view_does_not_display_next(self):
        self.assertEqual(len(self.collection.links.find(rel='next')), 0)

    def test_paginated_view_does_not_display_previous(self):
        self.assertEqual(len(self.collection.links.find(rel='previous')), 0)
