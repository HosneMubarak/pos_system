from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum, Q
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render

from account.decorators import staff_user_required
from .forms import *
from .models import *


@login_required
@staff_user_required
def dashboard_view(request):
    today = datetime.now().date()

    time_interval = request.GET.get('time_interval')

    if time_interval == 'weekly':
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    elif time_interval == 'monthly':
        start_date = today.replace(day=1)
        end_date = start_date.replace(day=1, month=start_date.month + 1) - timedelta(days=1)
    elif time_interval == 'yearly':
        start_date = today.replace(month=1, day=1)
        end_date = start_date.replace(year=start_date.year + 1) - timedelta(days=1)
    else:
        # Default to daily if no or invalid parameter is provided
        start_date = end_date = today

    total_categories = Category.objects.count()
    total_products = Product.objects.count()

    # Use get_user_model() to reference your custom user model
    total_users = get_user_model().objects.count()  # Get the total number of users based on your custom user model

    # Get the aggregated values directly in the context
    total_stock = Product.objects.aggregate(sum=models.Sum('stock'))['sum'] or 0
    todays_sales_count = Sale.objects.filter(
        date_added__date__range=(start_date, end_date)
    ).count()
    todays_sales_amount = Sale.objects.filter(
        date_added__date__range=(start_date, end_date)
    ).aggregate(total_sales=Sum('grand_total'))['total_sales'] or 0

    recent_transactions = StockTransaction.objects.select_related('product').filter(
        date_added__date__range=(start_date, end_date)
    ).order_by('-date_added')[:5]  # last 5 transactions, with related Product data

    context = {
        'total_categories': total_categories,
        'total_products': total_products,
        'total_stock': total_stock,
        'total_users': total_users,
        'todays_sales_count': todays_sales_count,
        'todays_sales_amount': todays_sales_amount,
        'recent_transactions': recent_transactions,
        'time_interval': time_interval or 'daily',
    }

    return render(request, 'pos/dashboard.html', context)


@login_required
@staff_user_required
def category_list_view(request):
    # Get all categories
    categories = Category.objects.all().select_related('created_by', 'updated_by')

    # Sorting
    sort_by = request.GET.get('sort_by', 'date_updated')  # Default sorting by date_updated
    if sort_by not in ['name', 'description', 'status', 'date_updated']:
        sort_by = '-date_updated'  # Default to date_updated if invalid sort criteria
    categories = categories.order_by(sort_by)

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        categories = categories.filter(Q(name__icontains=search_query) |
                                       Q(description__icontains=search_query) |
                                       Q(status__icontains=search_query))

    # Number of categories to display per page
    per_page = 10  # Adjust the number as needed

    # Create a Paginator object
    paginator = Paginator(categories, per_page)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the Page object for the current page
    page = paginator.get_page(page_number)

    return render(request, 'pos/category_list.html', {'page': page, 'sort_by': sort_by, 'search_query': search_query})


@login_required
@staff_user_required
def category_add_view(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.created_by = request.user
            category.updated_by = request.user
            category.save()
            messages.success(request, 'Category successfully added.')
            return redirect('pos:category-list')  # Redirect to the category list view after adding
        else:
            messages.error(request, 'There was an error adding the category.')
    else:
        form = CategoryForm()

    return render(request, 'pos/category_add.html', {'form': form})


@login_required
@staff_user_required
def category_edit_view(request, category_id):
    category = get_object_or_404(Category, pk=category_id)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save(commit=False)
            category.updated_by = request.user  # only updating 'updated_by' for edits
            category.save()
            messages.success(request, 'Category successfully updated.')
            return redirect('pos:category-list')  # Redirect to the category list view after editing
        else:
            messages.error(request, 'There was an error updating the category.')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'pos/category_edit.html', {'form': form, 'category': category})


@login_required
@staff_user_required
def category_delete_view(request, category_id):
    # Ensure only admin can delete
    if not request.user.is_admin:
        messages.error(request, "You don't have the permission to delete this category.")
        return redirect('pos:category-list')  # Redirect back to the category list view

    category = get_object_or_404(Category, pk=category_id)

    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category successfully deleted.')
        return redirect('pos:category-list')  # Redirect to the category list view after deletion

    # Since we removed the confirmation page, if the method is not POST, redirect to the list view.
    return redirect('pos:category-list')


