from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from home.models import Buyer
from rest_framework.filters import SearchFilter
from adminsite.serializers.user_serializer import BuyerSerializer
from adminsite.permissions import IsSellerOrAdmin


class UserListCreateAPI(ListCreateAPIView):
    queryset = Buyer.objects.all()
    serializer_class = BuyerSerializer
    permission_classes = [IsSellerOrAdmin]
    filter_backends = [SearchFilter]
    search_fields = ['first_name', 'last_name', 'email', 'phone']


class UserDetailAPI(RetrieveUpdateDestroyAPIView):
    queryset = Buyer.objects.all()
    serializer_class = BuyerSerializer
    permission_classes = [IsSellerOrAdmin]
