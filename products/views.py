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
