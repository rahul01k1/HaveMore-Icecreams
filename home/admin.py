from django.contrib import admin
from  .models import Buyer , Seller , Product , Cart , Wishlist , Message , Newsletter ,Order , OrderItem



@admin.register(Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = ('id','user_name','user_email')
    search_fields = ('id','user_name','user_email')

@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ('id','seller_name','seller_email')
    search_fields = ('id','seller_name','seller_email')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id','product_name','product_price','product_stock','product_detail','product_status')
    search_fields = ('id','product_name','product_status')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "price", "qty")
    search_fields = ('id','product','price')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "product", "price")
    search_fields = ('id',"user",'product','price')



@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user",  "status", "payment_status", "date")
    list_filter = ("status", "payment_status")
    search_fields = ("buyer__user_name", "id")

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "seller", "price", "qty")
    list_filter = ("seller",)
    search_fields = ("order__id", "product__product_name")

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "name", "email", "subject", "created_at")
    search_fields = ('id','user','email',)


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "created_at")
    search_fields = ('id','email',)