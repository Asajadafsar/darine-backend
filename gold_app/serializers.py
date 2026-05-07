from rest_framework import serializers
from .models import GoldTransaction, PriceAlert, Product, Cart, Order, OrderItem, FinancialTransaction
from rest_framework import serializers
# اضافه کردن مدل‌های جدید به لیست ایمپورت‌ها:
from .models import (
    Product, Cart, Order, OrderItem, FinancialTransaction, 
    GiftCard, GiftCardOrder  
)





# سریالایزر محصولات (برای نمایش لیست کالاها)
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

# سریالایزر سبد خرید
class CartSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'product', 'product_details', 'quantity']

# سریالایزر جزئیات اقلام سفارش
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product_name', 'quantity', 'price_at_time', 'weight_at_time']

# سریالایزر نهایی سفارشات
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'status', 'status_display', 'address', 'city', 
            'payment_method', 'payment_method_display', 
            'total_gold_amount', 'total_toman_amount', 
            'created_at', 'items'
        ]

# سریالایزر تراکنش‌های مالی (که قبلاً استفاده می‌کردیم)
class FinancialTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialTransaction
        fields = '__all__'



class GiftCardOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiftCardOrder
        fields = '__all__'
        read_only_fields = ['user', 'total_price', 'status']

class GiftCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = GiftCard
        fields = ['serial_number', 'weight', 'is_used', 'created_at']



# سریالایزر گزارش معاملات طلا
class GoldTransactionReportSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    class Meta:
        model = GoldTransaction
        fields = ['id', 'type', 'type_display', 'amount_gr', 'price_per_gram', 'total_amount', 'created_at', 'is_completed']

# سریالایزر گزارش واریز و برداشت ریالی
class FinancialReportSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    class Meta:
        model = FinancialTransaction
        fields = ['id', 'amount', 'type', 'type_display', 'status', 'status_display', 'method', 'created_at']


class PriceAlertSerializer(serializers.ModelSerializer):
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    
    class Meta:
        model = PriceAlert
        fields = ['id', 'target_price', 'alert_type', 'alert_type_display', 'is_active', 'created_at']
        read_only_fields = ['is_active']


