from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Category, Product, Cart, CartItem, Order, OrderItem, Payment, Wishlist, Review, Shipping, StoreSettings

# Custom AdminSite to display store name
class CustomAdminSite(admin.AdminSite):
    def each_context(self, request):
        context = super().each_context(request)
        if request.user.is_authenticated:
            try:
                store_settings = request.user.store_settings
                context['site_title'] = store_settings.store_name
                context['site_header'] = f"{store_settings.store_name} Admin"
            except StoreSettings.DoesNotExist:
                context['site_title'] = 'E-commerce Admin'
                context['site_header'] = 'E-commerce Admin'
        else:
            context['site_title'] = 'E-commerce Admin'
            context['site_header'] = 'E-commerce Admin'
        return context

# Instantiate custom admin site
custom_admin_site = CustomAdminSite(name='custom_admin')

# Register models with custom admin site
custom_admin_site.register(User, BaseUserAdmin)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']

custom_admin_site.register(Category, CategoryAdmin)

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']

custom_admin_site.register(Product, ProductAdmin)

class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_items_count', 'get_total', 'created_at']
    search_fields = ['user__username']

    def get_items_count(self, obj):
        return obj.items.count()
    get_items_count.short_description = 'Items Count'

    def get_total(self, obj):
        return sum(item.quantity * item.product.price for item in obj.items.all())
    get_total.short_description = 'Total Price'

custom_admin_site.register(Cart, CartAdmin)

class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity']
    search_fields = ['product__name']

custom_admin_site.register(CartItem, CartItemAdmin)

class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['user__username', 'id']

custom_admin_site.register(Order, OrderAdmin)

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price']
    search_fields = ['product__name']

custom_admin_site.register(OrderItem, OrderItemAdmin)

class PaymentAdmin(admin.ModelAdmin):
    list_display = ['reference', 'order', 'method', 'amount', 'status', 'created_at']
    list_filter = ['method', 'status']
    search_fields = ['reference']

custom_admin_site.register(Payment, PaymentAdmin)

class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    search_fields = ['user__username', 'product__name']

custom_admin_site.register(Wishlist, WishlistAdmin)

class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['user__username', 'product__name']

custom_admin_site.register(Review, ReviewAdmin)

class ShippingAdmin(admin.ModelAdmin):
    list_display = ['order', 'method', 'status', 'tracking_number', 'created_at']
    list_filter = ['status', 'method']
    search_fields = ['order__id']

custom_admin_site.register(Shipping, ShippingAdmin)

class StoreSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'store_name', 'created_at']
    search_fields = ['user__username', 'store_name']
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(user=request.user)
        return qs

custom_admin_site.register(StoreSettings, StoreSettingsAdmin)