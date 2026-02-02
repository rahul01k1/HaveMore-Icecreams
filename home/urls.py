from django.urls import path 
from . import views


urlpatterns = [

    # Pages
    path('', views.home, name="home"),
    path('menu/', views.menu, name="menu"),
    path('order/', views.order, name="order"),
    path('about/', views.about, name="about"),
    path('contact/', views.contact, name="contact"),

    # View Product / Orders
    path('view_product/<int:id>/', views.view_product, name="view_product"),
    path('view_order/<int:id>/', views.view_order, name="view_order"),
    path('order_success/<int:order_id>/', views.order_success, name="order_success"),
    
    path('cancel_order/<int:id>/', views.cancel_order, name="cancel_order"),

    # Search
    path('search/', views.search_product, name="search_product"),

    # download invoice
    path("download-invoice/<int:order_id>/", views.download_invoice, name="download_invoice"),


    # Cart
    path('cart/', views.cart, name="cart"),
    path('add_to_cart/<int:id>/', views.add_to_cart, name="add_to_cart"),
    path('update_cart/<int:id>/', views.update_cart, name="update_cart"),
    path('remove_cart/<int:id>/', views.remove_cart, name="remove_cart"),
    path('empty_cart/', views.empty_cart, name="empty_cart"),

    # Wishlist
    path('wishlist/', views.wishlist, name="wishlist"),
    path("toggle_wishlist/", views.toggle_wishlist, name="toggle_wishlist"),
    path('add_to_wishlist/<int:id>/', views.add_to_wishlist, name="add_to_wishlist"),
    path('remove_wishlist/<int:id>/', views.remove_wishlist, name="remove_wishlist"),


    path("cart-count/", views.cart_count, name="cart_count"),
    path("wishlist-count/", views.wishlist_count, name="wishlist_count"),


    # Checkout
    path('checkout/', views.checkout, name="checkout"),
    path('add_newsletter/', views.add_newsletter, name="add_newsletter"),
    
    # path('checkout/<int:id>', views.checkout, name="checkout"),

    
    # Profile
    path('profile/', views.profile, name="profile"),
    path('update_profile/', views.update_profile, name="update_profile"),
    path('user_messages/', views.user_messages, name="user_messages"),

    # Authentication
    path('login/', views.user_login, name="login"),
    path('register/', views.user_register, name="register"),
    path('logout/', views.user_logout, name="logout"),
]
