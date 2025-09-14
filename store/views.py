from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
import uuid
import requests
import stripe
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Payment, Wishlist, Review, Shipping
from .serializers import *
from .permissions import IsVendorOrAdmin
from .utils import send_order_confirmation_email, send_payment_confirmation_email

User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY

# Authentication Views
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        Cart.objects.create(user=user)
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserProfileSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout(request):
    try:
        refresh_token = request.data["refresh_token"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def forgot_password(request):
    email = request.data.get('email')
    try:
        user = User.objects.get(email=email)
        reset_token = str(uuid.uuid4())
        user.reset_token = reset_token
        user.save()
        
        send_mail(
            'Password Reset',
            f'Your reset token: {reset_token}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        return Response({"message": "Reset email sent"})
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password(request):
    token = request.data.get('token')
    new_password = request.data.get('new_password')
    
    try:
        user = User.objects.get(reset_token=token)
        user.set_password(new_password)
        user.reset_token = ''
        user.save()
        return Response({"message": "Password reset successful"})
    except User.DoesNotExist:
        return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT'])
def profile(request):
    if request.method == 'GET':
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Product Views
class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'price']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']

    def perform_create(self, serializer):
        serializer.save()

class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_destroy(self, instance):
        if instance.image:
            instance.image.delete()
        instance.delete()

@api_view(['POST'])
@permission_classes([IsVendorOrAdmin])
def delete_product_image(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if product.image:
        product.image.delete()
        product.image = None
        product.save()
        return Response({"message": "Product image deleted"})
    return Response({"error": "No image to delete"}, status=status.HTTP_400_BAD_REQUEST)

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

# Cart Views
@api_view(['GET'])
def get_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    serializer = CartSerializer(cart)
    return Response(serializer.data)

@api_view(['POST'])
def add_to_cart(request):
    product_id = request.data.get('product_id')
    quantity = request.data.get('quantity', 1)
    
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return Response({"message": "Item added to cart"}, status=status.HTTP_201_CREATED)
    
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def remove_from_cart(request):
    product_id = request.data.get('product_id')
    
    try:
        cart = Cart.objects.get(user=request.user)
        cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
        cart_item.delete()
        return Response({"message": "Item removed from cart"})
    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def clear_cart(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart.items.all().delete()
        return Response({"message": "Cart cleared"})
    except Cart.DoesNotExist:
        return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)

# Wishlist Views
@api_view(['GET'])
def get_wishlist(request):
    wishlist = Wishlist.objects.filter(user=request.user)
    serializer = WishlistSerializer(wishlist, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def add_to_wishlist(request):
    product_id = request.data.get('product_id')
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        if created:
            return Response({"message": "Product added to wishlist"}, status=status.HTTP_201_CREATED)
        return Response({"message": "Product already in wishlist"})
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def remove_from_wishlist(request):
    product_id = request.data.get('product_id')
    try:
        wishlist_item = Wishlist.objects.get(user=request.user, product_id=product_id)
        wishlist_item.delete()
        return Response({"message": "Product removed from wishlist"})
    except Wishlist.DoesNotExist:
        return Response({"error": "Product not in wishlist"}, status=status.HTTP_404_NOT_FOUND)

# Review Views
class ReviewListCreateView(generics.ListCreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ReviewRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)

# Order Views
@api_view(['GET'])
def list_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    serializer = OrderSerializer(order)
    return Response(serializer.data)

@api_view(['POST'])
@transaction.atomic
def create_order(request):
    cart_data = request.data.get('cart', [])
    address = request.data.get('address')
    shipping_method = request.data.get('shipping_method', 'Standard Shipping')
    
    if not cart_data or not address:
        return Response({"error": "Cart and address required"}, status=status.HTTP_400_BAD_REQUEST)
    
    total_amount = 0
    order_items = []
    
    for item in cart_data:
        try:
            product = Product.objects.get(id=item['product_id'], is_active=True)
            quantity = item['quantity']
            
            if product.stock < quantity:
                return Response({"error": f"Insufficient stock for {product.name}"}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            item_total = product.price * quantity
            total_amount += item_total
            
            order_items.append({
                'product': product,
                'quantity': quantity,
                'price': product.price
            })
        except Product.DoesNotExist:
            return Response({"error": "Invalid product"}, status=status.HTTP_400_BAD_REQUEST)
    
    order = Order.objects.create(
        user=request.user,
        total_amount=total_amount,
        shipping_address=address
    )
    
    for item_data in order_items:
        OrderItem.objects.create(
            order=order,
            product=item_data['product'],
            quantity=item_data['quantity'],
            price=item_data['price']
        )
        
        product = item_data['product']
        product.stock -= item_data['quantity']
        product.save()
    
    Shipping.objects.create(
        order=order,
        method=shipping_method,
    )
    
    try:
        cart = Cart.objects.get(user=request.user)
        cart.items.all().delete()
    except Cart.DoesNotExist:
        pass
    
    send_order_confirmation_email(order)
    
    serializer = OrderSerializer(order)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['PUT'])
@permission_classes([IsVendorOrAdmin])
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    new_status = request.data.get('status')
    
    if new_status not in dict(Order.STATUS_CHOICES):
        return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
    
    order.status = new_status
    order.save()
    
    serializer = OrderSerializer(order)
    return Response(serializer.data)

# Shipping Views
@api_view(['GET'])
def get_shipping(request, order_id):
    shipping = get_object_or_404(Shipping, order_id=order_id, order__user=request.user)
    serializer = ShippingSerializer(shipping)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsVendorOrAdmin])
def update_shipping(request, order_id):
    shipping = get_object_or_404(Shipping, order_id=order_id)
    serializer = ShippingSerializer(shipping, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Payment Views
@api_view(['POST'])
def initiate_payment(request):
    order_id = request.data.get('order_id')
    method = request.data.get('method')
    
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        
        reference = f"PAY_{uuid.uuid4().hex[:10].upper()}"
        
        payment = Payment.objects.create(
            order=order,
            method=method,
            reference=reference,
            amount=order.total_amount
        )
        
        if method == 'paystack':
            url = "https://api.paystack.co/transaction/initialize"
            headers = {
                "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "email": request.user.email,
                "amount": int(order.total_amount * 100),
                "reference": reference
            }
            
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                return Response({
                    "reference": reference,
                    "authorization_url": response_data['data']['authorization_url']
                })
        
        elif method == 'stripe':
            try:
                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': f"Order {str(order.id)[:8]}",
                            },
                            'unit_amount': int(order.total_amount * 100),
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url='http://localhost:3000/payment/success',
                    cancel_url='http://localhost:3000/payment/cancel',
                    metadata={'order_id': str(order.id), 'reference': reference}
                )
                return Response({
                    "reference": reference,
                    "session_id": session.id,
                    "url": session.url
                })
            except stripe.error.StripeError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"reference": reference, "amount": order.total_amount})
    
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def verify_payment(request):
    reference = request.data.get('reference')
    
    try:
        payment = Payment.objects.get(reference=reference)
        
        if payment.method == 'paystack':
            url = f"https://api.paystack.co/transaction/verify/{reference}"
            headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                response_data = response.json()
                if response_data['data']['status'] == 'success':
                    payment.status = 'completed'
                    payment.order.status = 'confirmed'
                    payment.save()
                    payment.order.save()
                    send_payment_confirmation_email(payment)
                    return Response({"message": "Payment verified successfully"})
        
        elif payment.method == 'stripe':
            try:
                session = stripe.checkout.Session.retrieve(payment.reference)
                if session.payment_status == 'paid':
                    payment.status = 'completed'
                    payment.order.status = 'confirmed'
                    payment.save()
                    payment.order.save()
                    send_payment_confirmation_email(payment)
                    return Response({"message": "Payment verified successfully"})
            except stripe.error.StripeError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"error": "Payment verification failed"}, status=status.HTTP_400_BAD_REQUEST)
    
    except Payment.DoesNotExist:
        return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def payment_history(request):
    payments = Payment.objects.filter(order__user=request.user).order_by('-created_at')
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data)

# Admin Views
@api_view(['GET'])
@permission_classes([IsVendorOrAdmin])
def admin_dashboard(request):
    total_orders = Order.objects.count()
    total_revenue = sum(order.total_amount for order in Order.objects.all())
    pending_orders = Order.objects.filter(status='pending').count()
    
    return Response({
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "pending_orders": pending_orders,
        "total_customers": User.objects.filter(is_vendor=False).count()
    })

@api_view(['GET'])
@permission_classes([IsVendorOrAdmin])
def admin_orders(request):
    orders = Order.objects.all().order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)