from rest_framework import serializers
from home.models import Product


class ProductSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source="seller.seller_name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "product_name",
            "product_price",
            "product_stock",
            "product_status",
            "product_image",
            "seller",
            "seller_name",
        ]
        extra_kwargs = {
            "product_image": {"required": False},
            "seller": {"required": False},
        }

    def update(self, instance, validated_data):
        
        if "product_image" not in validated_data:
            validated_data.pop("product_image", None)

        return super().update(instance, validated_data)
