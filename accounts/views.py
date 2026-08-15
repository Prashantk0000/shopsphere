from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse

from .forms import RegisterForm, LoginForm, ProfileForm, AddressForm
from .models import Customer, Address
from orders.models import Order


def register_view(request):
    if request.user.is_authenticated:
        return redirect('store:home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Customer.objects.get_or_create(user=user, defaults={'role': 'customer'})
            login(request, user)
            messages.success(request, f"Welcome to ShopSphere, {user.first_name}!")
            return redirect('store:home')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('store:home')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next') or 'store:home'
            return redirect(next_url)
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('store:home')


@login_required
def profile_view(request):
    profile, _ = Customer.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    addresses = request.user.addresses.all()
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'accounts/profile.html', {
        'form': form,
        'profile': profile,
        'orders': orders,
        'addresses': addresses,
    })


@login_required
def address_list(request):
    addresses = request.user.addresses.all()
    return render(request, 'accounts/address_list.html', {'addresses': addresses})


@login_required
def address_add(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            addr = form.save(commit=False)
            addr.user = request.user
            if addr.is_default:
                request.user.addresses.filter(address_type=addr.address_type).update(is_default=False)
            addr.save()
            messages.success(request, "Address added.")
            return redirect('accounts:address_list')
    else:
        form = AddressForm()
    return render(request, 'accounts/address_form.html', {'form': form, 'action': 'Add'})


@login_required
def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated.")
            return redirect('accounts:address_list')
    else:
        form = AddressForm(instance=address)
    return render(request, 'accounts/address_form.html', {'form': form, 'action': 'Edit'})


@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.delete()
    messages.info(request, "Address deleted.")
    return redirect('accounts:address_list')


# ---------- Admin dashboard (role-based) ----------
def is_admin_user(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    try:
        return user.profile.role == 'admin'
    except Customer.DoesNotExist:
        return False


@user_passes_test(is_admin_user)
def admin_dashboard(request):
    from store.models import Product, Category
    from django.contrib.auth.models import User
    context = {
        'total_products': Product.objects.count(),
        'total_categories': Category.objects.count(),
        'total_orders': Order.objects.count(),
        'total_users': User.objects.count(),
        'recent_orders': Order.objects.order_by('-created_at')[:10],
        'low_stock': Product.objects.filter(stock__lt=5).order_by('stock')[:10],
    }
    return render(request, 'accounts/admin_dashboard.html', context)
