from django import forms
from .models import Order, PickupPoint, Product, Color, Size, ProductVariation, ProductImage


class OrderForm(forms.ModelForm):
    """
    Форма для оформления заказа.
    Позволяет выбрать способ оплаты и пункт самовывоза.
    """

    class Meta:
        model = Order  # Используем модель Order
        fields = ['type_payment', 'address']  # Поля для отображения
        widgets = {
            'type_payment': forms.RadioSelect,  # Радиокнопки для выбора оплаты
            'address': forms.Select,  # Выпадающий список для пунктов выдачи
        }

    def __init__(self, *args, **kwargs):
        """
        Инициализация формы с дополнительными настройками полей.
        """
        super().__init__(*args, **kwargs)

        # Настройка поля выбора пункта самовывоза
        self.fields['address'].queryset = PickupPoint.objects.all()  # Все доступные пункты
        self.fields['address'].required = True  # Обязательное поле
        self.fields['address'].label = "Выберите пункт самовывоза"  # Кастомный лейбл
        self.fields['address'].widget.attrs.update({'class': 'form-select'})  # CSS-класс

        # Настройка поля выбора способа оплаты
        self.fields['type_payment'].required = True  # Обязательное поле
        self.fields['type_payment'].label = "Способ оплаты"  # Кастомный лейбл
        self.fields['type_payment'].widget.attrs.update({'class': 'form-check-input'})  # CSS-класс


class ProductForm(forms.ModelForm):
    """
    Форма для создания/редактирования продукта.
    Содержит основные поля продукта: название, описание и цену.
    """

    class Meta:
        model = Product  # Используем модель Product
        fields = ['name', 'description', 'price']  # Поля для отображения
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3  # Высота текстового поля
            }),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ProductVariationForm(forms.Form):
    """
    Форма для выбора вариаций продукта (цвета и размеры).
    Не привязана напрямую к модели, используется для обработки выбора.
    """
    # Поле для выбора цветов (множественный выбор)
    color = forms.ModelMultipleChoiceField(
        queryset=Color.objects.all(),  # Все доступные цвета
        widget=forms.CheckboxSelectMultiple,  # Чекбоксы для выбора
        label='Цвета'  # Лейбл поля
    )

    # Поле для выбора размеров (множественный выбор)
    size = forms.ModelMultipleChoiceField(
        queryset=Size.objects.all(),  # Все доступные размеры
        widget=forms.CheckboxSelectMultiple,  # Чекбоксы для выбора
        label='Размеры'  # Лейбл поля
    )