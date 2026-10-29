from django.conf import settings
from django.utils import translation


class QueryLanguageMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        self.supported = {code for code, _ in settings.LANGUAGES}

    def __call__(self, request):
        lang = request.GET.get("lang")
        if lang in self.supported:
            translation.activate(lang)
            request.LANGUAGE_CODE = lang
        return self.get_response(request)
