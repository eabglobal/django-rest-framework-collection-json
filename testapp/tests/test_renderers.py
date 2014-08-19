from six.moves.urllib.parse import urljoin

import django
if django.VERSION[0] == 1 and django.VERSION[1] == 3:
    from django.conf.urls.defaults import patterns, include
else:
    from django.conf.urls import patterns, include

from django.test import TestCase

from collection_json import Collection
from rest_framework import status
from rest_framework.exceptions import ParseError
from rest_framework.relations import HyperlinkedIdentityField
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.serializers import (
    HyperlinkedModelSerializer, ModelSerializer
)
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from rest_framework_cj.renderers import CollectionJsonRenderer
from rest_framework_cj.fields import LinkField

from testapp.models import Dummy, Idiot, Moron, Simple


class MoronHyperlinkedModelSerializer(HyperlinkedModelSerializer):
    class Meta(object):
        model = Moron
        fields = ('url', 'name')


class MoronReadOnlyModelViewSet(ReadOnlyModelViewSet):
    renderer_classes = (CollectionJsonRenderer, )
    queryset = Moron.objects.all()
    serializer_class = MoronHyperlinkedModelSerializer


class IdiotHyperlinkedModelSerializer(HyperlinkedModelSerializer):
    class Meta(object):
        model = Idiot
        fields = ('url', 'name')


class IdiotReadOnlyModelViewSet(ReadOnlyModelViewSet):
    renderer_classes = (CollectionJsonRenderer, )
    queryset = Idiot.objects.all()
    serializer_class = IdiotHyperlinkedModelSerializer


class DummyHyperlinkedModelSerializer(HyperlinkedModelSerializer):
    other_stuff = LinkField('get_other_link')
    empty_link = LinkField('get_empty_link')
    some_link = HyperlinkedIdentityField(view_name='moron-detail')

    class Meta(object):
        model = Dummy
        fields = ('url', 'name', 'moron', 'idiots', 'other_stuff', 'some_link', 'empty_link')

    def get_other_link(self, obj):
        return 'http://other-stuff.com/'

    def get_empty_link(self, obj):
        return None


class DummyReadOnlyModelViewSet(ReadOnlyModelViewSet):
    renderer_classes = (CollectionJsonRenderer, )
    queryset = Dummy.objects.all()
    serializer_class = DummyHyperlinkedModelSerializer


class NoSerializerView(APIView):
    renderer_classes = (CollectionJsonRenderer, )

    def get(self, request):
        return Response({'foo': '1'})


class SimpleGetTest(TestCase):
    urls = 'testapp.tests.test_renderers'
    endpoint = ''

    def setUp(self):
        self.response = self.client.get(self.endpoint)
        self.collection = Collection.from_json(self.response.content.decode('utf8'))


def create_models():
    bob = Moron.objects.create(name='Bob LawLaw')
    dummy = Dummy.objects.create(name='Yolo McSwaggerson', moron=bob)
    dummy.idiots.add(Idiot.objects.create(name='frick'))
    dummy.idiots.add(Idiot.objects.create(name='frack'))


class TestCollectionJsonRenderer(SimpleGetTest):
    endpoint = '/rest-api/dummy/'

    def setUp(self):
        create_models()
        super(TestCollectionJsonRenderer, self).setUp()

    def test_it_has_the_right_response_code(self):
        self.assertEqual(self.response.status_code, status.HTTP_200_OK)

    def test_it_has_the_right_content_type(self):
        content_type = self.response['Content-Type']
        self.assertEqual(content_type, 'application/vnd.collection+json')

    def test_it_has_the_version_number(self):
        self.assertEqual(self.collection.version, '1.0')

    def test_it_has_an_href(self):
        href = self.collection.href
        self.assertEqual(href, 'http://testserver/rest-api/dummy/')

    def get_dummy(self):
        return self.collection.items[0]

    def test_the_dummy_item_has_an_href(self):
        href = self.get_dummy().href
        self.assertEqual(href, 'http://testserver/rest-api/dummy/1/')

    def test_the_dummy_item_contains_name(self):
        name = self.get_dummy().data.find('name')[0].value
        self.assertEqual(name, 'Yolo McSwaggerson')

    def get_dummy_link(self, rel):
        links = self.get_dummy()['links']
        return next(x for x in links if x['rel'] == rel)

    def test_the_dummy_item_links_to_child_elements(self):
        href = self.get_dummy().links.find(rel='moron')[0].href
        self.assertEqual(href, 'http://testserver/rest-api/moron/1/')

    def test_link_fields_are_rendered_as_links(self):
        href = self.get_dummy().links.find(rel='other_stuff')[0].href
        self.assertEqual(href, 'http://other-stuff.com/')

    def test_empty_link_fields_are_not_rendered_as_links(self):
        links = self.get_dummy().links.find(rel='empty_link')
        self.assertEqual(len(links), 0)

    def test_attribute_links_are_rendered_as_links(self):
        href = self.get_dummy().links.find(rel='some_link')[0].href
        self.assertEqual(href, 'http://testserver/rest-api/moron/1/')

    def test_many_to_many_relationships_are_rendered_as_links(self):
        idiots = self.get_dummy().links.find(rel='idiots')
        self.assertEqual(idiots[0].href, 'http://testserver/rest-api/idiot/1/')
        self.assertEqual(idiots[1].href, 'http://testserver/rest-api/idiot/2/')


