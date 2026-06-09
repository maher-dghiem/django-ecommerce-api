import logging
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from orders.models import Order

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY
ENDPOINT_SECRET = settings.STRIPE_WEBHOOK_SECRET  # set in env

@method_decorator(csrf_exempt, name="dispatch")
class PaymentWebhookAPIView(APIView):
    authentication_classes = []  # webhooks are unauthenticated; we verify signature
    permission_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        if not ENDPOINT_SECRET:
            return Response({"detail": "Webhook secret not configured."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            event = stripe.Webhook.construct_event(
                payload=payload, sig_header=sig_header, secret=ENDPOINT_SECRET
            )
        except ValueError:
            # Invalid payload
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Handle the event
        event_type = event["type"]
        data = event["data"]["object"]

        if event_type == "payment_intent.succeeded":
            # Payment succeeded, mark order as paid
            # We stored order_id in metadata when creating the PaymentIntent
            order_id = data.get("metadata", {}).get("order_id")
            amount = data.get("amount")
            if order_id and amount:
                try:
                    order = Order.objects.get(id=int(order_id))
                    # Verify amount matches order total (fraud prevention)
                    if int(order.total * 100) != amount:
                        logger.error(f"Amount mismatch for order {order_id}: expected {int(order.total * 100)}, got {amount}")
                        return Response(status=status.HTTP_400_BAD_REQUEST)
                    # Only update if status changed (idempotency)
                    if order.status != "paid":
                        order.status = "paid"
                        try:
                            order.save(update_fields=["status"])
                        except Exception as e:
                            logger.error(f"Failed to update order {order_id}: {str(e)}")
                            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                except Order.DoesNotExist:
                    logger.warning(f"Webhook received for non-existent order: {order_id}")

        elif event_type == "payment_intent.payment_failed":
            # Optionally mark order as cancelled or failed
            order_id = data.get("metadata", {}).get("order_id")
            if order_id:
                try:
                    order = Order.objects.get(id=int(order_id))
                    # Only update if status hasn't already been set (idempotency)
                    if order.status != "cancelled":
                        order.status = "cancelled"
                        try:
                            order.save(update_fields=["status"])
                        except Exception as e:
                            logger.error(f"Failed to update order {order_id}: {str(e)}")
                            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                except Order.DoesNotExist:
                    logger.warning(f"Webhook received for non-existent order: {order_id}")

        # Add other event types as needed (charge.refunded, dispute.created, etc.)

        return Response({"received": True}, status=status.HTTP_200_OK)
