from rest_framework import serializers
from home.models import Buyer
from django.contrib.auth.hashers import make_password


class BuyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Buyer
        fields = "__all__"
        extra_kwargs = {
            "user_password": {
                "write_only": True,
                "required": False,   # 
            }
        }

    def create(self, validated_data):
        if "user_password" in validated_data:
            validated_data["user_password"] = make_password(
                validated_data["user_password"]
            )
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "user_password" in validated_data:
            validated_data["user_password"] = make_password(
                validated_data["user_password"]
            )
        return super().update(instance, validated_data)
