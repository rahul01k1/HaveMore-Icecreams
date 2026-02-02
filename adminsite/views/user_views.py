from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from home.models import Buyer
from adminsite.serializers.user_serializer import BuyerSerializer
from adminsite.permissions import IsSellerOrAdmin


class UserListCreateAPI(ListCreateAPIView):
    queryset = Buyer.objects.all()
    serializer_class = BuyerSerializer
    permission_classes = [IsSellerOrAdmin]


class UserDetailAPI(RetrieveUpdateDestroyAPIView):
    queryset = Buyer.objects.all()
    serializer_class = BuyerSerializer
    permission_classes = [IsSellerOrAdmin]
