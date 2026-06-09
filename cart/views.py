# cart/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db import transaction
from .models import Cart, CartItem
from .serializers import CartItemReadSerializer, CartItemWriteSerializer
from products.models import Product


class IsCartOwner(permissions.BasePermission):
    """
    Allow users to access only their own cart.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class CartListThrottle(UserRateThrottle):
    scope = "cart_list"


class CartModifyThrottle(UserRateThrottle):
    scope = "cart_modify"


class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsCartOwner]
    throttle_classes = [CartListThrottle, CartModifyThrottle]

    def _get_or_create_cart(self, user):
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart

    @method_decorator(cache_page(60 * 1))  # Cache for 1 minute
    def list(self, request):
        """List cart items with caching"""
        cart = self._get_or_create_cart(request.user)
        items = cart.items.select_related("product").all()
        serializer = CartItemReadSerializer(items, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def add_item(self, request):
        """
        Add item to cart.
        payload: {"product_id": <id>, "quantity": <int>}
        If item exists, increment quantity.
        """
        serializer = CartItemWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cart = self._get_or_create_cart(request.user)
        product = serializer.validated_data["product"]
        qty = serializer.validated_data["quantity"]

        if qty <= 0:
            return Response({"detail": "Quantity must be positive."}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            item, created = CartItem.objects.select_for_update().get_or_create(
                cart=cart, product=product, defaults={"quantity": qty}
            )
            if not created:
                item.quantity = item.quantity + qty
                item.save(update_fields=["quantity"])

        read = CartItemReadSerializer(item, context={"request": request})
        return Response(read.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["patch"])
    def update_item(self, request):
        """
        Update cart item quantity.
        payload: {"item_id": <id>, "quantity": <int>}
        If quantity <= 0, item is deleted.
        """
        item_id = request.data.get("item_id")
        quantity = request.data.get("quantity")
        if item_id is None or quantity is None:
            return Response({"detail": "item_id and quantity required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart = self._get_or_create_cart(request.user)
            item = cart.items.get(id=item_id)
        except CartItem.DoesNotExist:
            return Response({"detail": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)

        if int(quantity) <= 0:
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        item.quantity = int(quantity)
        item.save(update_fields=["quantity"])
        return Response(CartItemReadSerializer(item, context={"request": request}).data)

    @action(detail=False, methods=["post"])
    def remove_item(self, request):
        """
        Remove item from cart.
        payload: {"item_id": <id>}
        """
        item_id = request.data.get("item_id")
        if item_id is None:
            return Response({"detail": "item_id required."}, status=status.HTTP_400_BAD_REQUEST)
        cart = self._get_or_create_cart(request.user)
        deleted, _ = cart.items.filter(id=item_id).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["post"])
    def clear(self, request):
        """Clear all items from cart"""
        cart = self._get_or_create_cart(request.user)
        cart.items.all().delete()
        return Response({"message": "Cart cleared."}, status=status.HTTP_204_NO_CONTENT)
