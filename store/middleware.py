from django.conf import settings


class CartMiddleware:
    """Ensure cart session key exists for every request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.session.get(settings.CART_SESSION_ID):
            request.session[settings.CART_SESSION_ID] = {}
        return self.get_response(request)
