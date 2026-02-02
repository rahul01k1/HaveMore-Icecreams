from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Sum
from home.models import Order
from django.utils.timezone import now
from datetime import timedelta

class DashboardStatsAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        today = now().date()

        months = []
        revenue = []

        for i in range(5, -1, -1):
            start_date = (today.replace(day=1) - timedelta(days=30*i))
            end_date = start_date + timedelta(days=30)

            total = (
                Order.objects
                .filter(date__range=(start_date, end_date), payment_status="completed")
                .aggregate(total=Sum("items__price"))["total"]
                or 0
            )

            months.append(start_date.strftime("%b"))
            revenue.append(float(total))

        return Response({
            "months": months,
            "revenue": revenue
        })
