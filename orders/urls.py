from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('coupon/apply/', views.apply_coupon, name='apply_coupon'),
    path('success/<str:order_number>/', views.order_success, name='order_success'),
    path('', views.order_list, name='order_list'),
    path('<str:order_number>/', views.order_detail, name='order_detail'),
    path('<str:order_number>/cancel/', views.cancel_order, name='cancel_order'),

    # Admin
    path('manage/all/', views.manage_orders, name='manage_orders'),
    path('manage/<str:order_number>/status/', views.update_order_status, name='update_order_status'),
]
