from django.shortcuts import redirect , render


from django.shortcuts import redirect
from functools import wraps
from home.models import Seller

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        seller_id = request.session.get("seller_id")
        if not seller_id:
            return redirect("admin_login")

        try:
            seller = Seller.objects.get(id=seller_id)
        except Seller.DoesNotExist:
            return redirect("admin_login")

        if seller.role != "admin":
            return redirect("admin_login")

        return view_func(request, *args, **kwargs)
    return wrapper
