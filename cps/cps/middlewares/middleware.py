import re
from django.http import HttpResponseRedirect
from cps import settings


class LoginRequiredMiddleware(object):
    def __init__(self):
        self.exceptions = tuple(re.compile(url) for url in settings.LOGIN_REQUIRED_URLS_EXCEPTIONS)

    def process_request(self, request):
        if not request.user.is_authenticated():
            for url in self.exceptions:
                if url.match(request.path):
                    return None
            return HttpResponseRedirect((settings.LOGIN_URL + '?next=%s') % request.path)
        return None
