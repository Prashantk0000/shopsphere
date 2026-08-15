from django.contrib import admin
from .models import Customer, Address


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone', 'created_at')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email', 'phone')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'address_type', 'is_default')
    list_filter = ('address_type', 'is_default', 'country')
    search_fields = ('user__username', 'full_name', 'city')
