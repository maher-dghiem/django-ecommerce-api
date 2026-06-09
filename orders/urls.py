from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet
from .checkout import CheckoutAPIView
from .webhooks import PaymentWebhookAPIView

router = DefaultRouter()
router.register(r"", OrderViewSet, basename="order")

urlpatterns = [
    path("checkout/", CheckoutAPIView.as_view(), name="checkout"),
    path("webhooks/payments/", PaymentWebhookAPIView.as_view(), name="payment-webhook"),
    *router.urls,
]
