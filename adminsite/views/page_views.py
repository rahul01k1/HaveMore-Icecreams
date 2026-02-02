from django.shortcuts import render, redirect
from home.models import Product, Buyer, Order, Message, Seller
from adminsite.decorators import admin_required

@admin_required
def dashboard_page(request):
    
    return render(request, "adminsite/dashboard/dashboard.html", {
    "total_products": Product.objects.count(),
    "total_users": Buyer.objects.count(),
    "pending_orders": Order.objects.filter(status="pending").count(),
    "total_messages": Message.objects.count()
})


def login_page(request):
    return render(request, "adminsite/auth/login.html")

@admin_required
def users_page(request):
    return render(request, "adminsite/dashboard/users.html")

def sellers_page(request):
    seller_id = request.session.get("seller_id")
    if not seller_id:
        return redirect("admin_login")

    return render(request, "adminsite/dashboard/sellers.html")



@admin_required
def products_page(request):
    sellers = Seller.objects.all()
    return render(request, "adminsite/dashboard/products.html",{"sellers":sellers})

@admin_required
def orders_page(request):

    return render(request, "adminsite/dashboard/orders.html")

@admin_required
def messages_page(request):
    
    return render(request,"adminsite/dashboard/message.html")