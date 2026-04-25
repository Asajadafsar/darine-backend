from django.db import models
from django.conf import settings
from decimal import Decimal

class GoldInventory(models.Model):
    """موجودی طلای کاربر به گرم"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gold_inventory')
    balance = models.DecimalField(max_digits=20, decimal_places=5, default=0.00000)

    def __str__(self):
        return f"{self.user.mobile} - {self.balance}g"

class GoldTransaction(models.Model):
    """تاریخچه خرید و فروش طلا"""
    TRANSACTION_TYPES = (
        ('BUY', 'خرید'),
        ('SELL', 'فروش'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    amount_gr = models.DecimalField(max_digits=20, decimal_places=5) # وزن به گرم
    price_per_gram = models.DecimalField(max_digits=20, decimal_places=0) # قیمت لحظه‌ای
    fee = models.DecimalField(max_digits=20, decimal_places=0) # مبلغ کارمزد
    total_amount = models.DecimalField(max_digits=20, decimal_places=0) # مبلغ کل (تومان)
    is_completed = models.BooleanField(default=False) # وضعیت پرداخت
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.mobile} - {self.type} - {self.amount_gr}g"
    

class Wallet(models.Model):
    """کیف پول ریالی کاربر"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=20, decimal_places=0, default=0) # موجودی به تومان

    def __str__(self):
        return f"{self.user.mobile} - {self.balance} Toman"