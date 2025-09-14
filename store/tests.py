from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Category, Product, Wishlist, Review, Shipping, Order, OrderItem

User = get_user_model()

class EcommerceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            is_vendor=True
        )
        self.category = Category.objects.create(name='Electronics', description='Electronic items')
        self.product = Product.objects.create(
            name='Test Product',
            description='A test product',
            price=99.99,
            stock=10,
            category=self.category,
            is_active=True
        )

    def test_wishlist_add_remove(self):
        self.client.login(email='testuser@example.com', password='password123')
        response = self.client.post('/api/wishlist/add/', {'product_id': self.product.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Wishlist.objects.filter(user=self.user, product=self.product).exists())

        response = self.client.post('/api/wishlist/remove/', {'product_id': self.product.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Wishlist.objects.filter(user=self.user, product=self.product).exists())

    def test_review_create(self):
        self.client.login(email='testuser@example.com', password='password123')
        review_data = {
            'product_id': self.product.id,
            'rating': 5,
            'comment': 'Great product!'
        }
        response = self.client.post('/api/reviews/', review_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Review.objects.filter(user=self.user, product=self.product, rating=5).exists())

    def test_shipping_create_and_update(self):
        order = Order.objects.create(
            user=self.user,
            total_amount=99.99,
            shipping_address='123 Test St',
            status='pending'
        )
        OrderItem.objects.create(order=order, product=self.product, quantity=1, price=99.99)

        shipping = Shipping.objects.create(order=order, method='Standard Shipping', status='pending')
        
        self.client.login(email='admin@example.com', password='admin123')
        update_data = {'tracking_number': 'TRACK123', 'status': 'shipped'}
        response = self.client.put(f'/api/orders/{order.id}/shipping/update/', update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        shipping.refresh_from_db()
        self.assertEqual(shipping.tracking_number, 'TRACK123')
        self.assertEqual(shipping.status, 'shipped')