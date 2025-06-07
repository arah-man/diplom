from django.contrib import admin

from general.models import Color, Size, Product, ProductImage, UserProfile, Order, Cart, CartItem, ProductVariation, OrderItem, PickupPoint


admin.site.register(Size)
admin.site.register(Product)
admin.site.register(ProductImage)
admin.site.register(UserProfile)
admin.site.register(Order)

admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(ProductVariation)
admin.site.register(OrderItem)
admin.site.register(PickupPoint)

class ColorAdmin(admin.ModelAdmin):
    list_display = ('colored_circle', 'name', 'hex_code')
    search_fields = ('name',)

admin.site.register(Color, ColorAdmin)
