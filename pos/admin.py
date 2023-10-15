from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import Category, Product, Sale, SaleItem, StockTransaction, PaymentType


# Create resources for each model
class CategoryResource(resources.ModelResource):
    class Meta:
        model = Category
        fields = '__all__'


class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        fields = '__all__'


class SaleResource(resources.ModelResource):
    class Meta:
        model = Sale
        fields = '__all__'


class SaleItemResource(resources.ModelResource):
    class Meta:
        model = SaleItem
        fields = '__all__'


class StockTransactionResource(resources.ModelResource):
    class Meta:
        model = StockTransaction
        fields = '__all__'


class PaymentTypeResource(resources.ModelResource):
    class Meta:
        model = PaymentType
        fields = '__all__'


# Update Admin classes
class CategoryAdmin(ImportExportModelAdmin):
    model = Category
    list_display = ('name', 'status', 'date_added', 'date_updated')
    list_filter = ('status',)
    search_fields = ('name', 'description')
    list_per_page = 20


class ProductAdmin(ImportExportModelAdmin):
    model = Product
    list_display = (
        'code', 'name', 'category', 'buy_price', 'sell_price', 'status', 'date_added', 'date_updated')
    list_filter = ('status', 'category')
    search_fields = ('code', 'name', 'description')
    list_per_page = 20


class SaleAdmin(ImportExportModelAdmin):
    model = Sale
    list_display = ('code', 'sub_total', 'grand_total', 'date_added', 'date_updated')
    search_fields = ('code',)
    list_per_page = 20


class SaleItemAdmin(ImportExportModelAdmin):
    model = SaleItem
    list_display = ('sale', 'product', 'price', 'qty', 'total')
    list_filter = ('sale', 'product')
    list_per_page = 20


class StockTransactionAdmin(ImportExportModelAdmin):
    model = StockTransaction
    list_display = ('product', 'transaction_type', 'quantity', 'date_added', 'note')
    list_filter = ('transaction_type', 'product')
    search_fields = ('product__code', 'note')
    list_per_page = 20


class PaymentAdmin(ImportExportModelAdmin):
    model = PaymentType
    list_display = ('id', 'name')
    list_per_page = 20


# Register your models and admin classes
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Sale, SaleAdmin)
admin.site.register(SaleItem, SaleItemAdmin)
admin.site.register(StockTransaction, StockTransactionAdmin)
admin.site.register(PaymentType, PaymentAdmin)
