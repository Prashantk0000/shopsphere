from .cart import Cart
from .models import Category


def cart_context(request):
    cart = Cart(request)
    return {
        'cart_total_items': len(cart),
        'cart_total_price': cart.get_total_price(),
    }


def categories_context(request):
    return {
        'nav_categories': Category.objects.filter(is_active=True)[:10],
    }
