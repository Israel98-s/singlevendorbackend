from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/logout/', views.logout, name='logout'),
    path('auth/forgot-password/', views.forgot_password, name='forgot_password'),
    path('auth/reset-password/', views.reset_password, name='reset_password'),
    path('auth/profile/', views.profile, name='profile'),
    
    path('products/', views.ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', views.ProductRetrieveUpdateDestroyView.as_view(), name='product-detail'),
    path('products/<int:pk>/delete-image/', views.delete_product_image, name='delete-product-image'),
    path('categories/', views.CategoryListCreateView.as_view(), name='category-list-create'),
    
    path('cart/', views.get_cart, name='get_cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    path('wishlist/', views.get_wishlist, name='get_wishlist'),
    path('wishlist/add/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/', views.remove_from_wishlist, name='remove_from_wishlist'),
    
    path('reviews/', views.ReviewListCreateView.as_view(), name='review-list-create'),
    path('reviews/<int:pk>/', views.ReviewRetrieveUpdateDestroyView.as_view(), name='review-detail'),
    
    path('orders/', views.list_orders, name='list_orders'),
    path('orders/<uuid:order_id>/', views.get_order, name='get_order'),
    path('orders/create/', views.create_order, name='create_order'),
    path('orders/<uuid:order_id>/status/', views.update_order_status, name='update_order_status'),
    
    path('orders/<uuid:order_id>/shipping/', views.get_shipping, name='get_shipping'),
    path('orders/<uuid:order_id>/shipping/update/', views.update_shipping, name='update_shipping'),
    
    path('payments/initiate/', views.initiate_payment, name='initiate_payment'),
    path('payments/verify/', views.verify_payment, name='verify_payment'),
    path('payments/history/', views.payment_history, name='payment_history'),
    
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/orders/', views.admin_orders, name='admin_orders'),
]