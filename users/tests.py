from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from store.models import Category, Product, Wishlist, Review, Order, Shipping

User = get_user_model()

class EcommerceTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='testuser@ecommerce.com',
            username='testuser',
            password='test123'
        )
        self.admin = User.objects.create_superuser(
            email='admin@ecommerce.com',
            username='admin',
            password='admin123',
            is_vendor=True
        )
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            name='Test Product',
            price=99.99,
            stock=10,
            category=self.category
        )
    
    def test_add_to_wishlist(self):
        self.client.login(email='testuser@ecommerce.com', password='test123')
        response = self.client.post('/api/wishlist/add/', {'product_id': self.product.id})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Wishlist.objects.count(), 1)
    
    def test_create_review(self):
        self.client.login(email='testuser@ecommerce.com', password='test123')
        response = self.client.post('/api/reviews/', {
            'product': self.product.id,
            'rating': 5,
            'comment': 'Great product!'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Review.objects.count(), 1)
    
    def test_update_shipping_admin(self):
        order = Order.objects.create(
            user=self.user,
            total_amount=99.99,
            shipping_address='123 Test St'
        )
        shipping = Shipping.objects.create(order=order, method='Standard Shipping')
        self.client.login(email='admin@ecommerce.com', password='admin123')
        response = self.client.put(f'/api/orders/{order.id}/shipping/update/', {
            'status': 'in_transit',
            'tracking_number': 'TRACK456'
        })
        self.assertEqual(response.status_code, 200)
        shipping.refresh_from_db()
        self.assertEqual(shipping.status, 'in_transit')