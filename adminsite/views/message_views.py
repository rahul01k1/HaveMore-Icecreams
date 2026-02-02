from rest_framework.generics import ListAPIView, DestroyAPIView
from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404

from home.models import Message, Seller
from adminsite.serializers.message_serializer import MessageSerializer


# -------------------------
# Custom Permission
# -------------------------
class IsAdminSeller(BasePermission):
    def has_permission(self, request, view): #type: ignore
        seller_id = request.session.get("seller_id")
        if not seller_id:
            return False

        try:
            seller = Seller.objects.get(id=seller_id)
        except Seller.DoesNotExist:
            return False

        return seller.role == "admin"


# -------------------------
# Message List API
# -------------------------
class MessageListAPI(ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAdminSeller]

    def get_queryset(self):  #type: ignore
        return Message.objects.select_related("user").order_by("-created_at")


# -------------------------
# Message Delete API
# -------------------------
class MessageDeleteAPI(DestroyAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAdminSeller]

    def get_queryset(self):  #type: ignore
        return Message.objects.all()
