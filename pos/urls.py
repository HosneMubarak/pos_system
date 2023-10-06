from django.urls import path

from . import views

app_name = 'pos'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('categories/', views.category_list_view, name='category-list'),
    path('category/add/', views.category_add_view, name='category_add'),
    path('products/', views.product_list_view, name='product-list'),
    path('users/', views.user_list_view, name='user-list'),
    path('stocks/', views.stock_list_view, name='stock-list'),
    # ... other url patterns ...
]
