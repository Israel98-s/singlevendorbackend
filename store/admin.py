from django.contrib import admin
from .models import User, Category, Product, Cart, CartItem, Order, OrderItem, Payment, Wishlist, Review, Shipping

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_vendor', 'is_staff']
    list_filter = ['is_vendor', 'is_staff']
    search_fields = ['username', 'email']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_items_count', 'get_total', 'created_at']
    search_fields = ['user__username']

    def get_items_count(self, obj):
        return obj.items.count()
    get_items_count.short_description = 'Items Count'

    def get_total(self, obj):
        return sum(item.quantity * item.product.price for item in obj.items.all())
    get_total.short_description = 'Total Price'

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'quantity']
    search_fields = ['product__name']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['user__username', 'id']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price']
    search_fields = ['product__name']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['reference', 'order', 'method', 'amount', 'status', 'created_at']
    list_filter = ['method', 'status']
    search_fields = ['reference']

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'created_at']
    search_fields = ['user__username', 'product__name']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['user__username', 'product__name']

@admin.register(Shipping)
class ShippingAdmin(admin.ModelAdmin):
    list_display = ['order', 'method', 'status', 'tracking_number', 'created_at']
    list_filter = ['status', 'method']
    search_fields = ['order__id']