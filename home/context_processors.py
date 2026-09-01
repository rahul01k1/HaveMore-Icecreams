from .models import Buyer, Wishlist, Cart

def user_context(request):
    user_id = request.session.get("user_id")
    current_user = None
    wishlist_count = 0
    cart_count = 0

    if user_id:
        try:
            current_user = Buyer.objects.get(id=user_id)
            wishlist_count = Wishlist.objects.filter(user=current_user).count()
            cart_count = Cart.objects.filter(user=current_user).count()
        except Buyer.DoesNotExist:
            current_user = None

    return {
        "current_user": current_user,
        "wishlist_count": wishlist_count,
        "cart_count": cart_count,
    }
