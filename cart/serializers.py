from rest_framework import serializers
from products.serializers import ProductSerializer
from products.models import Product
from .models import CartItem, Cart

class CartItemWriteSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )

    class Meta:
        model = CartItem
        fields = ["id", "product_id", "quantity"]
        extra_kwargs = {"quantity": {"min_value": 1}}

class CartItemReadSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity"]


class CartSerializer(serializers.ModelSerializer):
    """Serializer for Cart with items and timestamps"""
    items = CartItemReadSerializer(many=True, read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "user", "user_email", "created_at", "updated_at", "items"]
        read_only_fields = ["id", "user", "created_at", "updated_at", "items"]