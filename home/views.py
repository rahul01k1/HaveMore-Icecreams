from django.shortcuts import render , redirect , get_object_or_404
from django.http import JsonResponse , HttpResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.contrib.auth.hashers import make_password , check_password
from django.contrib import messages
from  .models import *
from django.db.models import Q
import json
from django.views.decorators.csrf import csrf_exempt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.urls import reverse

# Navbar  Functions
def home(request):
    return render(request,"home/pages/home.html")

def order(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    orders = Order.objects.filter(user_id=user_id).prefetch_related("items")

    return render(request, "home/pages/order.html", {
        "orders": orders
    })

def menu(request):
    products = Product.objects.filter(product_status="active")

    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    user_id = request.session.get("user_id")

    if user_id:
        wishlist_ids = Wishlist.objects.filter(user_id=user_id).values_list("product_id", flat=True)
        for p in page_obj:
            p.is_in_wishlist = p.id in wishlist_ids
    else:
        for p in page_obj:
            p.is_in_wishlist = False
    
    is_logged_in = True if request.session.get("user_id") else False
    return render(request, "home/pages/menu.html", {"products": page_obj, "is_logged_in": is_logged_in})


def add_newsletter(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    email = request.POST.get("email")

    if not email:
        return JsonResponse({"error": "Please enter an email."}, status=400)

    # Check duplicate
    if Newsletter.objects.filter(email=email).exists():
        return JsonResponse({"error": "This email is already subscribed."}, status=409)

    Newsletter.objects.create(email=email)

    return JsonResponse({"success": "You have successfully subscribed!"})

def about(request):
    return render(request,"home/pages/about.html")


from django.http import JsonResponse

def contact(request):
    if request.method == "POST":

        if not request.session.get("user_id"):
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"error": "Please login to send a message."}, status=403)
            messages.error(request, "Please login to send a message.")
            return redirect("login")

        buyer = Buyer.objects.get(id=request.session["user_id"])
        subject = request.POST.get("subject", "").strip()
        message = request.POST.get("message", "").strip()

        # -------- Validation --------
        if len(subject) < 5:
            return JsonResponse({"error": "Subject must be at least 5 characters."}, status=400)

        if len(message) < 10:
            return JsonResponse({"error": "Message must be at least 10 characters."}, status=400)

        Message.objects.create(
            user=buyer,
            name=buyer.user_name,
            email=buyer.user_email,
            subject=subject,
            message=message
        )

        # -------- AJAX success --------
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})

        messages.success(request, "Message Sent Successfully.")
        return redirect("contact")

    return render(request, "home/pages/contact.html")

def search_product(request):
    query = request.GET.get("q", "").strip()
    products_qs = Product.objects.none()

    if query:
        keywords = query.split()

        q_filter = Q()
        for word in keywords:
            q_filter |= Q(product_name__icontains=word)
            q_filter |= Q(product_detail__icontains=word)

        products_qs = Product.objects.filter(q_filter).distinct().order_by("-id")

        if not products_qs.exists():
            messages.error(request, "No products found.")

    # ✅ PAGINATION
    paginator = Paginator(products_qs, 12)  # 12 products per page
    page_number = request.GET.get("page")
    products = paginator.get_page(page_number)

    context = {
        "products": products,
        "search_query": query
    }

    return render(request, "home/search/search_product.html", context)


# Cart & Wishlist Functions 
def cart(request,):
    user_id = request.session.get("user_id")
    if not user_id:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"error": "Not logged in"}, status=403)
        return redirect("login")
    
    user = Buyer.objects.get(id=user_id)
    cart_items = Cart.objects.filter(user=user)

    total_amount = sum(item.subtotal() for item in cart_items)

    # -------------------------------
    # AJAX REQUEST → Return JSON
    # -------------------------------
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        items_json = []
        
        for c in cart_items:
            items_json.append({
                "id": c.pk,
                "product_name": c.product.product_name,
                "product_image": c.product.product_image.url,
                "price": float(c.price),
                "qty": c.qty,
                "subtotal": float(c.subtotal())
            })

        return JsonResponse({
            "items": items_json,
            "total_amount": float(total_amount)
        })

    # -------------------------------
    # Normal page render
    # -------------------------------
    context = {
        "user": user,
        "cart_items": cart_items,
        "total_amount": total_amount
    }

    return render(request, "home/shop/cart.html", context)


