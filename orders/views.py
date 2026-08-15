from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from django.http import HttpResponseForbidden

from store.cart import Cart
from store.models import Coupon, Product
from .models import Order, OrderItem, Payment, InventoryLog
from .forms import CheckoutForm, PaymentForm, CouponApplyForm
from accounts.views import is_admin_user


@login_required
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect('store:product_list')

    coupon_id = request.session.get('coupon_id')
    coupon = None
    discount = Decimal('0.00')
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            if coupon.is_valid():
                discount = (cart.get_total_price() * Decimal(coupon.discount_percent) / Decimal(100)).quantize(Decimal('0.01'))
            else:
                coupon = None
        except Coupon.DoesNotExist:
            coupon = None

    shipping = Decimal('0.00') if cart.get_total_price() >= Decimal('999') else Decimal('49.00')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        payment_form = PaymentForm(request.POST)
        if form.is_valid() and payment_form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.coupon = coupon
            order.discount = discount
            order.shipping_cost = shipping
            order.save()

            for item in cart:
                product = item['product']
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    price=item['price'],
                    quantity=item['quantity'],
                )
                # Reduce stock and log
                if product.stock >= item['quantity']:
                    product.stock -= item['quantity']
                    product.save(update_fields=['stock'])
                    InventoryLog.objects.create(
                        product=product, action='sale', quantity=item['quantity'],
                        note=f"Order {order.order_number}"
                    )

            # Payment
            payment = payment_form.save(commit=False)
            payment.order = order
            payment.amount = order.get_total()
            if payment.method == 'cod':
                payment.status = 'pending'
                order.status = 'processing'
            else:
                # Simulate a successful gateway response
                payment.status = 'completed'
                payment.transaction_id = 'TXN' + order.order_number
                order.status = 'paid'
            payment.save()
            order.save(update_fields=['status'])

            # Clear cart + coupon
            cart.clear()
            if 'coupon_id' in request.session:
                del request.session['coupon_id']

            messages.success(request, f"Order {order.order_number} placed successfully!")
            return redirect('orders:order_success', order_number=order.order_number)
    else:
        # Prefill from user's default address if available
        initial = {'full_name': request.user.get_full_name() or request.user.username, 'email': request.user.email}
        default_addr = request.user.addresses.filter(is_default=True, address_type='shipping').first()
        if default_addr:
            initial.update({
                'full_name': default_addr.full_name,
                'phone': default_addr.phone,
                'address': default_addr.street_address,
                'city': default_addr.city,
                'state': default_addr.state,
                'postal_code': default_addr.postal_code,
                'country': default_addr.country,
            })
        form = CheckoutForm(initial=initial)
        payment_form = PaymentForm()

    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'form': form,
        'payment_form': payment_form,
        'coupon': coupon,
        'discount': discount,
        'shipping': shipping,
        'coupon_form': CouponApplyForm(),
        'grand_total': cart.get_total_price() - discount + shipping,
    })


def apply_coupon(request):
    now = timezone.now()
    form = CouponApplyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        code = form.cleaned_data['code'].strip()
        try:
            coupon = Coupon.objects.get(
                code__iexact=code, valid_from__lte=now, valid_until__gte=now, active=True
            )
            request.session['coupon_id'] = coupon.id
            messages.success(request, f"Coupon '{coupon.code}' applied — {coupon.discount_percent}% off.")
        except Coupon.DoesNotExist:
            request.session['coupon_id'] = None
            messages.error(request, "Invalid or expired coupon code.")
    return redirect('orders:checkout')


@login_required
def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/order_success.html', {'order': order})


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user)
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if order.user != request.user and not is_admin_user(request.user):
        return HttpResponseForbidden("You cannot view this order.")
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def cancel_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if order.status in ('pending', 'paid', 'processing'):
        order.status = 'cancelled'
        order.save(update_fields=['status'])
        # Restock
        for item in order.items.all():
            if item.product:
                item.product.stock += item.quantity
                item.product.save(update_fields=['stock'])
                InventoryLog.objects.create(
                    product=item.product, action='return', quantity=item.quantity,
                    note=f"Cancel order {order.order_number}"
                )
        messages.info(request, f"Order {order.order_number} cancelled.")
    else:
        messages.warning(request, "This order cannot be cancelled anymore.")
    return redirect('orders:order_detail', order_number=order.order_number)


# ---------- Admin views ----------
@user_passes_test(is_admin_user)
def manage_orders(request):
    status = request.GET.get('status', '')
    orders = Order.objects.all()
    if status:
        orders = orders.filter(status=status)
    return render(request, 'orders/manage_orders.html', {
        'orders': orders,
        'status_filter': status,
        'status_choices': Order.STATUS_CHOICES,
    })


@user_passes_test(is_admin_user)
def update_order_status(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save(update_fields=['status'])
            messages.success(request, f"Order {order.order_number} → {new_status}.")
    return redirect('orders:manage_orders')
