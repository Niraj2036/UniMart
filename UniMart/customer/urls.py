from django.urls import path
from . import views

urlpatterns = [
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('address', views.address, name='address'),
    path('user_dashboard', views.user_dashboard, name='user_dashboard'),
    path('shopdetails', views.shopdetails, name='shopdetails'),
    path('seller_dashboard', views.seller_dashboard, name='seller_dashboard'),
    path('manage_products_ins',views.manage_products_ins,name='manage_products_ins'),
    path('manage_products_upd/<int:product_id>',views.manage_products_upd,name='manage_products_upd'),
    path('manage_products_del/<int:product_id>',views.manage_products_del,name='manage_products_del'),
    path('order_list',views.list_orders,name='order_list'),
    path('update_order_status/<int:order_id>',views.update_order_status,name='order_status_update'),
    path('shop_details/<int:id>',views.shop_details,name='shop_details'),
    path('product_details/<int:id>',views.product_details,name='product_details'),
    path('cart/', views.view_cart, name='cart_view'),
    path('product/add_to_cart/<str:product_id_quantity>/', views.add_to_cart, name='add_to_cart'),
    path('remove/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('edit_cart_item/<str:cart_item_id_quantity>', views.edit_cart_item, name='edit_cart_item'),
    path('make_order',views.create_order_from_cart),
]
