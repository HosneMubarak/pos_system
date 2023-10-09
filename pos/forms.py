from django import forms

from .models import *


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'status']


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['code', 'category', 'name', 'description', 'buy_price', 'sell_price', 'status']


class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['grand_total', 'tendered_amount', 'amount_change']


class SaleItemForm(forms.ModelForm):
    class Meta:
        model = SaleItem
        fields = ['sale', 'product', 'price', 'qty', 'total']


class StockTransactionForm(forms.ModelForm):
    class Meta:
        model = StockTransaction
        fields = ['product', 'transaction_type', 'quantity', 'note']
