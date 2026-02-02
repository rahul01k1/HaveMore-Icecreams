from rest_framework import serializers
from home.models import Seller
from django.contrib.auth.hashers import make_password


class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = "__all__"
        extra_kwargs = {
            "seller_password": {
                "write_only": True,
                "required": False,  # 🔥 allows update without password
            }
        }

    def create(self, validated_data):
        if "seller_password" in validated_data:
            validated_data["seller_password"] = make_password(
                validated_data["seller_password"]
            )
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "seller_password" in validated_data:
            validated_data["seller_password"] = make_password(
                validated_data["seller_password"]
            )
        return super().update(instance, validated_data)
