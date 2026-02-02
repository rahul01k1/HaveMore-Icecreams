from django.db import models
from decimal import Decimal


# ---------------------------------------------------------
# Buyer Model
# ---------------------------------------------------------
class Buyer(models.Model):
    user_name = models.CharField(max_length=100)
    user_email = models.EmailField(max_length=200, unique=True)
    user_password = models.CharField(max_length=200)
    user_image = models.ImageField(upload_to="profiles/", default="profiles/user_profile.jpg")
    role = models.CharField(default="user", max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Buyer"
        verbose_name_plural = "Buyers"

    def __str__(self):
        return self.user_name
    

# ---------------------------------------------------------
# Seller Model
# ---------------------------------------------------------
class Seller(models.Model):
    seller_name = models.CharField(max_length=200)
    seller_email = models.EmailField(max_length=200, unique=True)
    seller_password = models.CharField(max_length=200)
    seller_image = models.ImageField(upload_to="sellers/", default="sellers/seller_profile.jpg")
    role = models.CharField(default="seller",choices=[('admin', 'Admin'), ('seller', 'Seller')], max_length=20)
    seller_status = models.CharField(max_length=20,choices=[("active","Active"),("inactive","Inactive")],default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Seller"
        verbose_name_plural = "Sellers"

    def __str__(self):
        return self.seller_name
    

# ---------------------------------------------------------
# Product Model
# ---------------------------------------------------------
class Product(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    product_price = models.DecimalField(max_digits=10, decimal_places=2,default=Decimal("10.00"))
    product_image = models.ImageField(upload_to="products/")
    product_stock = models.IntegerField()
    product_detail = models.TextField()
    product_status = models.CharField(max_length=100)
    add_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return self.product_name


# ---------------------------------------------------------
# Cart Model
# ---------------------------------------------------------
class Cart(models.Model):
    user = models.ForeignKey(Buyer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    qty = models.IntegerField(default=1)

    def subtotal(self):
        return self.price * self.qty

    class Meta:
        ordering = ["-id"]
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"

    def __str__(self):
        return f"{self.user.user_name} - {self.product.product_name}"


# ---------------------------------------------------------
# Wishlist Model
# ---------------------------------------------------------
class Wishlist(models.Model):
    user = models.ForeignKey(Buyer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Wishlist Item"
        verbose_name_plural = "Wishlist Items"

    def __str__(self):
        return f"{self.user.user_name} - {self.product.product_name}"
    
# ---------------------------------------------------------
# Order Model
# ---------------------------------------------------------
class Order(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(Buyer, on_delete=models.CASCADE)

    # Shipping / Contact information
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    number = models.CharField(max_length=10)
    address = models.CharField(max_length=255)
    address_type = models.CharField(max_length=100)

    # Status
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=100, default="in-Progress..")
    payment_status = models.CharField(max_length=255, default="pending")

    def order_total(self):
        return sum(item.total_price() for item in self.items.all()) # type: ignore

    def __str__(self):
        return f"Order #{self.id} - {self.user.user_name}"


# ---------------------------------------------------------
# OrderItem Model
# ---------------------------------------------------------
class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)
    
    order = models.ForeignKey(
        Order,
        related_name="items",
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    qty = models.IntegerField(default=1)

    def total_price(self):
        return self.price * self.qty

    def __str__(self):
        return f"{self.product.product_name} (x{self.qty})"





# ---------------------------------------------------------
# Message Model
# ---------------------------------------------------------
class Message(models.Model):
    user = models.ForeignKey(Buyer, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=100)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"{self.user.user_name} - {self.subject}"


# ---------------------------------------------------------
# Newsletter
# ---------------------------------------------------------
class Newsletter(models.Model):
    email = models.EmailField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "Newsletter"
        verbose_name_plural = "Newsletters"

    def __str__(self):
        return self.email
