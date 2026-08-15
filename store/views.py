from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Min, Max
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from decimal import Decimal

from .models import Product, Category, Brand, Wishlist, Review
from .cart import Cart
from .forms import CartAddProductForm, ReviewForm, SearchForm


def home(request):
    featured = Product.objects.filter(is_featured=True, is_available=True)[:8]
    latest = Product.objects.filter(is_available=True).order_by('-created_at')[:8]
    categories = Category.objects.filter(is_active=True)[:6]
    return render(request, 'store/home.html', {
        'featured_products': featured,
        'latest_products': latest,
        'categories': categories,
    })


def product_list(request, category_slug=None):
    category = None
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.all()

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(category=category)

    # Filters
    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(brand__name__icontains=query)
        )

    brand_id = request.GET.get('brand')
    if brand_id:
        products = products.filter(brand_id=brand_id)

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            products = products.filter(price__gte=Decimal(min_price))
        except Exception:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=Decimal(max_price))
        except Exception:
            pass

    sort = request.GET.get('sort', 'newest')
    sort_map = {
        'newest': '-created_at',
        'price_asc': 'price',
        'price_desc': '-price',
        'name': 'name',
    }
    products = products.order_by(sort_map.get(sort, '-created_at'))

    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    products_page = paginator.get_page(page)

    return render(request, 'store/product_list.html', {
        'category': category,
        'categories': categories,
        'brands': brands,
        'products': products_page,
        'query': query,
        'sort': sort,
        'selected_brand': int(brand_id) if brand_id else None,
        'min_price': min_price or '',
        'max_price': max_price or '',
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)
    related = Product.objects.filter(category=product.category, is_available=True).exclude(id=product.id)[:4]
    cart_form = CartAddProductForm()
    reviews = product.reviews.all()
    review_form = ReviewForm()
    user_has_reviewed = False
    if request.user.is_authenticated:
        user_has_reviewed = reviews.filter(user=request.user).exists()

    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related,
        'cart_form': cart_form,
        'reviews': reviews,
        'review_form': review_form,
        'user_has_reviewed': user_has_reviewed,
    })


def search(request):
    return product_list(request)


# ---------- Cart ----------
@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id, is_available=True)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product, quantity=cd['quantity'], update_quantity=cd['update'])
        messages.success(request, f"{product.name} added to cart.")
    return redirect('store:cart_detail')


def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.info(request, f"{product.name} removed from cart.")
    return redirect('store:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(initial={
            'quantity': item['quantity'],
            'update': True,
        })
    return render(request, 'store/cart_detail.html', {'cart': cart})


def cart_clear(request):
    cart = Cart(request)
    cart.clear()
    messages.info(request, "Cart cleared.")
    return redirect('store:cart_detail')


# ---------- Wishlist ----------
@login_required
def wishlist_view(request):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    return render(request, 'store/wishlist.html', {'wishlist': wishlist})


@login_required
def wishlist_toggle(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    if product in wishlist.products.all():
        wishlist.products.remove(product)
        messages.info(request, f"{product.name} removed from wishlist.")
    else:
        wishlist.products.add(product)
        messages.success(request, f"{product.name} added to wishlist.")
    next_url = request.META.get('HTTP_REFERER', 'store:product_list')
    return redirect(next_url)


# ---------- Reviews ----------
@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if Review.objects.filter(product=product, user=request.user).exists():
        messages.warning(request, "You already reviewed this product.")
        return redirect(product.get_absolute_url())
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Thanks! Your review has been posted.")
            return redirect(product.get_absolute_url())
    return redirect(product.get_absolute_url())
