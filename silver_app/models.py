from django.db import models
from django.conf import settings
from decimal import Decimal

class SilverInventory(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='silver_inventory')
    balance = models.DecimalField(max_digits=20, decimal_places=5, default=Decimal('0.00000'))
    total_spent_toman = models.DecimalField(max_digits=20, decimal_places=0, default=0) 
    total_withdrawn_gr = models.DecimalField(max_digits=20, decimal_places=5, default=0)

    def __str__(self):
        return f"{self.user.mobile} - {self.balance}g"

class SilverTransaction(models.Model):
    TYPE_CHOICES = (
        ('BUY', 'خرید نقره'),
        ('SELL', 'فروش نقره'),
        ('CONVERT', 'تبدیل از ریال'),
    )
    STATUS_CHOICES = (
        ('DONE', 'انجام شده'),
        ('PENDING', 'در انتظار'),
        ('FAILED', 'ناموفق'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount_gr = models.DecimalField(max_digits=20, decimal_places=5, default=0)
    amount_toman = models.DecimalField(max_digits=20, decimal_places=0) # مبلغ کل تراکنش به تومان
    type = models.CharField(max_length=15, choices=TYPE_CHOICES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='DONE')
    created_at = models.DateTimeField(auto_now_add=True)

class BankCard(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='silver_cards')
    bank_name = models.CharField(max_length=50)
    card_number = models.CharField(max_length=16)
    iban = models.CharField(max_length=26, blank=True, null=True)

    def __str__(self):
        return f"{self.user.mobile} - {self.bank_name}"