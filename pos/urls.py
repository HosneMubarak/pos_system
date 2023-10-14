from django.urls import path

from . import views

app_name = 'pos'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('categories/', views.category_list_view, name='category-list'),
    path('category/add/', views.category_add_view, name='category-add'),
    path('category/edit/<int:category_id>/', views.category_edit_view, name='category-edit'),
    path('category/delete/<int:category_id>/', views.category_delete_view, name='category-delete'),
    # Payment Type URLs
    path('payment_types/', views.payment_type_list_view, name='payment_type-list'),
    path('payment_type/add/', views.payment_type_add_view, name='payment_type-add'),
    path('payment_type/edit/<int:payment_type_id>/', views.payment_type_edit_view, name='payment_type-edit'),

    path('products/', views.product_list_view, name='product-list'),
    path('product/add/', views.product_add_view, name='product-add'),
    path('product/edit/<int:product_id>/', views.product_edit_view, name='product-edit'),
    path('product/delete/<int:product_id>/', views.product_delete_view, name='product-delete'),
    path('stocks/', views.stock_list_view, name='stock-list'),
    path('stock/add/', views.stock_add_view, name='stock-add'),
    path('stock/edit/<int:stock_id>/', views.stock_edit_view, name='stock-edit'),
    path('stock/<int:stock_id>/', views.stock_detail_view, name='stock-detail'),
    path('sale-item/', views.sale_item_list_view, name='sale-item-list'),
    path('sale-item/delete/<int:sale_item_id>/', views.sale_item_delete_view, name='sale-item-delete'),
    path('make-sale/', views.make_sale_view, name='make-sale'),
    path('save-sale/', views.save_sale_view, name='save_sale'),
    path('sale-list/', views.sale_list_view, name='sale-list'),
    path('sale/delete/<int:sale_id>/', views.sale_delete_view, name='sale-delete'),
    path('sale/<int:sale_id>/', views.sale_detail_view, name='sale-detail'),
    path('receipt/<int:sale_id>/', views.sale_receipt_view, name='sale-receipt'),

    # ... other url patterns ...

]
