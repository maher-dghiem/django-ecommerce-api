# orders/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from .models import Order
from .serializers import OrderSerializer


class IsStaffOrOwner(permissions.BasePermission):
    """
    Allow access to staff for all orders; owners can view their own orders.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user == request.user


class OrderListThrottle(UserRateThrottle):
    scope = "order_list"


class OrderDetailThrottle(UserRateThrottle):
    scope = "order_detail"


class OrderViewSet(viewsets.ModelViewSet):
    """
    Expose list/retrieve for users and staff. Prevent delete for non-staff.
    """
    queryset = Order.objects.prefetch_related("items__product").all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrOwner]
    throttle_classes = [OrderListThrottle, OrderDetailThrottle]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset.order_by("-created_at")
        return self.queryset.filter(user=user).order_by("-created_at")

    @method_decorator(cache_page(60 * 2))  # Cache for 2 minutes
    def list(self, request, *args, **kwargs):
        """List orders with caching"""
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def retrieve(self, request, *args, **kwargs):
        """Retrieve single order with caching"""
        return super().retrieve(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        # Prevent deletion except for staff
        if not request.user.is_staff:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        # Allow status updates only for staff (or implement business rules)
        if not request.user.is_staff:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        # Prevent direct order creation; use checkout instead
        return Response(
            {"detail": "Use /api/orders/checkout/ endpoint to create orders."},
            status=status.HTTP_400_BAD_REQUEST
        )
