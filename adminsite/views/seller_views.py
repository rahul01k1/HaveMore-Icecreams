from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from home.models import Seller
from adminsite.serializers.seller_serializer import SellerSerializer
from adminsite.permissions import IsSellerOrAdmin

class SellerListCreateAPI(ListCreateAPIView):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer
    permission_classes = [IsSellerOrAdmin]


class SellerDetailAPI(RetrieveUpdateDestroyAPIView):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer
    permission_classes = [IsSellerOrAdmin]
