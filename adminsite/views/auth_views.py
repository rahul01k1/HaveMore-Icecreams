from rest_framework.views import APIView 
from rest_framework.response import Response
from rest_framework.permissions import   AllowAny
from home.models import *
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator



class LoginAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):

        email = request.data.get("email")
        password = request.data.get("password")
        role = request.data.get("role")

        if role == "seller":
            user = Seller.objects.filter(seller_email=email).first()

            if not user:
                return Response({"error": "Invalid credentials"}, status=400)

            print("DB PASSWORD:", repr(user.seller_password))

            if user.seller_password != password:
                return Response({"error": "Invalid credentials"}, status=400)

            request.session["seller_id"] = user.pk
            request.session["seller_name"] = user.seller_name
            request.session["seller_role"] = "seller"
            request.session["seller_image"] = user.seller_image.url if user.seller_image else ""

        else:
            return Response({"error": "Invalid credentials"}, status=400)

        return Response({"success": True})

@method_decorator(csrf_exempt, name='dispatch')
class LogoutAPI(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        request.session.flush()
        return Response({"message": "Logged out"})
    




