from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.db.models import Sum
from decimal import Decimal, InvalidOperation
from .models import SilverInventory, SilverTransaction, BankCard
from .utils import get_live_silver_price
from gold_app.models import Wallet, FinancialTransaction, ReferralEarning, AdminBankInfo




# --- کلاس خرید ---
class BuySilver(APIView):
    permission_classes = [IsAuthenticated]
    @transaction.atomic
    def post(self, request):
        user = request.user
        price = get_live_silver_price()
        toman = request.data.get('toman')
        weight = request.data.get('weight')
        
        # محاسبه هوشمند
        if toman:
            total_toman = Decimal(str(toman))
            fee = total_toman * Decimal('0.01')
            weight = (total_toman - fee) / price
        elif weight:
            weight = Decimal(str(weight))
            fee = (weight * price) * Decimal('0.01')
            total_toman = (weight * price) + fee
        else:
            return Response({"error": "مبلغ یا وزن وارد کنید"}, status=400)

        wallet = Wallet.objects.get(user=user)
        if wallet.balance < total_toman:
            return Response({"error": "موجودی کافی نیست"}, status=400)

        wallet.balance -= total_toman
        wallet.save()
        inv, _ = SilverInventory.objects.get_or_create(user=user)
        inv.balance += weight
        inv.total_spent_toman += total_toman
        inv.save()
        
        SilverTransaction.objects.create(user=user, type='BUY', amount_gr=weight, amount_toman=total_toman, status='DONE')
        return Response({"message": "خرید موفق", "weight": round(weight, 5)})




# --- کلاس فروش ---
class SellSilver(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        price = get_live_silver_price()
        
        if not price:
            return Response({"error": "خطا در دریافت قیمت لحظه‌ای"}, status=500)

        toman_input = request.data.get('toman')
        weight_input = request.data.get('weight')
        
        inventory, _ = SilverInventory.objects.get_or_create(user=user)

        # ۱. منطق محاسباتی هوشمند
        try:
            if toman_input:
                # کاربر می‌گوید: ۱۰۰ هزار تومان نقره بفروش
                total_toman_to_receive = Decimal(str(toman_input))
                # برای اینکه کاربر خالص ۱۰۰ ت بگیرد، باید معادل (۱۰۰ ت + کارمزد) نقره کسر شود
                # یا ساده‌تر: ۱۰۰ تومانی که می‌فروشد، قبل از کسر کارمزد چقدر بوده؟
                # Gross_Amount - (Gross_Amount * 0.01) = Net_Toman
                raw_toman_value = total_toman_to_receive / Decimal('0.99')
                weight_to_deduct = raw_toman_value / price
                fee = raw_toman_value * Decimal('0.01')
                final_payout = total_toman_to_receive
            elif weight_input:
                # کاربر می‌گوید: ۰.۵ گرم نقره بفروش
                weight_to_deduct = Decimal(str(weight_input))
                raw_toman_value = weight_to_deduct * price
                fee = raw_toman_value * Decimal('0.01')
                final_payout = raw_toman_value - fee
            else:
                return Response({"error": "لطفاً مبلغ یا وزن برای فروش را وارد کنید"}, status=400)
        except (InvalidOperation, ValueError):
            return Response({"error": "مقادیر وارد شده معتبر نیستند"}, status=400)

        # ۲. بررسی موجودی نقره کاربر
        if inventory.balance < weight_to_deduct:
            return Response({
                "error": "موجودی نقره کافی نیست",
                "required_gr": round(weight_to_deduct, 5),
                "your_balance": round(inventory.balance, 5)
            }, status=400)

        # ۳. کسر نقره و واریز تومان به کیف پول
        inventory.balance -= weight_to_deduct
        inventory.save()

        wallet, _ = Wallet.objects.get_or_create(user=user)
        wallet.balance += final_payout
        wallet.save()

        # ۴. ثبت تراکنش
        SilverTransaction.objects.create(
            user=user,
            type='SELL',
            amount_gr=weight_to_deduct,
            amount_toman=final_payout,
            status='DONE'
        )

        return Response({
            "message": "فروش با موفقیت انجام شد",
            "details": {
                "deducted_weight_gr": round(weight_to_deduct, 5),
                "payout_toman": round(final_payout),
                "fee_toman": round(fee),
                "new_silver_balance": round(inventory.balance, 5),
                "new_wallet_balance": round(wallet.balance)
            }
        }, status=status.HTTP_200_OK)





# --- داشبورد (تحلیلی) ---
class SilverDashboardAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        price = get_live_silver_price()
        inv, _ = SilverInventory.objects.get_or_create(user=request.user)
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        return Response({
            "assets": {"total": round((inv.balance * price) + wallet.balance), "silver": round(inv.balance, 5), "toman": round(wallet.balance)},
            "price_info": {"current": price, "change": 9.56, "highest": 493000, "lowest": 391920}
        })





# --- کیف پول (عملیاتی) ---
class SilverWalletAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        price = get_live_silver_price()
        inv, _ = SilverInventory.objects.get_or_create(user=request.user)
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        return Response({
            "wallet_header": {"total": round((inv.balance * price) + wallet.balance), "silver": round(inv.balance, 5), "toman": round(wallet.balance)},
            "summary": {"profit": round((inv.balance * price) - inv.total_spent_toman), "pending_toman": 0, "pending_silver": 0}
        })




# --- دیپوزیت و کارت ---
class SilverDeposit(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        FinancialTransaction.objects.create(user=request.user, amount=request.data['amount'], type='DEPOSIT', status='PENDING')
        return Response({"message": "در انتظار تایید"})




class BankCardAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response([{"id": c.id, "bank": c.bank_name, "card": c.card_number} for c in BankCard.objects.filter(user=request.user)])
    def post(self, request):
        BankCard.objects.create(user=request.user, bank_name=request.data['bank_name'], card_number=request.data['card_number'])
        return Response({"message": "ثبت شد"})