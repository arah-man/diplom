from django.urls import path
from django.contrib.auth import views as auth_views

from general.views import index, catalog, logout_view, cart_view, add_to_cart, remove_from_cart, update_cart_item
from general.views import product_detail, create_order, get_sizes, switch_color, order_success, proceed_to_order, register
from general.views import profile, admin_order, admin_product, update_order_status, add_product, update_product, product_detail, about

urlpatterns = [
    path('', index, name = 'index'),
    path('catalog/', catalog, name='catalog'),
    path('profile/', profile, name='profile'),
    path('product_detail/<int:pk>/', product_detail, name='product_detail'),
    path('admin_order/', admin_order, name='admin_order'),
    path('admin_product/', admin_product, name='admin_product'),
    path('product_detail/<int:product_id>/<int:color_id>/', product_detail, name='product_detail'),
    path('about/', about, name='about'),
    path('register/', register, name='register'),

    path("accounts/login/", auth_views.LoginView.as_view(template_name="login.html"), name='login'),
    path('logout/', logout_view, name='logout'),
    path('get_sizes/', get_sizes, name='get_sizes'),
    path('switch_color/', switch_color, name='switch_color'),

    path('cart/', cart_view, name='cart_view'),
    path('add_to_cart/', add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:item_id>/', remove_from_cart, name='remove_from_cart'),

    path('create_order/', create_order, name='create_order'),
    path('proceed_to_order/', proceed_to_order, name='proceed_to_order'),
    path('update_cart_item/<int:item_id>/', update_cart_item, name='update_cart_item'),
    path('order_success/<int:order_id>/', order_success, name='order_success'),

    path('update_order_status/<int:order_id>/', update_order_status, name='update_order_status'),
    path('add_product', add_product, name='add_product'),
    path('update_product/<int:product_id>/', update_product, name='update_product'),
]
