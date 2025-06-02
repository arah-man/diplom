from tkinter.font import names
from django.urls import path
from django.contrib.auth import views as auth_views

from general.views import index, catalog, logout_view, cart_view, add_to_cart, remove_from_cart, update_cart_item, product_detail, cart_detail, create_order
urlpatterns = [
    path('', index, name = 'index'),
    path('catalog/', catalog, name='catalog'),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="login.html"), name='login'),
    path('logout/', logout_view, name='logout'),



    path('cart/', cart_view, name='cart_view'),
    path('cart/add/', add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', update_cart_item, name='update_cart_item'),
    path('product/<int:pk>/', product_detail, name='product_detail'),
    path('cart/', cart_detail, name='cart_detail'),
    path('cart/checkout/', create_order, name='create_order'),

    # path('product_card/', product_card, name='product_card'),
    # path('product_detail/', product_detail, name='product_detail'),
    #
    # path('cart_view', cart_view, name='cart_view'),
    # path('add_to_cart/', add_to_cart, name='add_to_cart'),
    # path('remove_from_cart/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    # path('update_cart_item/<int:item_id>/', update_cart_item, name='update_cart_item'),
]
