from rest_framework import serializers
from home.models import Message, Buyer


class MessageSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.user_name", read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "user_name",
            "name",
            "email",
            "subject",
            "message",
            "created_at",
        ]

    def create(self, validated_data):
        request = self.context.get("request")

        if not request:
            raise serializers.ValidationError("Request context is required")

        user_id = request.session.get("user_id")  # buyer session

        if not user_id:
            raise serializers.ValidationError("User not logged in")

        try:
            buyer = Buyer.objects.get(id=user_id)
        except Buyer.DoesNotExist:
            raise serializers.ValidationError("Invalid user")

        validated_data["user"] = buyer
        return super().create(validated_data)