class TestNoSerializerViews(SimpleGetTest):
    endpoint = '/rest-api/no-serializer/'

    def setUp(self):
        create_models()
        super(TestNoSerializerViews, self).setUp()

    def test_views_without_a_serializer_work(self):
        value = self.collection.items[0].data.find('foo')[0].value
        self.assertEqual(value, '1')


class SimpleModelSerializer(ModelSerializer):

    class Meta(object):
        model = Dummy
        fields = ('name', )


class SimpleViewSet(ReadOnlyModelViewSet):
    renderer_classes = (CollectionJsonRenderer, )
    queryset = Simple.objects.all()
    serializer_class = SimpleModelSerializer


class TestNormalModels(SimpleGetTest):
    endpoint = '/rest-api/normal-model/'

    def setUp(self):
        Simple.objects.create(name='Foobar Baz')
        super(TestNormalModels, self).setUp()

    def test_items_dont_have_a_href(self):
        href_count = len(self.collection.items[0].find(name='href'))
        self.assertEqual(href_count, 0)


class PaginatedDataView(APIView):
    renderer_classes = (CollectionJsonRenderer, )

    def get(self, request):
        return Response({
            'next': 'http://test.com/colleciton/next',
            'previous': 'http://test.com/colleciton/previous',
            'results': [{'foo': 1}],
        })


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


class NonePaginatedDataView(APIView):
    renderer_classes = (CollectionJsonRenderer, )

    def get(self, request):
        return Response({
            'next': None,
            'previous': None,
            'results': [{'foo': 1}],
        })


class TestCollectionJsonRendererPaginationWithNone(SimpleGetTest):
    endpoint = '/rest-api/none-paginated/'

    def test_paginated_view_does_not_display_next(self):
        self.assertEqual(len(self.collection.links.find(rel='next')), 0)

    def test_paginated_view_does_not_display_previous(self):
        self.assertEqual(len(self.collection.links.find(rel='previous')), 0)


class ParseErrorView(APIView):
    renderer_classes = (CollectionJsonRenderer, )

    def get(self, request):
        raise ParseError('lol nice one')


class TestErrorHandling(SimpleGetTest):
    endpoint = '/rest-api/parse-error/'

    def test_errors_are_reported(self):
        self.assertEqual(self.collection.error.message, 'lol nice one')


class UrlRewriteRenderer(CollectionJsonRenderer):
    def get_href(self, request):
        return urljoin('http://rewritten.com', request.path)


class UrlRewriteView(APIView):
    renderer_classes = (UrlRewriteRenderer, )

    def get(self, request):
        return Response({'foo': 'bar'})


class TestUrlRewrite(SimpleGetTest):
    endpoint = '/rest-api/url-rewrite/'

    def test_the_href_url_can_be_rewritten(self):
        rewritten_url = "http://rewritten.com/rest-api/url-rewrite/"
        self.assertEqual(self.collection.href, rewritten_url)


class EmptyView(APIView):
    renderer_classes = (CollectionJsonRenderer, )

    def get(self, request):
        return Response(status=HTTP_204_NO_CONTENT)


class TestEmpty(TestCase):
    urls = 'testapp.tests.test_renderers'

    def test_empty_content_works(self):
        response = self.client.get('/rest-api/empty/')
        self.assertEqual(response.status_code, HTTP_204_NO_CONTENT)
        self.assertEqual(response.content.decode('utf8'), '')


router = DefaultRouter()
router.register('dummy', DummyReadOnlyModelViewSet)
router.register('moron', MoronReadOnlyModelViewSet)
router.register('idiot', IdiotReadOnlyModelViewSet)
router.register('normal-model', SimpleViewSet)
urlpatterns = patterns(
    '',
    (r'^rest-api/', include(router.urls)),
    (r'^rest-api/no-serializer/', NoSerializerView.as_view()),
    (r'^rest-api/paginated/', PaginatedDataView.as_view()),
    (r'^rest-api/none-paginated/', NonePaginatedDataView.as_view()),
    (r'^rest-api/parse-error/', ParseErrorView.as_view()),
    (r'^rest-api/url-rewrite/', UrlRewriteView.as_view()),
    (r'^rest-api/empty/', EmptyView.as_view()),
)
