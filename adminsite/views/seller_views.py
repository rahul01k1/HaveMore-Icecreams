from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from home.models import Seller
from rest_framework.filters import SearchFilter
from adminsite.serializers.seller_serializer import SellerSerializer
from adminsite.permissions import IsSellerOrAdmin

class SellerListCreateAPI(ListCreateAPIView):
    queryset = Seller.objects.exclude(role='admin')
    serializer_class = SellerSerializer
    permission_classes = [IsSellerOrAdmin]
    filter_backends = [SearchFilter]
    search_fields = ['seller_name', 'email', 'phone']


class SellerDetailAPI(RetrieveUpdateDestroyAPIView):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer
    permission_classes = [IsSellerOrAdmin]
    parser_classes = (MultiPartParser, FormParser)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        serializer.save()
        return Response(serializer.data, status=200)
