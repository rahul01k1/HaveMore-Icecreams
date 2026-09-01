from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter
from home.models import Order
from adminsite.serializers.order_serializer import OrderSerializer

class OrderListAPI(ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter]
    search_fields = ['id', 'user_name', 'email', 'status']

class OrderDetailAPI(RetrieveUpdateDestroyAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [AllowAny]