def add_to_cart(request, id):
    user_id = request.session.get("user_id")

    # ---------- Not logged in ----------
    if not user_id:
        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "error": "Login required"}, status=403)
        return redirect("login")

    user = Buyer.objects.get(id=user_id)
    product = Product.objects.get(id=id)

    existing_item = Cart.objects.filter(user=user, product=product).first()

    if existing_item:
        existing_item.qty += 1
        existing_item.save()
    else:
        Cart.objects.create(
            user=user,
            product=product,
            price=product.product_price,
            qty=1
        )

    # ---------- IMPORTANT PART ----------
    cart_count = Cart.objects.filter(user=user).count()

    # ---------- AJAX response ----------
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "cart_count": cart_count
        })

    # ---------- Normal browser request ----------
    return redirect("cart")


def update_cart(request, id):
    if not request.session.get("user_id"):
        return JsonResponse({"error": "Not logged in"}, status=403)

    cart_item = Cart.objects.get(id=id)
    data = json.loads(request.body.decode("utf-8"))
    qty = int(data.get("qty"))

    if qty <= 0:
        cart_item.delete()
    else:
        cart_item.qty = qty
        cart_item.save()

    user = cart_item.user
    total_amount = sum(i.subtotal() for i in Cart.objects.filter(user=user))

    return JsonResponse({
        "subtotal": cart_item.subtotal() if qty > 0 else 0,
        "total_amount": float(total_amount)
    })

def remove_cart(request,id):
    cart_item = Cart.objects.get(id=id)
    user = cart_item.user
    cart_item.delete()

    total_amount = sum(i.subtotal() for i in Cart.objects.filter(user=user))

    return JsonResponse({"total_amount": float(total_amount)})

def empty_cart(request):
    user = Buyer.objects.get(id=request.session["user_id"])
    Cart.objects.filter(user=user).delete()

    return JsonResponse({"status": "success"})



import json
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from .models import Buyer, Product, Cart, Order, OrderItem


def checkout(request):
    # ===============================
    # AUTH CHECK
    # ===============================
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    user = Buyer.objects.get(id=user_id)

    # ===============================
    # BUY NOW STATE (SESSION)
    # ===============================
    if request.method == "GET":
        buy_now_param = request.GET.get("buy_now")
        if buy_now_param:
            request.session["buy_now_id"] = buy_now_param
        else:
            request.session.pop("buy_now_id", None)

    buy_now_id = request.session.get("buy_now_id")
    is_buy_now = bool(buy_now_id)

    # ===============================
    # PREPARE ITEMS
    # ===============================
    if is_buy_now:
        try:
            product = Product.objects.get(id=buy_now_id)
        except Product.DoesNotExist:
            messages.error(request, "Product not found.")
            return redirect("home")

        class TempItem:
            def __init__(self, product):
                self.product = product
                self.price = product.product_price
                self.qty = 1

            def subtotal(self):
                return self.price * self.qty

        cart_items = [TempItem(product)]

    else:
        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            messages.error(request, "Your cart is empty!")
            return redirect("cart")

    # ===============================
    # ✅ TOTAL AMOUNT (NOT STORED)
    # ===============================
    total_amount = sum(item.subtotal() for item in cart_items)

    # ===============================
    # POST → PLACE ORDER (AJAX)
    # ===============================
    if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        try:
            data = json.loads(request.body)

            order = Order.objects.create(
                user=user,
                name=data["name"],
                email=data["email"],
                number=data["number"],
                address=data["address"],
                address_type=data["address_type"],
                status="Processing",
                payment_status="Pending" if data["method"] == "cod" else "Paid"
            )

            if is_buy_now:
                product = Product.objects.get(id=buy_now_id)

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    seller=product.seller,
                    price=product.product_price,
                    qty=1
                )

                product.product_stock = max(0, product.product_stock - 1)
                product.save()

                request.session.pop("buy_now_id", None)

            else:
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        seller=item.product.seller,
                        price=item.price,
                        qty=item.qty
                    )

                    item.product.product_stock = max(0, item.product.product_stock - item.qty)
                    item.product.save()

                Cart.objects.filter(user=user).delete()

            return JsonResponse({
                "success": True,
                "redirect_url": f"/order_success/{order.id}/"
            })

        except Exception as e:
            return JsonResponse({
                "error": str(e)
            }, status=400)

    # ===============================
    # RENDER PAGE
    # ===============================
    return render(request, "home/shop/checkout.html", {
        "user": user,
        "cart_items": cart_items,
        "total_amount": total_amount,   # ✅ ADDED
        "is_buy_now": is_buy_now
    })


def order_success(request, order_id):

    order = get_object_or_404(Order, id=order_id)

    order_items = order.items.all()   # related_name="items" #type: ignore

    total_amount = sum(item.total_price() for item in order_items)

    return render(request, "home/shop/order_success.html", {
        "order": order,
        "order_items": order_items,
        "total_amount": total_amount
    })

