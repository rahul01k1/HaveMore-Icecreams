from rest_framework import serializers
from home.models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.product_name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ["product_name", "price", "qty"]

class OrderSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.user_name", read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "user_name",
            "name",
            "email",
            "number",
            "address",
            "address_type",
            "status",
            "payment_status",
            "date",
            "items",
        ]
