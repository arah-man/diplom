from tkinter.font import names
from django.urls import path
from django.contrib.auth import views as auth_views

from general.views import index, catalog, logout_view, cart_view, add_to_cart, remove_from_cart, update_cart_item, product_detail, cart_detail, create_order, get_sizes, switch_color, order_success, proceed_to_order, profile
urlpatterns = [
    path('', index, name = 'index'),
    path('catalog/', catalog, name='catalog'),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="login.html"), name='login'),
    path('logout/', logout_view, name='logout'),

    path('profile/', profile, name='profile'),

    path('cart/', cart_view, name='cart_view'),
    path('add_to_cart/', add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('update_cart_item/<int:item_id>/', update_cart_item, name='update_cart_item'),
    path('product_detail/<int:pk>/', product_detail, name='product_detail'),
    path('cart_detail/', cart_detail, name='cart_detail'),
    path('create_order/', create_order, name='create_order'),
    path('get_sizes/', get_sizes, name='get_sizes'),
    path('switch_color/', switch_color, name='switch_color'),
    path('proceed_to_order/', proceed_to_order, name='proceed_to_order'),
    path('order_success/<int:order_id>/', order_success, name='order_success'),

    # path('product_card/', product_card, name='product_card'),
    # path('product_detail/', product_detail, name='product_detail'),
    #
    # path('cart_view', cart_view, name='cart_view'),
    # path('add_to_cart/', add_to_cart, name='add_to_cart'),
    # path('remove_from_cart/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    # path('update_cart_item/<int:item_id>/', update_cart_item, name='update_cart_item'),
]
