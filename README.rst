=======================================
Django Rest Framework - Collection+JSON
=======================================

.. image:: https://travis-ci.org/advisory/django-rest-framework-collection-json.svg?branch=master
    :target: https://travis-ci.org/advisory/django-rest-framework-collection-json

This library adds support for the Collection+JSON hypermedia format to Django Rest Framework. For more information on Collection+JSON see the `official Collection+JSON documentation <http://amundsen.com/media-types/collection/>`_.

Installation
============

Install django-rest-framework-collection-json with pip::

    pip install django-rest-framework-collection-json


Usage
=====

To enable the Collection+JSON renderer, either add it as a default renderer in your django settings file::

    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework_cj.renderers.CollectionJsonRenderer',
    )


or explicitly set the renderer on your view::

    class MyViewSet(ReadOnlyModelViewSet):
        renderer_classes = (CollectionJsonRenderer, )

Renderer Behavior
=================

The Collection+JSON renderer will do it's best to support the built in Django Rest Framework Serializers and Views. However, the renderer is designed to work with Django Rest Framework's hyperlinked views/serializers.

Given a simple model and an associated view/serializer::

    class Dummy(Model):
        name = CharField(max_length='100')

    class DummyHyperlinkedModelSerializer(HyperlinkedModelSerializer):
        class Meta(object):
            model = Dummy
            fields = ('url', 'name', )

    class DummyReadOnlyModelViewSet(ReadOnlyModelViewSet):
        renderer_classes = (CollectionJsonRenderer, )
        queryset = Dummy.objects.all()
        serializer_class = DummyHyperlinkedModelSerializer

If you register the view as follows::

    router = DefaultRouter()
    router.register('dummy', DummyReadOnlyModelViewSet)
    urlpatterns = patterns(
        '',
        (r'^rest-api/', include(router.urls)),
    )

Navigating to the url /rest-api/dummy/ will generate a collection+JSON containing serialized dummy objects in it's items array.::

    "items": [
        {
            "href": "http://foobar.com/rest-api/dummy/1"/,
            "data": [
                {
                    "name": "name",
                    "value": "foo"
                },
            ]
        },
        {
            "href": "http://foobar.com/rest-api/dummy/2/",
            "data": [
                {
                    "name": "name",
                    "value": "bar"
                },
            ]
        }
    ]

Foreign key/Many to Many relationships will be rendered in an item's links array::

    children = ManyToManyField('Child')

    "links": [
        {
            "href": "http://foobar.com/rest-api/child/1/",
            "rel": "children"
        },
        {
            "href": "http://foobar.com/rest-api/child/2/",
            "rel": "children"
        },
    ]

The renderer will also recognize the default router and provide links its resources::

    {
        "collection": {
            "href": "http://foobar.com/rest-api/",
            "items": [],
            "version": "1.0",
            "links": [
                {
                    "href": "http://foobar.com/rest-api/dummy/",
                    "rel": "dummy"
                },
            ]
        }
    }

Link Fields
===========

Django Rest Framework Colleciton+JSON also includes a new LinkField class for linking to arbitrary resources.::

    class DummyHyperlinkedModelSerializer(HyperlinkedModelSerializer):
        related_link = LinkField('get_related_link')

        class Meta(object):
            model = Dummy
            fields = ('url', 'name', 'related_link')

        def get_related_link(self, obj):
            return 'http://something-relavent.com/'

    "items": [
        {
            "href": "http://foobar.com/rest-api/dummy/1"/,
            "data": [
                {
                    "name": "name",
                    "value": "foo"
                },
            ],
            "links": [
                {
                    "rel": 'related_link',
                    "href": 'http://something-relavent.com',
                }
            ]
        },
    ]

Unit Testing
============

You can run the unit tests against your current environment by running::

    $ python setup.py test

You can also use tox::

    $ tox

The build environments in the tox configuration are designed to match the builds supported by Django Rest Framework.
