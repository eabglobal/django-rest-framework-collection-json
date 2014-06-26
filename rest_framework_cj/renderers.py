from rest_framework.relations import (
    HyperlinkedRelatedField,
    HyperlinkedIdentityField,
)
from rest_framework.renderers import JSONRenderer


class CollectionJsonRenderer(JSONRenderer):
    media_type = 'application/vnd.collection+json'
    format = 'collection+json'

    def _transform_field(self, key, value):
        return {'name': key, 'value': value}

    def _get_id_field(self, fields):
        try:
            return next(k for (k, v) in fields
                        if isinstance(v, HyperlinkedIdentityField))
        except StopIteration:
            return None

    def _get_related_fields(self, fields):
        return [k for (k, v) in fields
                if isinstance(v, HyperlinkedRelatedField)]

    def _transform_item(self, serializer, item):
        fields = serializer.fields.items()
        id_field = self._get_id_field(fields)
        related_fields = self._get_related_fields(fields)

        data = [self._transform_field(k, item[k])
                for k in item.keys()
                if k != id_field and k not in related_fields]
        result = {'data': data}

        if id_field:
            result['href'] = item[id_field]

        links = [{'rel': x, 'href': item[x]} for x in related_fields]
        if links:
            result['links'] = links

        return result

    def _transform_items(self, view, data):
        serializer = view.get_serializer()

        if isinstance(data, list):
            items = map(lambda x: self._transform_item(serializer, x), data)
        elif isinstance(data, dict):
            items = [self._transform_item(serializer, data)]

        return items

    def _transform_data(self, request, view, data):
        href = request.build_absolute_uri()

        # ------------------------------------------
        #          ______   ___  ______
        #           )_   \ '-,) /   _(
        #             )_  \_//_/  _(
        #               )___  ___(
        #                   ))
        #                  ((
        #                   ``-
        #  HC SVNT DRACONES (et debitum technica)
        # ------------------------------------------
        # This lookup of the Api Root string isn't
        # the right long-term approach. Even if we
        # looked it up properly from the default
        # router, we would still need to handle
        # custom routers. Works okay for now.
        # ------------------------------------------
        if view.get_view_name() == 'Api Root':
            {'practices': 'http://localhost:8001/rest-api/practices/', 'members': 'http://localhost:8001/rest-api/members/'}
            links = [{'rel': key, 'href': data[key]} for key in data.keys()]
            items = []
        else:
            items =self._transform_items(view, data)
            links = []

        return {
            "collection":
            {
                "version": "1.0",
                "href": href,
                "links": links,
                "items": items,
                "queries": [],
                "template": {},
                "error": {},
            }
        }

    def render(self, data, media_type=None, renderer_context=None):
        request = renderer_context['request']
        view = renderer_context['view']

        data = self._transform_data(request, view, data)

        return super(CollectionJsonRenderer, self).render(data, media_type,
                                                          renderer_context)
