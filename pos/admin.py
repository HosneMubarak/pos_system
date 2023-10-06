from django.contrib import admin

from .models import Category, Product, Sale, SaleItem, StockTransaction


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'date_added', 'date_updated')
    list_filter = ('status',)
    search_fields = ('name', 'description')
    list_per_page = 20


class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'code', 'name', 'category', 'buy_price', 'sell_price', 'status', 'date_added', 'date_updated')
    list_filter = ('status', 'category')
    search_fields = ('code', 'name', 'description')
    list_per_page = 20


class SaleAdmin(admin.ModelAdmin):
    list_display = ('code', 'sub_total', 'grand_total', 'date_added', 'date_updated')
    search_fields = ('code',)
    list_per_page = 20


class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('sale', 'product', 'price', 'qty', 'total')
    list_filter = ('sale', 'product')
    list_per_page = 20


class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ('product', 'transaction_type', 'quantity', 'date', 'note')
    list_filter = ('transaction_type', 'product')
    search_fields = ('product__code', 'note')
    list_per_page = 20


# Register your models and admin classes
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(SaleItem, SaleItemAdmin)
admin.site.register(StockTransaction, StockTransactionAdmin)
