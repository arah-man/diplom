from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Prefetch
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required

from general.forms import OrderForm, ProductForm, ProductVariationForm, UserForm, UserProfileForm
from general.models import Product, Color, Size, ProductImage, Order, Cart, CartItem, ProductVariation, OrderItem

# страницы
# главная страница
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
# каталог
def catalog(request):
    product_images = []

    images = ProductImage.objects.select_related('product', 'color')

    for image in images:
        # Получаем все вариации с тем же продуктом и цветом
        variations = ProductVariation.objects.filter(product=image.product, color=image.color).prefetch_related('size')

        # Собираем размеры
        sizes = set()
        for var in variations:
            sizes.update(var.size.all())

        # Собираем все цвета для этого продукта
        all_variations = ProductVariation.objects.filter(product=image.product).select_related('color')
        color_set = set(v.color for v in all_variations)

        product_images.append({
            'product': image.product,
            'image': image,
            'color': image.color,
            'sizes': sorted(sizes, key=lambda s: s.name),
            'colors': sorted(color_set, key=lambda c: c.name),
        })

    return render(request, 'catalog.html', {
        'product_images': product_images
    })
# страница товара
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_detail.html', {'product': product})
# профиль пользователя
def profile(request):
    orders = Order.objects.filter(user=request.user).prefetch_related(
        'items__product', 'items__color', 'items__size'
    ).select_related('address').order_by('-date_at')

    return render(request, 'profile.html', {
        'orders': orders,
    })
# админка управления заказами
def admin_order(request):
    status = request.GET.get('status')
    orders = Order.objects.all().order_by('-date_at')
    if status:
        orders = orders.filter(status=status)
    return render(request, 'admin_order.html', {'orders': orders})
# админка работа с товарами
def admin_product(request):
    products = Product.objects.all()
    colors = Color.objects.all()
    sizes = Size.objects.all()
    return render(request, 'admin_product.html', {
        'products': products,
        'colors': colors,
        'sizes': sizes
    })
# страница товара
def product_detail(request, product_id, color_id):
    product = get_object_or_404(Product, pk=product_id)
    variation = get_object_or_404(ProductVariation, product=product, color__id=color_id)
    images = ProductImage.objects.filter(product=product, color__id=color_id)
    sizes = variation.size.all()

    context = {
        'product': product,
        'variation': variation,
        'images': images,
        'sizes': sizes,
    }
    return render(request, 'product_detail.html', context)
# о нас
def about(request):
    return render(request, 'about.html')
# регистрация
def register(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = UserProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user.password)  # хеширование пароля
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            login(request, user)  # автоматически входить после регистрации
            return redirect('profile') 

    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render(request, 'register.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


# корзина
# страница корзины
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
# добавление товара в корзину
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
            'message': 'Товар добавлен в корзину',
            'cart_count': cart.total_items

        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
# удаление товара
@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('cart')


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
# выход
def logout_view(request):
    logout(request)
    return redirect('index')


# создание заказа
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
# выбор товаров в заказ
def proceed_to_order(request):
    if request.method == "POST":
        selected_items = request.POST.getlist("selected_items")
        if not selected_items:
            messages.warning(request, "Вы не выбрали товары для оформления.")
            return redirect("cart")
        request.session["selected_items"] = selected_items
        return redirect("create_order")  # URL на create_order_view
    return redirect("cart")
# изменение количество товара
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


# работа в админке
# изменение статуса заказа
@login_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        cancel_reason = request.POST.get('cancel_reason', '').strip()

        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status

            if new_status == '4':
                if not cancel_reason:
                    messages.error(request, "Пожалуйста, укажите причину отмены заказа.")
                    return redirect(request.META.get('HTTP_REFERER', '/'))
                order.cancel_reason = cancel_reason
            else:
                order.cancel_reason = ''

            order.save()
            messages.success(request, f"Статус заказа №{order.id} успешно обновлён.")
        else:
            messages.error(request, "Недопустимый статус.")

    return redirect(request.META.get('HTTP_REFERER', '/'))
# создание нового товара
@login_required
def add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')

        # Новый цвет
        new_color_name = request.POST.get('new_color_name')
        new_color_hex = request.POST.get('new_color_hex')

        # Новый размер
        new_size_name = request.POST.get('new_size_name')

        # Создаем продукт
        product = Product.objects.create(
            name=name,
            description=description,
            price=price
        )

        # Обработка цвета
        color_ids = request.POST.getlist('colors')
        if new_color_name and new_color_hex:
            color = Color.objects.create(name=new_color_name, hex_code=new_color_hex)
            color_ids.append(str(color.id))
        colors = Color.objects.filter(id__in=color_ids)

        # Обработка размеров
        size_ids = request.POST.getlist('sizes')
        if new_size_name:
            size = Size.objects.create(name=new_size_name)
            size_ids.append(str(size.id))
        sizes = Size.objects.filter(id__in=size_ids)

        # Создаем вариацию (одну для всех сочетаний)
        variation = ProductVariation.objects.create(product=product)
        variation.color.set(colors)
        variation.size.set(sizes)

        # Обработка изображений
        images = request.FILES.getlist('images')
        for color in colors:
            for image in images:
                ProductImage.objects.create(
                    product=product,
                    color=color,
                    image=image
                )

        return redirect('admin_product')

    return redirect('admin_product')
# изменение существующего товара
@login_required
def update_product(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.save()

        # Новый цвет
        new_color_name = request.POST.get('new_color_name')
        new_color_hex = request.POST.get('new_color_hex')
        color_ids = request.POST.getlist('colors')
        if new_color_name and new_color_hex:
            color = Color.objects.create(name=new_color_name, hex_code=new_color_hex)
            color_ids.append(str(color.id))
        colors = Color.objects.filter(id__in=color_ids)

        # Новый размер
        new_size_name = request.POST.get('new_size_name')
        size_ids = request.POST.getlist('sizes')
        if new_size_name:
            size = Size.objects.create(name=new_size_name)
            size_ids.append(str(size.id))
        sizes = Size.objects.filter(id__in=size_ids)

        # Удаляем старые вариации и изображения
        ProductVariation.objects.filter(product=product).delete()
        ProductImage.objects.filter(product=product).delete()

        # Создаем новую вариацию
        variation = ProductVariation.objects.create(product=product)
        variation.color.set(colors)
        variation.size.set(sizes)

        # Обработка новых изображений
        images = request.FILES.getlist('images')
        for color in colors:
            for image in images:
                ProductImage.objects.create(
                    product=product,
                    color=color,
                    image=image
                )

        return redirect('admin_product')

    return redirect('admin_product')