def wishlist(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    user = Buyer.objects.get(id=user_id)

    wishlist_qs = Wishlist.objects.filter(user=user).order_by("-id")

    paginator = Paginator(wishlist_qs, 8)  # ✅ 12 items per page
    page_number = request.GET.get("page")
    items = paginator.get_page(page_number)

    return render(request, "home/shop/wishlist.html", {
        "items": items
    })

def add_to_wishlist(request, id):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    user = Buyer.objects.get(id=user_id)
    product = Product.objects.get(id=id)

    Wishlist.objects.get_or_create(
        user=user,
        product=product,
        defaults={"price": product.product_price}
    )

    return redirect("wishlist")

@csrf_exempt
def toggle_wishlist(request):
    data = json.loads(request.body)
    product_id = data["product_id"]

    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"error": "Login required"}, status=403)

    user = Buyer.objects.get(id=user_id)
    product = Product.objects.get(id=product_id)

    existing = Wishlist.objects.filter(user=user, product=product)
    if existing.exists():
        existing.delete()
        return JsonResponse({"removed": True})

    Wishlist.objects.create(user=user, product=product, price=product.product_price)
    return JsonResponse({"added": True})




@require_POST
def remove_wishlist(request, id):
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"error": "login_required"}, status=401)

    deleted, _ = Wishlist.objects.filter(id=id, user_id=user_id).delete()

    return JsonResponse({"success": bool(deleted)})

  #  Views Function 

def view_product(request, id):
    product = get_object_or_404(Product, id=id)

    # CHECK IF USER LOGGED IN
    user_id = request.session.get("buyer_id")

    is_in_wishlist = False

    if user_id:
        is_in_wishlist = Wishlist.objects.filter(
            user_id=user_id,
            product=product
        ).exists()

    return render(request, "home/shop/views/view_product.html", {
        "product": product,
        "is_in_wishlist": is_in_wishlist,
    })


def view_order(request, id):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    order = get_object_or_404(Order, id=id, user_id=user_id)

    order_items = OrderItem.objects.filter(order=order)
    total_amount = sum(item.total_price() for item in order_items)

    return render(request, "home/shop/views/view_order.html", {
        "order": order,
        "order_items": order_items,
        "total_amount": total_amount,
    })


def cancel_order(request, id):
    user_id = request.session.get("user_id")

    if not user_id:
        return redirect("login")

    # Ensure user can cancel ONLY their own order
    order = get_object_or_404(Order, id=id, user_id=user_id)

    # Prevent double cancel
    if order.status == "canceled":
        messages.warning(request, "This order is already canceled.")
        return redirect("view_order", id=id)

    # Update order status
    order.status = "canceled"
    order.payment_status = "pending"
    order.save()

    # Restore product stock
    for item in order.items.all(): #type: ignore
        product = item.product
        product.product_stock += item.qty
        product.save(update_fields=["product_stock"])

    messages.success(request, "Order canceled successfully!")

    return redirect("view_order", id=id)

# Add Cart And Wishlist Count:

def cart_count(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"count": 0})

    count = Cart.objects.filter(user_id=user_id).count()
    return JsonResponse({"count": count})


def wishlist_count(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"count": 0})

    count = Wishlist.objects.filter(user_id=user_id).count()
    return JsonResponse({"count": count})

