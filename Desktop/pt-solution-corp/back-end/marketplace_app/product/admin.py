from django.contrib import admin
from .models import Product, ProductImage



class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'stock_quantity', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)

    inlines = [ProductImageInline]