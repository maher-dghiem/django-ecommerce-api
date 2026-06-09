# products/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from .models import Product
from .serializers import ProductSerializer


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Allow staff to modify products; others can only read.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class ProductListThrottle(AnonRateThrottle):
    scope = "product_list"


class ProductDetailThrottle(UserRateThrottle):
    scope = "product_detail"


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]
    throttle_classes = [ProductListThrottle, ProductDetailThrottle]
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'stock']

    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def list(self, request, *args, **kwargs):
        """List all products with caching"""
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def retrieve(self, request, *args, **kwargs):
        """Retrieve single product with caching"""
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Create product - staff only"""
        if not request.user.is_staff:
            return Response(
                {"detail": "Only staff can create products."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Update product - staff only"""
        if not request.user.is_staff:
            return Response(
                {"detail": "Only staff can update products."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete product - staff only"""
        if not request.user.is_staff:
            return Response(
                {"detail": "Only staff can delete products."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)
