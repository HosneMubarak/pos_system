import json
from datetime import timedelta
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from account.decorators import staff_user_required
from .forms import *
from .models import *

import csv
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum
from django.core.paginator import Paginator
from datetime import datetime
from .models import Sale  # Adjust this import based on your actual model location
from django.utils import timezone


@login_required
@staff_user_required
def dashboard_view(request):
    current_date = datetime.now().date()
    selected_interval = request.GET.get('time_interval')

    # By default, set the interval's ending point to today's date
    interval_end = current_date

    if selected_interval == 'weekly':
        interval_start = current_date - timedelta(days=6)
    elif selected_interval == 'monthly':
        interval_start = current_date - timedelta(days=29)
    elif selected_interval == 'yearly':
        interval_start = current_date - timedelta(days=364)
    else:
        # Default to today's date if no or invalid parameter is provided
        interval_start = current_date

    # Sales count and amount in the selected interval
    sales_count_in_interval = Sale.objects.filter(
        date_added__date__range=(interval_start, interval_end)
    ).count()
    sales_amount_in_interval = Sale.objects.filter(
        date_added__date__range=(interval_start, interval_end)
    ).aggregate(total_sales=Sum('grand_total'))['total_sales'] or 0

    # Recent stock transactions in the selected interval
    recent_stock_transactions = StockTransaction.objects.select_related('product').filter(
        date_added__date__range=(interval_start, interval_end)
    ).order_by('-date_added')[:5]

    # Similar to sale_report_view, aggregate payment counts by payment type for sales in the interval
    payment_counts = Sale.objects.filter(
        date_added__date__range=(interval_start, interval_end)
    ).values('payment_type__name').annotate(count=Count('payment_type'))

    category_count = Category.objects.count()
    product_count = Product.objects.count()
    user_count = get_user_model().objects.count()

    aggregated_stock = Product.objects.aggregate(sum=Sum('stock'))['sum'] or 0

    recent_stock_transactions = StockTransaction.objects.select_related('product').order_by('-date_added')[:5]
    top_sellers = SaleItem.objects.values('product__id', 'product__name').annotate(total_qty=Sum('qty')).order_by('-total_qty')[:10]
    for rank, seller in enumerate(top_sellers, start=1):
        seller['rank'] = rank

    context = {
        'total_categories': category_count,
        'total_products': product_count,
        'total_stock': aggregated_stock,
        'total_users': user_count,
        'sales_count_for_interval': sales_count_in_interval,
        'sales_amount_for_interval': sales_amount_in_interval,
        'recent_transactions': recent_stock_transactions,
        'time_interval': selected_interval or 'today',
        'top_sellers': top_sellers
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
    # Ensure only admin can add categories
    if not request.user.is_admin:
        messages.error(request, "You don't have the permission to add categories.")
        return redirect('pos:dashboard')  # Redirect back to the category list view if not admin

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
    # Ensure only admin can edit categories
    if not request.user.is_admin:
        messages.error(request, "You don't have the permission to edit this category.")
        return redirect('pos:dashboard')  # Redirect back to the category list view if not admin

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
        return redirect('pos:dashboard')  # Redirect back to the category list view

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
    # Ensure only admin can edit
    if not request.user.is_admin:
        messages.error(request, "You don't have the permission to edit this product.")
        return redirect('pos:dashboard')  # Redirect back to the product list view if not admin
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
    # Ensure only admin can edit
    if not request.user.is_admin:
        messages.error(request, "You don't have the permission to edit this product.")
        return redirect('pos:dashboard')  # Redirect back to the product list view if not admin

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
        return redirect('pos:dashboard')  # Redirect back to the product list view

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
    if not request.user.is_admin:
        messages.error(request, "You don't have the permission to add stock transactions.")
        return redirect('pos:dashboard')
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
    if not request.user.is_admin:
        messages.error(request, "You don't have the permission to edit this stock transaction.")
        return redirect('pos:dashboard')
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

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        sale_items = sale_items.filter(
            Q(product__code__icontains=search_query) |
            Q(product__name__icontains=search_query) |
            Q(sale__code__icontains=search_query)
        )

    # Number of sale items to display per page
    per_page = 10

    # Create a Paginator object
    paginator = Paginator(sale_items, per_page)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the Page object for the current page
    page = paginator.get_page(page_number)

    return render(request, 'pos/sale_item_list.html', {'page': page, 'search_query': search_query})


@login_required
@staff_user_required
def sale_item_delete_view(request, sale_item_id):
    # Ensure only admin can delete
    if not request.user.is_admin:
        messages.error(request, "You don't have the permission to delete this sale item.")
        return redirect('pos:dashboard')

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
    pament_types = PaymentType.objects.all()
    return render(request, 'pos/make_sale.html', {'products': products, 'payment_types': pament_types})


@login_required
@staff_user_required
def save_sale_view(request):
    if request.method != "POST":
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed.'}, status=405)

    try:
        # Check if the request's body contains valid JSON data
        if not request.body:
            return JsonResponse({'status': 'error', 'message': 'No JSON data in the request.'}, status=400)

        # Get the JSON data from the request's body
        data = json.loads(request.body)
        product_data = data.get('product_data')

        # Check if product_data is empty
        if not product_data:
            return JsonResponse({'status': 'error', 'message': 'No products selected for the sale.'}, status=400)

        # Typecasting amounts into decimals
        grand_total = Decimal(data.get('grand_total'))
        tendered_amount = Decimal(data.get('tendered_amount'))
        amount_change = Decimal(data.get('amount_change'))

        # Fetch the selected payment type
        payment_type_id = data.get('payment_type')
        selected_payment_type = PaymentType.objects.get(id=payment_type_id)

        # Save the Sale instance with the payment type
        sale = Sale(
            grand_total=grand_total,
            sub_total=grand_total,
            tendered_amount=tendered_amount,
            amount_change=amount_change,
            payment_type=selected_payment_type,
            created_by=request.user,
            updated_by=request.user
        )
        sale.save()

        for product in product_data:
            product_id = product['product_id']
            quantity = int(product['quantity'])
            related_product = Product.objects.get(id=product_id)  # fetch the related product

            # Create the SaleItem instance
            sale_item = SaleItem(
                sale=sale,
                product=related_product,
                price=related_product.sell_price,  # Set the sell_price from related product
                qty=quantity,
                created_by=request.user,
                updated_by=request.user
            )
            sale_item.save()

        messages.success(request, 'Invoice created successfully')
        return JsonResponse({'status': 'success', 'sale_id': sale.id, 'message': 'Invoice created successfully!'})

    except Exception as e:
        print(e)
        return JsonResponse({'status': 'error', 'message': f'There was an error processing your request: {str(e)}'},
                            status=500)


@login_required
@staff_user_required
def sale_list_view(request):
    sales = Sale.objects.all().select_related('created_by', 'updated_by')

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        sales = sales.filter(
            Q(code__icontains=search_query)
        )

    # Number of sales to display per page
    per_page = 10

    # Create a Paginator object
    paginator = Paginator(sales, per_page)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the Page object for the current page
    page = paginator.get_page(page_number)

    return render(request, 'pos/sale_list.html', {'page': page, 'search_query': search_query})


@login_required
@staff_user_required
def sale_delete_view(request, sale_id):
    # Ensure only admin can delete
    if not request.user.is_admin:
        messages.error(request, "You don't have the permission to delete this sale.")
        return redirect('pos:dashboard')

    sale = get_object_or_404(Sale, pk=sale_id)

    if request.method == 'POST':
        sale.delete()
        messages.success(request, 'Sale successfully deleted.')
        return redirect('pos:sale-list')  # Redirect to the sale list view after deletion

    # If the method is not POST, redirect to the list view.
    return redirect('pos:sale-list')


@login_required
@staff_user_required
def sale_detail_view(request, sale_id):
    # Ensure only admin/staff can view sale details
    if not request.user.is_staff:
        messages.error(request, "You don't have the permission to view this sale.")
        return redirect('pos:dashboard')

    sale = get_object_or_404(Sale, pk=sale_id)

    # Corrected related data fetching for sales items for this sale
    sales_items = sale.saleitem_set.all()

    context = {
        'sale': sale,
        'sales_items': sales_items,
    }

    return render(request, 'pos/sale_detail.html', context)


@login_required
@staff_user_required
def sale_receipt_view(request, sale_id):
    # Ensure only admin/staff can view sale details
    if not request.user.is_staff:
        messages.error(request, "You don't have the permission to view this sale.")
        return redirect('pos:dashboard')

    sale = get_object_or_404(Sale, pk=sale_id)

    # Corrected related data fetching for sales items for this sale
    sales_items = sale.saleitem_set.all()

    context = {
        'sale': sale,
        'sales_items': sales_items,
    }

    return render(request, 'pos/pos_receipt.html', context)


@login_required
@staff_user_required
def payment_type_list_view(request):
    # Get all payment types
    payment_types = PaymentType.objects.all()

    # Sorting
    sort_by = request.GET.get('sort_by', 'name')  # Default sorting by name
    if sort_by not in ['name', 'description']:
        sort_by = 'name'  # Default to name if invalid sort criteria
    payment_types = payment_types.order_by(sort_by)

    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        payment_types = payment_types.filter(Q(name__icontains=search_query) |
                                             Q(description__icontains=search_query))

    # Number of payment types to display per page
    per_page = 10  # Adjust the number as needed

    # Create a Paginator object
    paginator = Paginator(payment_types, per_page)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the Page object for the current page
    page = paginator.get_page(page_number)

    return render(request, 'pos/payment_type_list.html',
                  {'page': page, 'sort_by': sort_by, 'search_query': search_query})


@login_required
@staff_user_required
def payment_type_add_view(request):
    # Ensure only admin can add payment types
    if not request.user.is_staff:
        messages.error(request, "You don't have the permission to add payment types.")
        return redirect('pos:dashboard')

    if request.method == 'POST':
        form = PaymentTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment type successfully added.')
            return redirect('pos:payment_type-list')
        else:
            messages.error(request, 'There was an error adding the payment type.')

    else:
        form = PaymentTypeForm()

    return render(request, 'pos/payment_type_add.html', {'form': form})


@login_required
@staff_user_required
def payment_type_edit_view(request, payment_type_id):
    # Ensure only admin can edit payment types
    if not request.user.is_staff:
        messages.error(request, "You don't have the permission to edit this payment type.")
        return redirect('pos:dashboard')

    payment_type = get_object_or_404(PaymentType, pk=payment_type_id)

    if request.method == 'POST':
        form = PaymentTypeForm(request.POST, instance=payment_type)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment type successfully updated.')
            return redirect('pos:payment_type-list')
        else:
            messages.error(request, 'There was an error updating the payment type.')
    else:
        form = PaymentTypeForm(instance=payment_type)

    return render(request, 'pos/payment_type_edit.html', {'form': form, 'payment_type': payment_type})


@login_required
@staff_user_required
def sale_report_view(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have the permission to view this page.")
        return redirect('pos:dashboard')

    sales = Sale.objects.all().select_related('created_by', 'updated_by')

    # Date range filter
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    try:
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            sales = sales.filter(date_added__date__gte=start_date.date())

        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            sales = sales.filter(date_added__date__lte=end_date.date())

        # Check if the end date is greater than or equal to the start date
        if start_date and end_date and end_date < start_date:
            messages.error(request, "End date should be greater than or equal to start date.")
            return redirect('pos:sale_report')

    except ValueError:
        messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
        return redirect('pos:sale_report')

    # Aggregate total sale price and count
    total_sale_price = sales.aggregate(Sum('grand_total'))['grand_total__sum']
    total_sale_count = sales.count()

    # Aggregate payment counts by payment type
    payment_counts = sales.values('payment_type__name').annotate(count=Count('payment_type'))

    # Number of sales to display per page
    per_page = 10

    # Create a Paginator object
    paginator = Paginator(sales, per_page)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the Page object for the current page
    page = paginator.get_page(page_number)

    # Customize pagination information
    pagination_info = {
        'total_items': paginator.count,
        'items_per_page': per_page,
        'total_pages': paginator.num_pages,
        'current_page': page.number,
    }

    # Pass date range parameters, total sale price, total sale count, and payment counts to the template
    date_range_params = {
        'start_date': start_date.strftime('%Y-%m-%d') if start_date else '',
        'end_date': end_date.strftime('%Y-%m-%d') if end_date else '',
    }

    # Check if a CSV export is requested
    export_csv = request.GET.get('export_csv')

    if export_csv:
        # Prepare the response for a CSV file
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sale_report.csv"'

        # Create a CSV writer
        csv_writer = csv.writer(response)

        # Write metadata
        csv_writer.writerow(['Date Range:', date_range_params['start_date'], 'to', date_range_params['end_date']])
        csv_writer.writerow(['Total Sale Count:', total_sale_count])
        csv_writer.writerow(['Total Sale Price:', total_sale_price])
        csv_writer.writerow([])  # Add an empty row for better readability

        # Write payment counts
        csv_writer.writerow(['Payment Type', 'Payment Count'])
        for payment_count in payment_counts:
            csv_writer.writerow([payment_count['payment_type__name'], payment_count['count']])
        csv_writer.writerow([])  # Add an empty row for better readability

        # Write the header row
        csv_writer.writerow(['Invoice ID', 'Date Added', 'Payment Type', 'Sub Total', 'Grand Total', 'Sell By'])

        # Write data rows
        for sale in sales:
            csv_writer.writerow([
                sale.code,
                timezone.localtime(sale.date_added, timezone=timezone.get_current_timezone()).strftime('%b. %d, %Y, '
                                                                                                       '%I:%M %p'),
                sale.payment_type.name,
                sale.sub_total,
                sale.grand_total,
                sale.created_by.username
            ])

        return response

    return render(request, 'pos/sale_report.html',
                  {'page': page, 'pagination_info': pagination_info,
                   'date_range_params': date_range_params,
                   'total_sale_price': total_sale_price,
                   'total_sale_count': total_sale_count,
                   'payment_counts': payment_counts})