@login_required
@staff_user_required
def product_list_view(request):
    # Get all products
    products = Product.objects.all().select_related('created_by', 'updated_by')

    # Sorting
    sort_by = request.GET.get('sort_by', 'date_updated')  # Default sorting by date_updated
    if sort_by not in ['code', 'category', 'name', 'description', 'stock', 'buy_price', 'sell_price', 'status',
                       'date_updated']:
        sort_by = '-date_updated'  # Default to date_updated if invalid sort criteria
    products = products.order_by(sort_by)

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(Q(code__icontains=search_query) |
                                   Q(category__name__icontains=search_query) |
                                   Q(name__icontains=search_query) |
                                   Q(description__icontains=search_query) |
                                   Q(stock__icontains=search_query) |
                                   Q(buy_price__icontains=search_query) |
                                   Q(sell_price__icontains=search_query) |
                                   Q(status__icontains=search_query))

    # Number of products to display per page
    per_page = 10  # Adjust the number as needed

    # Create a Paginator object
    paginator = Paginator(products, per_page)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the Page object for the current page
    page = paginator.get_page(page_number)

    return render(request, 'pos/product_list.html', {'page': page, 'sort_by': sort_by, 'search_query': search_query})


@login_required
@staff_user_required
def product_add_view(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user
            product.updated_by = request.user
            product.save()
            messages.success(request, 'Product successfully added.')
            return redirect('pos:product-list')  # Redirect to the product list view after adding
        else:
            messages.error(request, 'There was an error adding the product.')
    else:
        form = ProductForm()

    return render(request, 'pos/product_add.html', {'form': form, 'categories': categories})


@login_required
@staff_user_required
def product_edit_view(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    categories = Category.objects.all()
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            product.updated_by = request.user  # only updating 'updated_by' for edits
            product.save()
            messages.success(request, 'Product successfully updated.')
            return redirect('pos:product-list')  # Redirect to the product list view after editing
        else:
            messages.error(request, 'There was an error updating the product.')
    else:
        form = ProductForm(instance=product)

    return render(request, 'pos/product_edit.html', {'form': form, 'product': product, 'categories': categories})


@login_required
@staff_user_required
def product_delete_view(request, product_id):
    # Ensure only admin can delete
    if not request.user.is_admin:
        messages.error(request, "You don't have the permission to delete this product.")
        return redirect('pos:product-list')  # Redirect back to the product list view

    product = get_object_or_404(Product, pk=product_id)

    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product successfully deleted.')
        return redirect('pos:product-list')  # Redirect to the product list view after deletion

    # Since we removed the confirmation page, if the method is not POST, redirect to the list view.
    return redirect('pos:product-list')


@login_required
@staff_user_required
def stock_list_view(request):
    # Fetch related data for 'created_by', 'updated_by', and 'product' fields
    stocks = StockTransaction.objects.all().select_related('created_by', 'updated_by', 'product')

    # Sorting
    sort_by = request.GET.get('sort_by', 'date_updated')  # Default sorting by date_updated
    if sort_by not in ['product', 'transaction_type', 'quantity', 'note', 'date_updated']:
        sort_by = '-date_updated'  # Default to date_updated if invalid sort criteria
    stocks = stocks.order_by(sort_by)

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        stocks = stocks.filter(Q(product__code__icontains=search_query) |
                               Q(product__category__name__icontains=search_query) |
                               Q(product__name__icontains=search_query) |
                               Q(transaction_type__icontains=search_query) |
                               Q(quantity__icontains=search_query) |
                               Q(note__icontains=search_query))

    # Number of stock transactions to display per page
    per_page = 10  # Adjust the number as needed

    # Create a Paginator object
    paginator = Paginator(stocks, per_page)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the Page object for the current page
    page = paginator.get_page(page_number)

    return render(request, 'pos/stock_list.html', {'page': page, 'sort_by': sort_by, 'search_query': search_query})


@login_required
@staff_user_required
def stock_detail_view(request, stock_id):
    # Fetch the specific StockTransaction with related data
    stock = get_object_or_404(StockTransaction.objects.select_related('created_by', 'updated_by', 'product'),
                              pk=stock_id)

    context = {
        'stock': stock
    }

    return render(request, 'pos/stock_detail.html', context)


@login_required
@staff_user_required
def stock_add_view(request):
    products = Product.objects.all()

    if request.method == 'POST':
        form = StockTransactionForm(request.POST)
        if form.is_valid():
            stock = form.save(commit=False)
            stock.created_by = request.user
            stock.updated_by = request.user

            # Check if the transaction is valid based on the transaction type and quantity.
            if ((stock.transaction_type == StockTransaction.TRANSACTION_OUT or
                 stock.transaction_type == StockTransaction.TRANSACTION_RETURN) and
                    stock.quantity > stock.product.stock):
                messages.error(request,
                               f'Not enough stock available for this transaction. You have {stock.product.stock} in stock.')

            else:
                stock.save()
                messages.success(request, 'Stock transaction successfully added.')
                return redirect('pos:stock-list')  # Redirect to the stock transaction list view after adding
        else:
            messages.error(request, 'There was an error adding the stock transaction.')
    else:
        form = StockTransactionForm()

    return render(request, 'pos/stock_add.html', {'form': form, 'products': products})


@login_required
@staff_user_required
def stock_edit_view(request, stock_id):
    stock_transaction = get_object_or_404(StockTransaction, pk=stock_id)
    products = Product.objects.all()

    if request.method == 'POST':
        form = StockTransactionForm(request.POST, instance=stock_transaction)
        if form.is_valid():
            stock = form.save(commit=False)
            stock.updated_by = request.user  # only updating 'updated_by' for edits

            # Check if the transaction is valid based on the transaction type and quantity.
            if ((stock.transaction_type == StockTransaction.TRANSACTION_OUT or
                 stock.transaction_type == StockTransaction.TRANSACTION_RETURN) and
                    stock.quantity > stock.product.stock):
                messages.error(request,
                               f'Not enough stock available for this transaction. You have {stock.product.stock} in stock.')

            else:
                stock.save()
                messages.success(request, 'Stock transaction successfully updated.')
                return redirect('pos:stock-list')  # Redirect to the stock transaction list view after editing
        else:
            messages.error(request, 'There was an error updating the stock transaction.')
    else:
        form = StockTransactionForm(instance=stock_transaction)

    return render(request, 'pos/stock_edit.html',
                  {'form': form, 'stock_transaction': stock_transaction, 'products': products})


@login_required
@staff_user_required
def sale_item_list_view(request):
    sale_items = SaleItem.objects.all().select_related('created_by', 'updated_by', 'sale', 'product')

    # Number of sale items to display per page
    per_page = 10  # Adjust the number as needed

    # Create a Paginator object
    paginator = Paginator(sale_items, per_page)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the Page object for the current page
    page = paginator.get_page(page_number)
    return render(request, 'pos/sale_item_list.html', {'page': page})


@login_required
@staff_user_required
def sale_item_delete_view(request, sale_item_id):
    # Ensure only admin can delete
    if not request.user.is_admin:
        messages.error(request, "You don't have the permission to delete this sale item.")
        return redirect('pos:sale-item-list')  # Redirect back to the sale item list view

    sale_item = get_object_or_404(SaleItem, pk=sale_item_id)

    if request.method == 'POST':
        sale_item.delete()
        messages.success(request, 'Sale item successfully deleted.')
        return redirect('pos:sale-item-list')  # Redirect to the sale item list view after deletion

    # Since we removed the confirmation page, if the method is not POST, redirect to the list view.
    return redirect('pos:sale-item-list')


@login_required
@staff_user_required
def make_sale_view(request):
    # Get all products
    products = Product.objects.all()
    return render(request, 'pos/make_sale.html', {'products': products})
