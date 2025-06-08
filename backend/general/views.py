from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Prefetch
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

from general.forms import OrderForm, ProductForm
from general.models import Product, Color, Size, ProductImage, Order, Cart, CartItem, ProductVariation, OrderItem


def index(request):
    # Выявление последних 6 вариаций (тип продукта + цвет)
    latest_image_ids = (
        ProductImage.objects
        .values('product', 'color')  # Группировка по продукту и цвету
        .annotate(latest_image_id=Max('id'))  # Берём ID последнего изображения в группе
        .order_by('-latest_image_id')[:6]  # Сортируем по новизне и берём 6
    )

    # 2. Получаем полные объекты ProductImage по найденным ID
    image_ids = [item['latest_image_id'] for item in latest_image_ids]
    products = ProductImage.objects.filter(id__in=image_ids).select_related('product', 'color')
    context = {'products': products}

    return render(request, 'index.html', context)

def logout_view(request):
    logout(request)
    return redirect('index')

def catalog(request):
    # Получаем последние изображения для каждой комбинации продукт+цвет
    latest_images = (
        ProductImage.objects
        .values('product', 'color')
        .annotate(latest_image_id=Max('id'))
        .values_list('latest_image_id', flat=True)
    )

    # Загружаем объекты изображений с продуктами и цветами
    product_images = (
        ProductImage.objects
        .filter(id__in=latest_images)
        .select_related('product', 'color')  # этого достаточно
    )

    context = {
        'product_images': product_images
    }
    return render(request, "catalog.html", context)

