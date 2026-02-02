from django.urls import path
from adminsite.views.page_views import login_page, dashboard_page , users_page , sellers_page , products_page  , messages_page , orders_page
from adminsite.views.auth_views import LoginAPI, LogoutAPI
from adminsite.views.user_views import UserListCreateAPI, UserDetailAPI
from adminsite.views.seller_views import SellerListCreateAPI, SellerDetailAPI
from adminsite.views.product_views import  ProductListCreateAPI, ProductDetailAPI
from adminsite.views.message_views import  MessageListAPI,MessageDeleteAPI
from adminsite.views.order_views import  OrderListAPI,OrderDetailAPI
from adminsite.views.dashboard_views import DashboardStatsAPI


urlpatterns = [
    # Pages
    path("login/", login_page, name="admin_login"),
    path("dashboard/", dashboard_page, name="admin_dashboard"),
    path("users/", users_page, name="admin_users"),
    path("sellers/", sellers_page, name="admin_sellers"),
    path("products/", products_page, name="admin_products"),
    path("orders/", orders_page, name="admin_orders"),
    path("messages/", messages_page, name="admin_messages"),


    # APIs

    # Auth
    path("api/login/", LoginAPI.as_view(),name="admin_login_api"),
    path("api/logout/", LogoutAPI.as_view(), name="admin_logout_api"),


    # User , Seller & Product , Order And Messages Api
    path("api/users/", UserListCreateAPI.as_view() , name="users_api"),
    path("api/users/<int:pk>/", UserDetailAPI.as_view(),name="user_detail_api"),
    path("api/sellers/", SellerListCreateAPI.as_view()),
    path("api/sellers/<int:pk>/", SellerDetailAPI.as_view()),
    path("api/products/", ProductListCreateAPI.as_view(), name="admin_products_api"),
    path("api/products/<int:pk>/", ProductDetailAPI.as_view(), name="admin_product_detail_api"),
    path("api/messages/", MessageListAPI.as_view(), name="admin_messages_api"),
    path("api/messages/<int:pk>/", MessageDeleteAPI.as_view(), name="admin_message_delete_api"),
    path("api/orders/", OrderListAPI.as_view(), name="admin_orders_api"),
    path("api/orders/<int:pk>/", OrderDetailAPI.as_view(), name="admin_order_detail_api"),
    path("api/dashboard/stats/", DashboardStatsAPI.as_view(), name="dashboard_stats_api"),

]
