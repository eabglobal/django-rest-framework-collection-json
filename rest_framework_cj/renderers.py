from rest_framework.renderers import JSONRenderer


class CollectionJsonRenderer(JSONRenderer):
    media_type = 'application/vnd.collection+json'
    format = 'collection+json'

    def _get_response_body(self, href, data):
        return {
            "collection":
            {
                "version": "1.0",
                "href": href,
                "links": [],
                "items": [data],
                "queries": [],
                "template": {},
                "error": {},
            }
        }

    def render(self, data, media_type=None, renderer_context=None):
        request = renderer_context['request']
        href = request.build_absolute_uri()

        data = self._get_response_body(href, data)

        return super(CollectionJsonRenderer, self).render(data, media_type,
                                                          renderer_context)
