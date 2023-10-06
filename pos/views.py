from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from django.shortcuts import render, get_object_or_404, redirect

from .forms import CategoryForm
from .models import *


@login_required
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
        date__date__range=(start_date, end_date)
    ).order_by('-date')[:5]  # last 5 transactions, with related Product data

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
def category_list_view(request):
    # Get all categories
    categories = Category.objects.all()

    # Number of categories to display per page
    per_page = 10  # Adjust the number as needed

    # Create a Paginator object
    paginator = Paginator(categories, per_page)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the Page object for the current page
    page = paginator.get_page(page_number)

    return render(request, 'pos/category_list.html', {'page': page})


@login_required
def category_add_view(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category_list')  # Redirect to the category list view after adding
    else:
        form = CategoryForm()

    return render(request, 'pos/category_add.html', {'form': form})


@login_required
def category_edit_view(request, category_id):
    category = get_object_or_404(Category, pk=category_id)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category_list')  # Redirect to the category list view after editing
    else:
        form = CategoryForm(instance=category)

    return render(request, 'pos/category_edit.html', {'form': form, 'category': category})


@login_required
def product_list_view(request):
    products = Product.objects.all()

    # Number of categories to display per page
    per_page = 10  # Adjust the number as needed

    # Create a Paginator object
    paginator = Paginator(products, per_page)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the Page object for the current page
    page = paginator.get_page(page_number)

    return render(request, 'pos/product_list.html', {'page': page})


@login_required
def user_list_view(request):
    User = get_user_model()
    users = User.objects.all()

    # Number of categories to display per page
    per_page = 10  # Adjust the number as needed

    # Create a Paginator object
    paginator = Paginator(users, per_page)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the Page object for the current page
    page = paginator.get_page(page_number)
    return render(request, 'pos/user_list.html', {'page': page})


@login_required
def stock_list_view(request):
    stocks = StockTransaction.objects.all()

    # Number of categories to display per page
    per_page = 10  # Adjust the number as needed

    # Create a Paginator object
    paginator = Paginator(stocks, per_page)

    # Get the current page number from the request's GET parameters
    page_number = request.GET.get('page')

    # Get the Page object for the current page
    page = paginator.get_page(page_number)
    return render(request, 'pos/stock_list.html', {'page': page})
