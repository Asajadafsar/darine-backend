from django.db import models
from django.conf import settings
from decimal import Decimal
import uuid

from accounts.models import User



# --- بخش ۱: مدیریت دارایی و کیف پول ---

class GoldInventory(models.Model):
    """موجودی طلای کاربر به گرم"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gold_inventory')
    balance = models.DecimalField(max_digits=20, decimal_places=5, default=Decimal('0.00000'))

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

# --- بخش ۲: تراکنش‌های مالی و بانکی ---

class AdminBankInfo(models.Model):
    """اطلاعات حساب مدیریت برای کارت به کارت"""
    card_number = models.CharField(max_length=16, verbose_name="شماره کارت")
    account_number = models.CharField(max_length=20, verbose_name="شماره حساب")
    shaba_number = models.CharField(max_length=26, verbose_name="شماره شبا")
    owner_name = models.CharField(max_length=100, verbose_name="بنام")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "اطلاعات حساب مدیریت"
        verbose_name_plural = "اطلاعات حساب مدیریت"

    def __str__(self):
        return f"{self.owner_name} - {self.card_number}"

    @staticmethod
    def get_active_info():
        info = AdminBankInfo.objects.filter(is_active=True).first()
        if info:
            return {
                "card_number": info.card_number,
                "shaba": info.shaba_number,
                "owner": info.owner_name,
                "account": info.account_number
            }
        return {
            "card_number": "0000000000000000",
            "shaba": "IR000000000000000000000000",
            "owner": "مدیریت سیستم",
            "account": "00000000"
        }

class FinancialTransaction(models.Model):
    """تراکنش‌های واریز و برداشت ریالی"""
    TYPE_CHOICES = (
        ('DEPOSIT', 'واریز'), 
        ('WITHDRAW', 'برداشت')
    )
    METHOD_CHOICES = (
        ('GATEWAY', 'درگاه بانکی'), 
        ('CARD', 'کارت به کارت')
    )
    STATUS_CHOICES = (
        ('PENDING', 'در انتظار بررسی'), 
        ('SUCCESS', 'موفق'), 
        ('REJECTED', 'رد شده')
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='financial_transactions')
    amount = models.DecimalField(max_digits=20, decimal_places=0, verbose_name="مبلغ (تومان)")
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name="نوع تراکنش")
    method = models.CharField(max_length=10, choices=METHOD_CHOICES, verbose_name="روش پرداخت")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING', verbose_name="وضعیت")
    receipt_image = models.ImageField(upload_to='receipts/%Y/%m/', null=True, blank=True, verbose_name="تصویر رسید")
    user_card = models.ForeignKey('accounts.BankCard', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="کارت مقصد کاربر")
    admin_note = models.TextField(null=True, blank=True, verbose_name="توضیحات مدیریت")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین تغییر")

    class Meta:
        verbose_name = "تراکنش مالی"
        verbose_name_plural = "تراکنش‌های مالی"
        ordering = ['-created_at']

# --- بخش ۳: محصولات و تحویل فیزیکی ---

class Product(models.Model):
    CATEGORY_CHOICES = (
        ('18_KARAT', '۱۸ عیار'),
        ('24_KARAT', '۲۴ عیار'),
        ('PARSIAN', 'پارسیان'),
    )
    name = models.CharField(max_length=255, verbose_name="نام محصول")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    weight = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="وزن خالص (گرم)")
    total_weight_with_fees = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="وزن نهایی با اجرت")
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.weight}g)"

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.user.mobile} - {self.product.name}"

class Order(models.Model):
    PAYMENT_METHODS = (('GOLD', 'پرداخت با طلا'), ('TOMAN', 'پرداخت نقدی'))
    STATUS_CHOICES = (('PENDING', 'ثبت درخواست'), ('DELIVERED', 'تحویل شده'), ('CANCELLED', 'لغو شده'))

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.TextField(verbose_name="آدرس تحویل")
    city = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS)
    total_gold_amount = models.DecimalField(max_digits=15, decimal_places=3)
    total_toman_amount = models.DecimalField(max_digits=20, decimal_places=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.mobile}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price_at_time = models.DecimalField(max_digits=20, decimal_places=0)
    weight_at_time = models.DecimalField(max_digits=10, decimal_places=3)




class GiftCard(models.Model):
    # این مدل برای کارت‌هایی است که صادر شده و باید توسط کاربر فعال شوند
    serial_number = models.CharField(max_length=20, unique=True, verbose_name="شماره سریال")
    weight = models.DecimalField(max_digits=10, decimal_places=3, verbose_name="وزن طلا (گرم)")
    is_used = models.BooleanField(default=False, verbose_name="استفاده شده؟")
    created_at = models.DateTimeField(auto_now_add=True)
    activated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='activated_cards')

    def __str__(self):
        return f"کارت {self.weight} گرمی - {self.serial_number}"

class GiftCardOrder(models.Model):
    # این مدل برای سفارش خرید کارت هدیه است
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    weight_per_card = models.DecimalField(max_digits=10, decimal_places=3)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=20, decimal_places=0)
    
    # اطلاعات ارسال
    province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.TextField()
    postal_code = models.CharField(max_length=10)
    unit = models.CharField(max_length=10, null=True, blank=True)
    plaque = models.CharField(max_length=10, null=True, blank=True)
    
    status = models.CharField(max_length=20, default='PENDING') # PENDING, SHIPPED, DELIVERED
    created_at = models.DateTimeField(auto_now_add=True)




class PriceAlert(models.Model):
    ALERT_TYPES = (
        ('ONCE', 'فقط یکبار اطلاع بده'),
        ('ALWAYS', 'هربار اطلاع بده'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='price_alerts')
    target_price = models.DecimalField(max_digits=20, decimal_places=0, verbose_name="قیمت هدف (تومان)")
    alert_type = models.CharField(max_length=10, choices=ALERT_TYPES, default='ONCE')
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.mobile} - Target: {self.target_price}"
    

class ReferralEarning(models.Model):
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referral_earnings', verbose_name="معرف")
    referred_user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="کاربر دعوت شده")
    amount = models.DecimalField(max_digits=20, decimal_places=0, verbose_name="مبلغ سود (تومان)")
    transaction_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "سود معرفی"
        verbose_name_plural = "سودهای معرفی"