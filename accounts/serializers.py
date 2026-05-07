from rest_framework import serializers
from .models import BankCard, User, OTPRequest
from django.contrib.auth.hashers import make_password
from datetime import date

class SendOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)

class VerifyOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)
    code = serializers.CharField(max_length=6)

class CompleteRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    birth_year = serializers.IntegerField(write_only=True)
    birth_month = serializers.IntegerField(write_only=True)
    birth_day = serializers.IntegerField(write_only=True)
    
    # فیلد مجازی برای گرفتن کد معرف از کاربر جدید
    entered_referral_code = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'national_code', 
            'password', 'birth_year', 'birth_month', 
            'birth_day', 'entered_referral_code' # نام فیلد اصلاح شد
        ]

    def create(self, validated_data):
        # استخراج داده‌های تاریخ
        year = validated_data.pop('birth_year')
        month = validated_data.pop('birth_month')
        day = validated_data.pop('birth_day')
        
        # استخراج کد معرف ورودی
        ref_code = validated_data.pop('entered_referral_code', None)
        
        try:
            validated_data['birth_date'] = date(year, month, day)
        except ValueError:
            raise serializers.ValidationError({"birth_date": "تاریخ تولد وارد شده معتبر نیست"})

        password = validated_data.pop('password')
        
        # پیدا کردن معرف در صورت وجود
        referred_by = None
        if ref_code:
            referred_by = User.objects.filter(referral_code=ref_code).first()

        # ایجاد کاربر
        user = User(**validated_data)
        user.set_password(password)
        
        if referred_by:
            user.referred_by = referred_by
            
        user.save()
        return user

# این کلاسی بود که باعث ارور ImportError شده بود
class ResetPasswordOTPSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)

class ResetPasswordConfirmSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=11)
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)

class BankCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankCard
        fields = ['id', 'card_number', 'bank_name', 'is_active']
        read_only_fields = ['id']

class ChangeMobileRequestSerializer(serializers.Serializer):
    new_mobile = serializers.CharField(max_length=11)

class ChangeMobileConfirmSerializer(serializers.Serializer):
    new_mobile = serializers.CharField(max_length=11)
    code = serializers.CharField(max_length=6)