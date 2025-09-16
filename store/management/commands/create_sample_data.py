from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from store.models import Category, Product, Cart, CartItem, Wishlist, Review, Order, OrderItem, Shipping, StoreSettings
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates sample data for the e-commerce application'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("Creating sample data...")

        # Create superuser
        if not User.objects.filter(email='admin@ecommerce.com').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@ecommerce.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                is_vendor=True
            )
            StoreSettings.objects.create(user=admin, store_name='Admin Store')
            self.stdout.write("Superuser created: admin@ecommerce.com / admin123")
        else:
            admin = User.objects.get(email='admin@ecommerce.com')

        # Create regular user
        if not User.objects.filter(email='testuser@example.com').exists():
            user = User.objects.create_user(
                username='testuser',
                email='testuser@example.com',
                password='password123',
                first_name='Test',
                last_name='User'
            )
            Cart.objects.create(user=user)
            StoreSettings.objects.create(user=user, store_name='Test User Store')
            self.stdout.write("Test user created: testuser@example.com / password123")
        else:
            user = User.objects.get(email='testuser@example.com')

        # Create categories
        categories = [
            {'name': 'Electronics', 'description': 'Electronic gadgets and devices'},
            {'name': 'Clothing', 'description': 'Fashion and apparel'},
            {'name': 'Books', 'description': 'Books and literature'},
        ]
        for cat_data in categories:
            Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )

        electronics = Category.objects.get(name='Electronics')
        clothing = Category.objects.get(name='Clothing')
        books = Category.objects.get(name='Books')

        # Create products
        products = [
            {
                'name': 'Smartphone',
                'description': 'Latest model smartphone with advanced features',
                'price': 699.99,
                'stock': 50,
                'category': electronics,
            },
            {
                'name': 'T-Shirt',
                'description': 'Comfortable cotton t-shirt',
                'price': 19.99,
                'stock': 100,
                'category': clothing,
            },
            {
                'name': 'Python Programming Book',
                'description': 'Comprehensive guide to Python programming',
                'price': 39.99,
                'stock': 30,
                'category': books,
            },
        ]
        for prod_data in products:
            Product.objects.get_or_create(
                name=prod_data['name'],
                defaults={
                    'description': prod_data['description'],
                    'price': prod_data['price'],
                    'stock': prod_data['stock'],
                    'category': prod_data['category'],
                    'is_active': True
                }
            )

        # Create sample wishlist
        smartphone = Product.objects.get(name='Smartphone')
        Wishlist.objects.get_or_create(user=user, product=smartphone)

        # Create sample review
        Review.objects.get_or_create(
            user=user,
            product=smartphone,
            defaults={'rating': 5, 'comment': 'Great phone!'}
        )

        # Create sample order
        order = Order.objects.create(
            user=user,
            total_amount=739.98,
            shipping_address='123 Test Street, Test City',
            status='pending'
        )
        OrderItem.objects.create(
            order=order,
            product=smartphone,
            quantity=1,
            price=699.99
        )
        OrderItem.objects.create(
            order=order,
            product=Product.objects.get(name='Python Programming Book'),
            quantity=1,
            price=39.99
        )

        # Create sample shipping
        Shipping.objects.create(
            order=order,
            method='Standard Shipping',
            status='pending'
        )

        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))