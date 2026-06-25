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


class ProductListAnonThrottle(AnonRateThrottle):
    scope = "product_list_anon"

class ProductListUserThrottle(UserRateThrottle):
    scope = "product_list_user"

class ProductDetailAnonThrottle(AnonRateThrottle):
    scope = "product_detail_anon"

class ProductDetailUserThrottle(UserRateThrottle):
    scope = "product_detail_user"

class ProductWriteThrottle(UserRateThrottle):
    scope = "product_write"


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsStaffOrReadOnly]
    throttle_classes = []
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at', 'stock']

    def get_throttles(self):
        if self.action == "list":
            if self.request.user.is_authenticated:
                return [ProductListUserThrottle()]
            return [ProductListAnonThrottle()]

        if self.action == "retrieve":
            if self.request.user.is_authenticated:
                return [ProductDetailUserThrottle()]
            return [ProductDetailAnonThrottle()]

        if self.action in ("create", "update", "partial_update", "destroy"):
            return [ProductWriteThrottle()]

        return super().get_throttles()

    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def list(self, request, *args, **kwargs):
        """List all products with caching"""
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def retrieve(self, request, *args, **kwargs):
        """Retrieve single product with caching"""
        return super().retrieve(request, *args, **kwargs)

