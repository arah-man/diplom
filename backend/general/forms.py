from django import forms
from .models import Order, PickupPoint, Product, Color, Size, ProductVariation, ProductImage


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['type_payment', 'address']
        widgets = {
            'type_payment': forms.RadioSelect,
            'address': forms.Select,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['address'].queryset = PickupPoint.objects.all()
        self.fields['address'].required = True
        self.fields['address'].label = "Выберите пункт самовывоза"
        self.fields['address'].widget.attrs.update({'class': 'form-select'})

        self.fields['type_payment'].required = True
        self.fields['type_payment'].label = "Способ оплаты"
        self.fields['type_payment'].widget.attrs.update({'class': 'form-check-input'})


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ProductVariationForm(forms.Form):
    color = forms.ModelMultipleChoiceField(
        queryset=Color.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Цвета'
    )
    size = forms.ModelMultipleChoiceField(
        queryset=Size.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label='Размеры'
    )