# Profile Functions
def profile(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    user = Buyer.objects.get(id=user_id)

    return render(request, "home/user/profile.html", {
        "user": user
    })

def update_profile(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    user = Buyer.objects.get(id=user_id)

    if request.method == "POST":

        # Update basic details
        user.user_name = request.POST.get("user_name")
        user.user_email = request.POST.get("user_email")

        # Update Image
        if "user_image" in request.FILES:
            user.user_image = request.FILES["user_image"]

        # ==============================
        # PASSWORD CHANGE LOGIC
        # ==============================
        old_pass = request.POST.get("user_old_password")
        new_pass = request.POST.get("user_new_password")
        confirm_pass = request.POST.get("user_confirm_password")

        # If user entered any password fields → password update requested
        if old_pass or new_pass or confirm_pass:

            # Check old password match
            if old_pass != user.user_password:
                messages.error(request, "Incorrect old password.")
                return redirect("update_profile")

            # New password must match confirm password
            if new_pass != confirm_pass:
                messages.error(request, "New Password and Confirm Password do not match.")
                return redirect("update_profile")

            # New password cannot be empty
            if new_pass.strip() == "":
                messages.error(request, "Password cannot be empty.")
                return redirect("update_profile")

            # Save new password
            user.user_password = new_pass

        # Save all updates
        user.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("profile")

    return render(request, "home/user/update_profile.html", {"user": user})


def user_messages(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    user = Buyer.objects.get(id=user_id)
    messages_list = Message.objects.filter(user=user)

    return render(request, "home/user/messages.html", {
        "messages_list": messages_list
    })

def user_register(request):
    if request.method == "POST":
        username = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        cpassword = request.POST.get('cpassword', '')
        profile_image = request.FILES.get('profile_image')

        # 1️⃣ Required field validation
        if not username or not email or not password or not cpassword:
            messages.error(request, "All fields are required!")
            return redirect("register")

        # 2️⃣ Email format validation
        if '@' not in email or '.' not in email:
            messages.error(request, "Invalid email address!")
            return redirect("register")

        # 3️⃣ Password match
        if password != cpassword:
            messages.error(request, "Passwords do not match!")
            return redirect("register")

        # 4️⃣ Password strength
        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long!")
            return redirect("register")

        # 5️⃣ Duplicate email check
        if Buyer.objects.filter(user_email=email).exists():
            messages.error(request, "Email already exists!")
            return redirect("register")

        # 6️⃣ Image validation
        if profile_image:
            valid_extensions = ['jpg', 'jpeg', 'png', 'gif']
            file_extension = profile_image.name.split('.')[-1].lower()

            if file_extension not in valid_extensions:
                messages.error(request, "Invalid image format!")
                return redirect("register")

            if profile_image.size > 2 * 1024 * 1024:  # 2MB
                messages.error(request, "Image size must be under 2MB!")
                return redirect("register")

        # 7️⃣ Save user
        user = Buyer(
            user_name=username,
            user_email=email,
            user_password=make_password(password),
            user_image=profile_image if profile_image else "user_profile.jpg"
        )
        user.save()

        # 8️⃣ Session
        request.session['user_id'] = user.pk
        request.session['user_name'] = user.user_name
        request.session['user_email'] = user.user_email
        request.session['user_image'] = str(user.user_image)

        messages.success(request, f"Welcome {user.user_name}! Account created successfully.")
        return redirect("home")

    return render(request, "home/user/auth/register.html")


def user_login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user =  Buyer.objects.get(user_email = email)
        except Buyer.DoesNotExist:
            messages.error(request,"Email not registered!")
            return redirect("login")
        
        if check_password(password, user.user_password):

            request.session['user_id'] = user.pk
            request.session['user_name'] = user.user_name
            request.session['user_email'] = user.user_email
            request.session['user_image'] = str(user.user_image)

            messages.success(request,f"Welcome Back ,{user.user_name}")
            return redirect("home")
        else :
            messages.error(request, "Incorrect password!")
            return redirect("login")
            
    return render(request,"home/user/auth/login.html")

def user_logout(request):
    request.session.flush()
    messages.success(request,"Logout Successfully!")
    return redirect("login")

def download_invoice(request, order_id):
    order = Order.objects.get(id=order_id)
    items = order.items.all() #type: ignore

    # Create the PDF response
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Invoice_{order.id}.pdf"'

    # Initialize PDF canvas
    p = canvas.Canvas(response, pagesize=A4) #type: ignore
    width, height = A4

    y = height - 50

    # ============= HEADER ==============
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, y, "Blue Sky Summer")
    y -= 30

    p.setFont("Helvetica", 12)
    p.drawString(50, y, "Customer Invoice")
    y -= 20

    p.line(50, y, width - 50, y)
    y -= 30

    # ============= ORDER INFO ==============
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, f"Order ID: #{order.id}")
    y -= 20
    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Name: {order.name}")
    y -= 20
    p.drawString(50, y, f"Email: {order.email}")
    y -= 20
    p.drawString(50, y, f"Phone: {order.number}")
    y -= 20
    p.drawString(50, y, f"Address: {order.address}")
    y -= 20
    p.drawString(50, y, f"Payment Status: {order.payment_status}")
    y -= 30

    p.line(50, y, width - 50, y)
    y -= 40

    # ============= TABLE HEADER ==============
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Product")
    p.drawString(250, y, "Qty")
    p.drawString(320, y, "Price")
    p.drawString(400, y, "Total")
    y -= 20

    p.line(50, y, width - 50, y)
    y -= 25

    # ============= ORDER ITEMS ==============
    p.setFont("Helvetica", 12)
    total = 0

    for item in items:
        p.drawString(50, y, item.product.product_name)
        p.drawString(250, y, str(item.qty))
        p.drawString(320, y, f"${item.price}")
        p.drawString(400, y, f"${item.total_price()}")
        total += item.total_price()

        y -= 20

        if y < 100:
            p.showPage()
            y = height - 50

    # ============= TOTAL AMOUNT ==============
    y -= 20
    p.line(50, y, width - 50, y)
    y -= 30

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, f"Grand Total: ${total}")

    # Finish PDF
    p.showPage()
    p.save()

    return response


