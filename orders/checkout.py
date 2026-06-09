# orders/checkout.py
import logging
import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import UserRateThrottle
from django.db import transaction
from cart.models import Cart
from orders.models import Order, OrderItem
from products.models import Product
from .serializers import OrderSerializer

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


class CheckoutThrottle(UserRateThrottle):
    scope = "checkout"


class CheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [CheckoutThrottle]

    @transaction.atomic
    def post(self, request):
        try:
            cart = Cart.objects.select_for_update().get(user=request.user)
        except Cart.DoesNotExist:
            return Response({"detail": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        items = list(cart.items.select_related("product").all())
        if not items:
            return Response({"detail": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        product_ids = [item.product_id for item in items]
        products = Product.objects.select_for_update().filter(id__in=product_ids).in_bulk()

        # Validate stock
        for item in items:
            product = products.get(item.product_id)
            if product is None:
                return Response({"detail": f"Product {item.product_id} not found."}, status=status.HTTP_400_BAD_REQUEST)
            if item.quantity > product.stock:
                return Response({"detail": f"Not enough stock for {product.name}."}, status=status.HTTP_400_BAD_REQUEST)

        # Create order and items
        order = Order.objects.create(user=request.user, status="pending", total=0)
        total = 0
        for item in items:
            product = products[item.product_id]
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item.quantity,
                price=product.price
            )
            product.stock -= item.quantity
            product.save(update_fields=["stock"])
            total += product.price * item.quantity

        order.total = total
        order.save(update_fields=["total"])

        # clear cart
        cart.items.all().delete()

        # Create Stripe PaymentIntent
        # Amount must be in the smallest currency unit (e.g., cents)
        amount = int(total * 100)  # DecimalField * 100 -> integer cents
        currency = getattr(settings, "STRIPE_CURRENCY", "eur")

        try:
            # Use idempotency key to avoid duplicate charges if client retries
            idempotency_key = f"checkout_order_{order.id}"
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                metadata={"order_id": str(order.id), "user_id": str(request.user.id)},
                description=f"Order #{order.id} for {request.user.email}",
                # optionally: receipt_email=request.user.email
            idempotency_key=idempotency_key)
        except stripe.error.StripeError as e:
            # Optionally roll back order creation or mark order as failed
            return Response({"detail": "Payment initialization failed.", "error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        # Return order and client_secret for client to confirm payment
        return Response({
            "order": OrderSerializer(order, context={"request": request}).data,
            "payment": {
                "client_secret": payment_intent.client_secret,
                "payment_intent_id": payment_intent.id,
                "amount": amount,
                "currency": currency
            }
        }, status=status.HTTP_201_CREATED)
