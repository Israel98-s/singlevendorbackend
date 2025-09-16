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
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Payment, Wishlist, Review, Shipping, StoreSettings
from .serializers import *
from .permissions import IsVendorOrAdmin
from .utils import send_order_confirmation_email, send_payment_confirmation_email

User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        Cart.objects.create(user=user)
        StoreSettings.objects.create(user=user, store_name=f"{user.username}'s Store")
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.data['refresh']
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response(status=status.HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
            'Password Reset Request',
            f'Use this token to reset your password: {reset_token}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'Email not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password(request):
    reset_token = request.data.get('reset_token')
    new_password = request.data.get('new_password')
    try:
        user = User.objects.get(reset_token=reset_token)
        user.set_password(new_password)
        user.reset_token = None
        user.save()
        return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def profile(request):
    if request.method == 'GET':
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def store_settings(request):
    if request.method == 'GET':
        store_settings, created = StoreSettings.objects.get_or_create(user=request.user, defaults={'store_name': 'My Store'})
        serializer = StoreSettingsSerializer(store_settings)
        return Response(serializer.data)
    elif request.method == 'PUT':
        store_settings, created = StoreSettings.objects.get_or_create(user=request.user, defaults={'store_name': 'My Store'})
        serializer = StoreSettingsSerializer(store_settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'price', 'stock']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']

    def perform_create(self, serializer):
        if not self.request.user.is_vendor and not self.request.user.is_superuser:
            raise permissions.PermissionDenied("Only vendors or admins can create products")
        serializer.save()

class ProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsVendorOrAdmin]

@api_view(['POST'])
@permission_classes([IsVendorOrAdmin])
def delete_product_image(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if product.image:
        product.image.delete()
        product.image = None
        product.save()
        return Response({'message': 'Product image deleted'}, status=status.HTTP_200_OK)
    return Response({'error': 'No image to delete'}, status=status.HTTP_400_BAD_REQUEST)

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def perform_create(self, serializer):
        if not self.request.user.is_vendor and not self.request.user.is_superuser:
            raise permissions.PermissionDenied("Only vendors or admins can create categories")
        serializer.save()

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    serializer = CartSerializer(cart)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_to_cart(request):
    product_id = request.data.get('product_id')
    quantity = int(request.data.get('quantity', 1))
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity
    cart_item.save()
    serializer = CartSerializer(cart)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def remove_from_cart(request):
    product_id = request.data.get('product_id')
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(CartItem, cart=cart, product_id=product_id)
    cart_item.delete()
    serializer = CartSerializer(cart)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def clear_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart.items.all().delete()
    serializer = CartSerializer(cart)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_wishlist(request):
    wishlist = Wishlist.objects.filter(user=request.user)
    serializer = WishlistSerializer(wishlist, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_to_wishlist(request):
    product_id = request.data.get('product_id')
    product = get_object_or_404(Product, id=product_id, is_active=True)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if created:
        serializer = WishlistSerializer(wishlist)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({'message': 'Product already in wishlist'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def remove_from_wishlist(request):
    product_id = request.data.get('product_id')
    wishlist = get_object_or_404(Wishlist, user=request.user, product_id=product_id)
    wishlist.delete()
    return Response({'message': 'Product removed from wishlist'}, status=status.HTTP_200_OK)

class ReviewListCreateView(generics.ListCreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product', 'rating']

    def perform_create(self, serializer):
        product_id = self.request.data.get('product')
        product = get_object_or_404(Product, id=product_id)
        serializer.save(user=self.request.user, product=product)

class ReviewRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        if serializer.instance.user != self.request.user:
            raise permissions.PermissionDenied("You can only edit your own reviews")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise permissions.PermissionDenied("You can only delete your own reviews")
        instance.delete()

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def list_orders(request):
    orders = Order.objects.filter(user=request.user)
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    serializer = OrderSerializer(order)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@transaction.atomic
def create_order(request):
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.exists():
        return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
    
    shipping_address = request.data.get('shipping_address')
    if not shipping_address:
        return Response({'error': 'Shipping address is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    total_amount = sum(item.quantity * item.product.price for item in cart.items.all())
    order = Order.objects.create(
        user=request.user,
        total_amount=total_amount,
        shipping_address=shipping_address,
        status='pending'
    )
    
    for item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )
    
    cart.items.all().delete()
    send_order_confirmation_email(request.user, order)
    serializer = OrderSerializer(order)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['PUT'])
@permission_classes([IsVendorOrAdmin])
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    status = request.data.get('status')
    if status not in dict(Order._meta.get_field('status').choices).keys():
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
    order.status = status
    order.save()
    send_order_confirmation_email(order.user, order)
    serializer = OrderSerializer(order)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_shipping(request, order_id):
    shipping = get_object_or_404(Shipping, order__id=order_id, order__user=request.user)
    serializer = ShippingSerializer(shipping)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsVendorOrAdmin])
def update_shipping(request, order_id):
    shipping = get_object_or_404(Shipping, order__id=order_id)
    serializer = ShippingSerializer(shipping, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def initiate_payment(request):
    order_id = request.data.get('order_id')
    payment_method = request.data.get('payment_method')
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if payment_method == 'stripe':
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(order.total_amount * 100),
                currency='usd',
                payment_method_types=['card'],
                metadata={'order_id': str(order.id)},
            )
            payment = Payment.objects.create(
                order=order,
                method=payment_method,
                amount=order.total_amount,
                reference=intent['id'],
                status='pending'
            )
            return Response({
                'client_secret': intent['client_secret'],
                'payment_id': payment.id
            })
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error': 'Unsupported payment method'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_payment(request):
    payment_id = request.data.get('payment_id')
    payment = get_object_or_404(Payment, id=payment_id, order__user=request.user)
    if payment.method == 'stripe':
        try:
            intent = stripe.PaymentIntent.retrieve(payment.reference)
            if intent.status == 'succeeded':
                payment.status = 'completed'
                payment.order.status = 'confirmed'
                payment.order.save()
                payment.save()
                send_payment_confirmation_email(payment.order.user, payment)
                return Response({'message': 'Payment verified'}, status=status.HTTP_200_OK)
            return Response({'error': 'Payment not completed'}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response({'error': 'Unsupported payment method'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def payment_history(request):
    payments = Payment.objects.filter(order__user=request.user)
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsVendorOrAdmin])
def admin_dashboard(request):
    total_orders = Order.objects.count()
    total_products = Product.objects.count()
    total_users = User.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    return Response({
        'total_orders': total_orders,
        'total_products': total_products,
        'total_users': total_users,
        'pending_orders': pending_orders,
    })

@api_view(['GET'])
@permission_classes([IsVendorOrAdmin])
def admin_orders(request):
    orders = Order.objects.all()
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)