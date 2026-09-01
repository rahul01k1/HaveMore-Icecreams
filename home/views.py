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
from reportlab.lib import colors
from django.urls import reverse

# Navbar  Functions
def home(request):
    featured_products = Product.objects.filter(product_status="active")[:8]
    return render(request, "home/pages/home.html", {
        "featured_products": featured_products
    })

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

    paginator = Paginator(products, 15)
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

    total_results = products_qs.count()

    # 15 products per page
    paginator = Paginator(products_qs, 15)
    page_number = request.GET.get("page")
    products = paginator.get_page(page_number)

    suggested_products = None
    if total_results == 0:
        suggested_products = Product.objects.filter(product_status="active")[:6]

    context = {
        "products": products,
        "search_query": query,
        "total_results": total_results,
        "suggested_products": suggested_products,
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

    qty_to_add = 1
    if request.method == "POST":
        if request.body and request.headers.get("Content-Type") == "application/json":
            try:
                body_data = json.loads(request.body)
                qty_to_add = int(body_data.get("qty", 1))
            except Exception:
                qty_to_add = 1
        elif request.POST.get("qty"):
            try:
                qty_to_add = int(request.POST.get("qty", 1))
            except Exception:
                qty_to_add = 1

    existing_item = Cart.objects.filter(user=user, product=product).first()

    if existing_item:
        existing_item.qty += qty_to_add
        existing_item.save()
    else:
        Cart.objects.create(
            user=user,
            product=product,
            price=product.product_price,
            qty=qty_to_add
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
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    if not user_id:
        if is_ajax:
            return JsonResponse({"error": "login_required"}, status=401)
        return redirect("login")

    try:
        user = Buyer.objects.get(id=user_id)
        product = Product.objects.get(id=id)
    except (Buyer.DoesNotExist, Product.DoesNotExist):
        if is_ajax:
            return JsonResponse({"error": "not_found"}, status=404)
        return redirect("wishlist")

    item, created = Wishlist.objects.get_or_create(
        user=user,
        product=product,
        defaults={"price": product.product_price}
    )

    if is_ajax:
        return JsonResponse({"added": True, "created": created})

    return redirect("wishlist")

@csrf_exempt
def toggle_wishlist(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    product_id = None
    if request.body:
        try:
            data = json.loads(request.body)
            if isinstance(data, dict):
                product_id = data.get("product_id") or data.get("id")
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            pass

    if not product_id:
        product_id = request.POST.get("product_id") or request.POST.get("id")

    if not product_id:
        return JsonResponse({"error": "Product ID is required"}, status=400)

    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"error": "Login required"}, status=403)

    try:
        user = Buyer.objects.get(id=user_id)
        product = Product.objects.get(id=product_id)
    except (Buyer.DoesNotExist, Product.DoesNotExist):
        return JsonResponse({"error": "Product or user not found"}, status=404)

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
    user_id = request.session.get("user_id")

    is_in_wishlist = False

    if user_id:
        is_in_wishlist = Wishlist.objects.filter(
            user_id=user_id,
            product=product
        ).exists()

    related_products = Product.objects.filter(product_status="active").exclude(id=product.id)[:4]

    return render(request, "home/shop/views/view_product.html", {
        "product": product,
        "is_in_wishlist": is_in_wishlist,
        "related_products": related_products,
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
    orders = Order.objects.filter(user=user).order_by("-id")
    total_orders = orders.count()
    recent_orders = orders[:3]
    wishlist_count = Wishlist.objects.filter(user=user).count()
    cart_count = Cart.objects.filter(user=user).count()

    return render(request, "home/user/profile.html", {
        "user": user,
        "total_orders": total_orders,
        "recent_orders": recent_orders,
        "wishlist_count": wishlist_count,
        "cart_count": cart_count,
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

        # Update session with new profile details
        request.session['user_name'] = user.user_name
        request.session['user_email'] = user.user_email
        request.session['user_image'] = str(user.user_image)
        request.session.modified = True

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
    messages.success(request, "Logout Successfully!")
    return redirect("login")


def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    items = order.items.all() #type: ignore

    # Create the PDF response
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="Invoice_HaveMore_#{order.id}.pdf"'

    # Initialize PDF canvas
    p = canvas.Canvas(response, pagesize=A4) #type: ignore
    width, height = A4

    # Theme Colors
    brand_pink = colors.HexColor("#ff6b81")
    brand_dark = colors.HexColor("#e8415a")
    navy_dark = colors.HexColor("#0f172a")
    text_body = colors.HexColor("#334155")
    text_muted = colors.HexColor("#64748b")
    card_bg = colors.HexColor("#f8fafc")
    card_border = colors.HexColor("#e2e8f0")
    row_alt = colors.HexColor("#fafafa")
    green_badge = colors.HexColor("#16a34a")
    green_bg = colors.HexColor("#dcfce7")

    margin = 40
    content_width = width - (margin * 2) # 515 pt

    # 1. TOP BRAND ACCENT BAR
    p.setFillColor(brand_pink)
    p.rect(0, height - 6, width, 6, fill=1, stroke=0)

    # 2. BRAND HEADER & INVOICE META
    p.setFillColor(navy_dark)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(margin, height - 38, "HaveMore IceCreams")
    p.setFont("Helvetica", 8.5)
    p.setFillColor(text_muted)
    p.drawString(margin, height - 51, "Fresh Handcrafted Artisanal Ice Creams & Desserts")
    p.drawString(margin, height - 62, "support@havemoreicecreams.com  |  havemoreicecreams.com")

    # Right Header Info
    p.setFillColor(navy_dark)
    p.setFont("Helvetica-Bold", 18)
    p.drawRightString(width - margin, height - 38, "TAX INVOICE")
    
    order_date_str = order.date.strftime("%d %b %Y, %I:%M %p") if order.date else "N/A"
    p.setFont("Helvetica-Bold", 9.5)
    p.setFillColor(text_body)
    p.drawRightString(width - margin, height - 51, f"Invoice #: INV-{order.id:05d}")
    p.setFont("Helvetica", 8.5)
    p.setFillColor(text_muted)
    p.drawRightString(width - margin, height - 62, f"Date: {order_date_str}")

    # Separator Line
    p.setStrokeColor(card_border)
    p.setLineWidth(0.8)
    p.line(margin, height - 72, width - margin, height - 72)

    # 3. DUAL DETAILS CARDS (CUSTOMER INFO & PAYMENT DETAILS)
    y_card = height - 82
    card_h = 72
    card_w = (content_width - 14) / 2 # ~250 pt each

    # Card 1: Billed To
    p.setFillColor(card_bg)
    p.setStrokeColor(card_border)
    p.setLineWidth(1)
    p.roundRect(margin, y_card - card_h, card_w, card_h, 5, fill=1, stroke=1)

    p.setFillColor(text_muted)
    p.setFont("Helvetica-Bold", 8)
    p.drawString(margin + 10, y_card - 14, "CUSTOMER & DELIVERY INFO")

    p.setFont("Helvetica-Bold", 9.5)
    p.setFillColor(navy_dark)
    p.drawString(margin + 10, y_card - 27, str(order.name)[:30])

    p.setFont("Helvetica", 8.5)
    p.setFillColor(text_body)
    p.drawString(margin + 10, y_card - 40, f"Phone: +91 {order.number}")
    p.drawString(margin + 10, y_card - 52, f"Email: {str(order.email)[:28]}")
    p.drawString(margin + 10, y_card - 64, f"Address: {str(order.address)[:26]} ({order.address_type})")

    # Card 2: Order & Payment Info
    col2_x = margin + card_w + 14
    p.setFillColor(card_bg)
    p.setStrokeColor(card_border)
    p.roundRect(col2_x, y_card - card_h, card_w, card_h, 5, fill=1, stroke=1)

    p.setFillColor(text_muted)
    p.setFont("Helvetica-Bold", 8)
    p.drawString(col2_x + 10, y_card - 14, "PAYMENT & ORDER STATUS")

    p.setFont("Helvetica-Bold", 9.5)
    p.setFillColor(navy_dark)
    p.drawString(col2_x + 10, y_card - 27, f"Order ID: #{order.id}")

    p.setFont("Helvetica", 8.5)
    p.setFillColor(text_body)
    p.drawString(col2_x + 10, y_card - 40, f"Order Status: {order.status}")
    p.drawString(col2_x + 10, y_card - 55, "Payment Status:")

    # Payment Status Badge
    is_paid = order.payment_status and order.payment_status.lower() in ["paid", "completed"]
    badge_text = "PAID" if is_paid else str(order.payment_status).upper()
    badge_bg = green_bg if is_paid else colors.HexColor("#fff0f3")
    badge_color = green_badge if is_paid else brand_dark
    
    p.setFillColor(badge_bg)
    p.roundRect(col2_x + 84, y_card - 61, 52, 15, 3, fill=1, stroke=0)
    p.setFillColor(badge_color)
    p.setFont("Helvetica-Bold", 7.5)
    p.drawCentredString(col2_x + 110, y_card - 50, badge_text)

    # 4. ITEMS TABLE HEADER
    y_tbl_top = y_card - card_h - 16
    tbl_hdr_h = 22
    p.setFillColor(navy_dark)
    p.roundRect(margin, y_tbl_top - tbl_hdr_h, content_width, tbl_hdr_h, 3, fill=1, stroke=0)

    p.setFillColor(colors.white)
    p.setFont("Helvetica-Bold", 8)
    p.drawString(margin + 10, y_tbl_top - 15, "#")
    p.drawString(margin + 30, y_tbl_top - 15, "ITEM DESCRIPTION")
    p.drawCentredString(345, y_tbl_top - 15, "QTY")
    p.drawRightString(445, y_tbl_top - 15, "PRICE (INR)")
    p.drawRightString(width - margin - 10, y_tbl_top - 15, "TOTAL (INR)")

    # 5. ITEM ROWS (Drawn with clear vertical separation below the header)
    y_row = y_tbl_top - tbl_hdr_h - 16
    row_height = 24
    total = 0
    row_num = 1

    for item in items:
        # Alternating row background
        if row_num % 2 == 0:
            p.setFillColor(row_alt)
            p.rect(margin, y_row - 6, content_width, row_height - 4, fill=1, stroke=0)

        p.setStrokeColor(colors.HexColor("#f1f5f9"))
        p.setLineWidth(0.5)
        p.line(margin, y_row - 6, width - margin, y_row - 6)

        # Product Title
        raw_name = str(item.product.product_name)
        display_name = raw_name[:34] + ("..." if len(raw_name) > 34 else "")

        p.setFillColor(navy_dark)
        p.setFont("Helvetica", 9)
        p.drawString(margin + 10, y_row, str(row_num))
        p.drawString(margin + 30, y_row, display_name)
        p.drawCentredString(345, y_row, str(item.qty))
        p.drawRightString(445, y_row, f"Rs. {item.price:.2f}")
        
        item_tot = item.total_price()
        p.setFont("Helvetica-Bold", 9)
        p.drawRightString(width - margin - 10, y_row, f"Rs. {item_tot:.2f}")

        total += item_tot
        row_num += 1
        y_row -= row_height

        if y_row < 140:
            p.showPage()
            y_row = height - 60

    # 6. TOTALS & SUMMARY SECTION
    y_sum = y_row - 8
    p.setStrokeColor(card_border)
    p.setLineWidth(1)
    p.line(margin, y_sum, width - margin, y_sum)
    y_sum -= 16

    # Breakdown Block on Right
    summary_x = 330
    p.setFont("Helvetica", 9)
    p.setFillColor(text_muted)
    p.drawString(summary_x, y_sum, "Items Subtotal:")
    p.drawRightString(width - margin - 10, y_sum, f"Rs. {total:.2f}")
    y_sum -= 16

    p.drawString(summary_x, y_sum, "Delivery Charges:")
    p.setFillColor(green_badge)
    p.setFont("Helvetica-Bold", 9)
    p.drawRightString(width - margin - 10, y_sum, "FREE")
    y_sum -= 16

    p.setFont("Helvetica", 9)
    p.setFillColor(text_muted)
    p.drawString(summary_x, y_sum, "Insulated Packaging:")
    p.setFillColor(green_badge)
    p.setFont("Helvetica-Bold", 9)
    p.drawRightString(width - margin - 10, y_sum, "FREE")
    y_sum -= 20

    # Grand Total Highlight Box
    p.setFillColor(colors.HexColor("#fff0f3"))
    p.setStrokeColor(brand_pink)
    p.setLineWidth(1.2)
    p.roundRect(summary_x - 10, y_sum - 22, 235, 28, 5, fill=1, stroke=1)

    p.setFillColor(brand_dark)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(summary_x, y_sum - 12, "Grand Total:")
    p.setFont("Helvetica-Bold", 12)
    p.drawRightString(width - margin - 10, y_sum - 12, f"Rs. {total:.2f}")

    # 7. FOOTER NOTE
    p.setStrokeColor(card_border)
    p.setLineWidth(0.8)
    p.line(margin, 50, width - margin, 50)

    p.setFillColor(text_muted)
    p.setFont("Helvetica-Bold", 8)
    p.drawString(margin, 36, "Thank you for choosing HaveMore IceCreams! Crafted with pure joy.")
    p.setFont("Helvetica", 7.5)
    p.drawString(margin, 24, "For support or queries regarding this order, contact: support@havemoreicecreams.com")
    
    p.setFont("Helvetica", 7.5)
    p.drawRightString(width - margin, 36, "Authorized Computer-Generated Invoice")
    p.drawRightString(width - margin, 24, "Page 1 of 1")

    # Finish and save PDF
    p.showPage()
    p.save()

    return response


