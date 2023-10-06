from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


class BaseUserTrackModel(models.Model):
    created_by = models.ForeignKey(get_user_model(), related_name="%(class)s_created_by", on_delete=models.CASCADE)
    updated_by = models.ForeignKey(get_user_model(), related_name="%(class)s_updated_by", on_delete=models.CASCADE)
    date_added = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(BaseUserTrackModel):
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    ACTIVE = 1
    INACTIVE = 0
    STATUS_CHOICES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
    ]
    status = models.IntegerField(choices=STATUS_CHOICES, default=ACTIVE)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-date_updated']


class Product(BaseUserTrackModel):
    code = models.CharField(max_length=20, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    stock = models.PositiveIntegerField(default=0)
    buy_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.IntegerField(choices=Category.STATUS_CHOICES, default=Category.ACTIVE)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['-date_updated']


class Sale(BaseUserTrackModel):
    code = models.CharField(max_length=20, unique=True)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage
    tendered_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_change = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.code

    class Meta:
        ordering = ['-date_updated']


class SaleItem(BaseUserTrackModel):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    qty = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-date_updated']
        verbose_name_plural = "Sale Items"

    def save(self, *args, **kwargs):
        # Calculate the total price for this sale item
        self.total = self.price * self.qty
        super(SaleItem, self).save(*args, **kwargs)

        # Update the stock level of the associated product
        if self.qty > 0:
            # Assuming positive quantity means it's a sale, reduce the stock
            self.product.stock -= self.qty
            self.product.save()


class StockTransaction(BaseUserTrackModel):
    TRANSACTION_IN = 'IN'
    TRANSACTION_OUT = 'OUT'
    TRANSACTION_RETURN = 'RETURN'
    TRANSACTION_CHOICES = [
        (TRANSACTION_IN, 'Stock In'),
        (TRANSACTION_OUT, 'Stock Out'),
        (TRANSACTION_RETURN, 'Return'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_CHOICES)
    quantity = models.PositiveIntegerField()
    note = models.TextField(null=True, blank=True)  # Optional note for any additional information

    class Meta:
        ordering = ['-date_updated']

    def save(self, *args, **kwargs):
        # Adjust the stock level in the Product model based on the transaction type.
        if self.transaction_type == self.TRANSACTION_IN:
            self.product.stock += self.quantity
        elif self.transaction_type == self.TRANSACTION_OUT:
            self.product.stock -= self.quantity
        elif self.transaction_type == self.TRANSACTION_RETURN:
            self.product.stock -= self.quantity  # Assuming returns add back to stock
        self.product.save()
        super(StockTransaction, self).save(*args, **kwargs)