# корзина
# добавление в корзину
@require_POST
@login_required
def add_to_cart(request):
    try:
        product_id = request.POST.get('product_id')
        color_id = request.POST.get('color')
        size_id = request.POST.get('size')

        product = get_object_or_404(Product, id=product_id)
        color = get_object_or_404(Color, id=color_id) if color_id else None
        size = get_object_or_404(Size, id=size_id) if size_id else None

        cart, created = Cart.objects.get_or_create(user=request.user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            color=color,
            size=size,
            defaults={'quantity': 1}
        )

        if not created:
            cart_item.quantity += 1
            cart_item.save()

        return JsonResponse({
            'success': True,
            'redirect_url': product.get_absolute_url(),  # Перенаправляем на страницу товара
            'message': 'Товар добавлен в корзину',
            'cart_count': cart.total_items

        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

# получение размера
def get_sizes(request):
    product_id = request.GET.get('product_id')
    color_id = request.GET.get('color_id')
    # Здесь логика получения доступных размеров для товара и цвета
    # Например:
    try:
        product_color = ProductVariation.objects.get(product_id = product_id, color_id = color_id)
        sizes = product_color.size.all()
        sizes_data = [{'id': size.id, 'name': size.name} for size in sizes]
        return JsonResponse({'sizes': sizes_data})
    except ProductVariation.DoesNotExist:
        return JsonResponse({'sizes': []})

# получение цвета
def switch_color(request):
    product_id = request.GET.get('product_id')
    color_id = request.GET.get('color_id')

    product = get_object_or_404(Product, id=product_id)
    variation = product.productvariation_set.filter(color_id=color_id).first()

    if not variation:
        return HttpResponse("Цвет не найден", status=404)

    image = variation.productimage_set.first

    context = {
        'image': image  # предполагаем, что image содержит ссылку на product и color
    }

    return render(request, 'product_card.html', context)

# корзина
@login_required
def cart_view(request):
    # Загружаем все элементы корзины текущего пользователя
    items = CartItem.objects.filter(cart__user=request.user).select_related('product', 'color', 'size')

    # Получаем последние изображения по сочетаниям product + color
    latest_images = (
        ProductImage.objects
        .values('product', 'color')
        .annotate(latest_id=Max('id'))
        .values_list('latest_id', flat=True)
    )

    images = (
        ProductImage.objects
        .filter(id__in=latest_images)
        .select_related('product', 'color')
    )

    # Создаём словарь (product_id, color_id) → image
    image_map = {
        (img.product.id, img.color.id): img
        for img in images
    }

    # Назначаем каждому item его картинку
    for item in items:
        key = (item.product.id, item.color.id if item.color else None)
        item.image = image_map.get(key)

    # Общая сумма
    total_price = sum(item.total_price for item in items)

    return render(request, 'cart.html', {
        'items': items,
        'cart': {
            'total_price': total_price
        }
    })

# оформление заказа
@login_required
def create_order(request):
    selected_items_ids = request.session.get("selected_items")

    if not selected_items_ids:
        messages.error(request, "Вы не выбрали товары для оформления.")
        return redirect("cart")

    selected_items = CartItem.objects.filter(id__in=selected_items_ids, cart__user=request.user)
    total_price = sum(item.total_price for item in selected_items)

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()

            for item in selected_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    color=item.color,
                    size=item.size,
                    quantity=item.quantity,
                    price=item.product.price
                )

            selected_items.delete()
            del request.session["selected_items"]
            return redirect("order_success", order_id=order.id)
        else:
            print("Ошибки формы:", form.errors)
    else:
        form = OrderForm()

    return render(request, "create_order.html", {
        "form": form,
        "selected_items": selected_items,
        "total_price": total_price,
    })


# передача чекбоксов из корзины в оформление заказа
def proceed_to_order(request):
    if request.method == "POST":
        selected_items = request.POST.getlist("selected_items")
        if not selected_items:
            messages.warning(request, "Вы не выбрали товары для оформления.")
            return redirect("cart")
        request.session["selected_items"] = selected_items
        return redirect("create_order")  # URL на create_order_view
    return redirect("cart")

# изменения в корзине
@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('cart_view')


@login_required
def update_cart_item(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        quantity = int(request.POST.get('quantity', 1))

        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            cart = cart_item.cart
            return JsonResponse({
                'success': True,
                'cart_total': cart.total_items,
                'item_total': cart_item.total_price,
                'cart_total_price': cart.total_price
            })

# успешный заказ
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "order_success.html", {"order": order})

# профиль пользователя
def profile(request):
    orders = Order.objects.filter(user=request.user).prefetch_related(
        'items__product', 'items__color', 'items__size'
    ).select_related('address')

    return render(request, 'profile.html', {
        'orders': orders,
    })









@staff_member_required
def admin_dashboard(request):
    status_filter = request.GET.get("status", "")
    orders = Order.objects.all()
    if status_filter:
        orders = orders.filter(status=status_filter)

    return render(request, "admin_panel/dashboard.html", {
        "orders": orders,
        "products": Product.objects.all(),
        "status_filter": status_filter,
    })


@staff_member_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == "POST":
        order.status = request.POST.get("status")
        order.save()
    return redirect("admin_dashboard")


@staff_member_required
def edit_product(request, product_id=None):
    if product_id:
        product = get_object_or_404(Product, id=product_id)
    else:
        product = None

    form = ProductForm(request.POST or None, instance=product)
    if form.is_valid():
        form.save()
        return redirect("admin_dashboard")

    return render(request, "admin_panel/edit_product.html", {"form": form})













@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('cart_view')


@login_required
def update_cart_item(request, item_id):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        quantity = int(request.POST.get('quantity', 1))

        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            cart = cart_item.cart
            return JsonResponse({
                'success': True,
                'cart_total': cart.total_items,
                'item_total': cart_item.total_price,
                'cart_total_price': cart.total_price
            })

    return redirect('cart_view')

# детали продукта
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    images = ProductImage.objects.filter(product=product)
    return render(request, 'product_detail.html', {
        'product': product,
        'images': images
    })

# сама корзина
@login_required
def cart_detail(request):
    cart = Cart.objects.get_or_create(user=request.user)[0]
    items = cart.items.select_related('product', 'color', 'size').all()

    return render(request, 'cart.html', {
        'cart': cart,
        'items': items
    })


# @login_required
# def create_order(request):
#     if request.method == 'POST':
#         cart = request.user.cart
#         items = cart.items.all()
#
#         if not items.exists():
#             return redirect('cart_detail')
#
#         # Создаем заказ
#         order = Order.objects.create(
#             user=request.user,
#             address=request.POST.get('address'),
#             type_payment=request.POST.get('payment_method'),
#             status='0'  # Новый заказ
#         )
#
#         # Добавляем товары в заказ
#         order.product.set([item.product for item in items])
#
#         # Очищаем корзину
#         items.delete()
#
#         return render(request, 'order_success.html', {'order': order})
#
#     return redirect('cart_detail')












# def product_detail(request, product_id, color_id):
#     product = get_object_or_404(Product, pk=product_id)
#     color = get_object_or_404(Color, pk=color_id)
#     images = ProductImage.objects.filter(product=product, color=color)
#
#     return render(request, 'product_detail.html', {
#         'product': product,
#         'color': color,
#         'images': images
#     })
#
#
#
#
#
# def register(request):
#     if request.user.is_authenticated or request.user.is_superuser:
#         return redirect('profile')
#     # latest_question_list = Question.objects.order_by("-pub_date")[:5]
#     # context = {"latest_question_list": latest_question_list}
#     return render(request, "registration.html")
#
# def profile(request):
#     if not request.user.is_authenticated:
#         return redirect('index')
#     # latest_question_list = Question.objects.order_by("-pub_date")[:5]
#     # context = {"latest_question_list": latest_question_list}
#     return render(request, "profile.html")
#
# def bascet(request):
#     if not request.user.is_authenticated:
#         return redirect('index')
#     # latest_question_list = Question.objects.order_by("-pub_date")[:5]
#     # context = {"latest_question_list": latest_question_list}
#     return render(request, "bascet.html")
#
# def order_list(request):
#     if not request.user.is_authenticated:
#         return redirect('index')
#     orders = Order.objects.all()
#     context = {'orders': orders}
#     return render(request, 'order_list.html', context)
# def product_card(request):
#     # latest_question_list = Question.objects.order_by("-pub_date")[:5]
#     # context = {"latest_question_list": latest_question_list}
#     return render(request, "product_card.html")
#
#
#
#
#
#
#
#
#
#
# @login_required
# def cart_view(request):
#     cart, created = Cart.objects.get_or_create(user=request.user)
#     return render(request, 'cart_view.html', {'cart': cart})
#
#
# @login_required
# def add_to_cart(request):
#     if request.method == 'POST':
#         product_id = request.POST.get('product_id')
#         color_id = request.POST.get('color')
#         size_id = request.POST.get('size')
#         quantity = int(request.POST.get('quantity', 1))
#
#         product = get_object_or_404(Product, id=product_id)
#         color = get_object_or_404(Color, id=color_id) if color_id else None
#         size = get_object_or_404(Size, id=size_id) if size_id else None
#
#         cart, created = Cart.objects.get_or_create(user=request.user)
#
#         # Ищем такой же товар в корзине
#         cart_item = CartItem.objects.filter(
#             cart=cart,
#             product=product,
#             color=color,
#             size=size
#         ).first()
#
#         if cart_item:
#             cart_item.quantity += quantity
#             cart_item.save()
#         else:
#             CartItem.objects.create(
#                 cart=cart,
#                 product=product,
#                 color=color,
#                 size=size,
#                 quantity=quantity
#             )
#
#         return redirect('cart:view')
#
#
# @login_required
# def remove_from_cart(request, item_id):
#     cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
#     cart_item.delete()
#     return redirect('cart:view')
#
#
# @login_required
# def update_cart_item(request, item_id):
#     cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
#     quantity = int(request.POST.get('quantity', 1))
#
#     if quantity > 0:
#         cart_item.quantity = quantity
#         cart_item.save()
#     else:
#         cart_item.delete()
#
#     return redirect('cart:view')