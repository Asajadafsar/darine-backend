from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from .models import GoldInventory, GoldTransaction
from .utils import get_live_gold_price
from .models import GoldInventory, GoldTransaction, Wallet


class BuyGold(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        price_per_gram = get_live_gold_price()
        if not price_per_gram:
            return Response({"error": "خطا در دریافت قیمت لحظه‌ای طلا"}, status=500)

        # دریافت ورودی‌ها از فرانت‌ند
        toman_amount = request.data.get('toman')   # اگر کاربر مبلغ وارد کند
        weight_amount = request.data.get('weight') # اگر کاربر وزن (گرم) وارد کند

        fee_rate = Decimal('0.01') # کارمزد ۱ درصد

        # سناریو ۱: خرید بر اساس مبلغ (تومان)
        if toman_amount:
            total_toman = Decimal(str(toman_amount))
            # در این حالت، مبلغ پرداختی کاربر ثابت است (مثلاً ۱ میلیون)
            # کارمزد از این مبلغ کسر می‌شود و باقی‌مانده تبدیل به طلا می‌شود
            fee = total_toman * fee_rate
            net_amount = total_toman - fee
            weight = net_amount / price_per_gram

        # سناریو ۲: خرید بر اساس وزن (گرم)
        elif weight_amount:
            weight = Decimal(str(weight_amount))
            # در این حالت، وزن طلا ثابت است (مثلاً ۰.۵ گرم)
            # کارمزد به مبلغ طلا اضافه می‌شود و مبلغ نهایی پرداختی محاسبه می‌شود
            net_amount = weight * price_per_gram
            fee = net_amount * fee_rate
            total_toman = net_amount + fee
            
        else:
            return Response({"error": "لطفاً مبلغ یا وزن را برای خرید وارد کنید"}, status=400)

        # ثبت تراکنش در دیتابیس
        transaction = GoldTransaction.objects.create(
            user=request.user,
            type='BUY',
            amount_gr=weight,
            price_per_gram=price_per_gram,
            fee=fee,
            total_amount=total_toman,
            is_completed=True
        )

        # آپدیت موجودی کاربر
        inventory, _ = GoldInventory.objects.get_or_create(user=request.user)
        inventory.balance = Decimal(str(inventory.balance)) + Decimal(str(weight))
        inventory.save()

        return Response({
            "message": "خرید با موفقیت انجام شد",
            "details": {
                "weight_gr": round(weight, 5),
                "price_per_gram": price_per_gram,
                "fee_toman": round(fee),
                "total_paid_toman": round(total_toman)
            }
        }, status=status.HTTP_201_CREATED)
    

class GoldBalance(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # ۱. دریافت قیمت لحظه‌ای برای محاسبه ارزش روز
        price_per_gram = get_live_gold_price()
        if not price_per_gram:
            return Response({"error": "خطا در دریافت قیمت لحظه‌ای"}, status=500)

        # ۲. پیدا کردن موجودی کاربر (اگر رکورد نداشت، موجودی صفر برمی‌گردانیم)
        inventory, created = GoldInventory.objects.get_or_create(user=request.user)
        
        gold_balance = Decimal(str(inventory.balance))
        
        # ۳. محاسبه ارزش ریالی موجودی
        total_value_toman = gold_balance * price_per_gram

        return Response({
            "gold_balance_gr": round(gold_balance, 5), # موجودی به گرم
            "current_gold_price": price_per_gram,      # قیمت هر گرم (تومان)
            "total_value_toman": round(total_value_toman), # ارزش کل دارایی (تومان)
        }, status=status.HTTP_200_OK)
    


class SellGold(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        price_per_gram = get_live_gold_price()
        if not price_per_gram:
            return Response({"error": "خطا در دریافت قیمت لحظه‌ای طلا"}, status=500)

        toman_amount = request.data.get('toman')
        weight_amount = request.data.get('weight')
        fee_rate = Decimal('0.01') 

        inventory, _ = GoldInventory.objects.get_or_create(user=request.user)
        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        # محاسبه وزن و مبلغ پرداختی به کاربر
        if toman_amount:
            total_toman_request = Decimal(str(toman_amount))
            weight_to_sell = total_toman_request / price_per_gram
            fee = total_toman_request * fee_rate
            final_payout = total_toman_request - fee
        elif weight_amount:
            weight_to_sell = Decimal(str(weight_amount))
            raw_toman = weight_to_sell * price_per_gram
            fee = raw_toman * fee_rate
            final_payout = raw_toman - fee
        else:
            return Response({"error": "لطفاً مبلغ یا وزن را وارد کنید"}, status=400)

        # بررسی موجودی طلا
        if inventory.balance < weight_to_sell:
            return Response({"error": "موجودی طلای شما کافی نیست"}, status=400)

        # ثبت تراکنش
        GoldTransaction.objects.create(
            user=request.user,
            type='SELL',
            amount_gr=weight_to_sell,
            price_per_gram=price_per_gram,
            fee=fee,
            total_amount=final_payout,
            is_completed=True
        )

        # عملیات انتقال وجه و کسر طلا
        inventory.balance = Decimal(str(inventory.balance)) - Decimal(str(weight_to_sell))
        inventory.save()
        
        wallet.balance = Decimal(str(wallet.balance)) + Decimal(str(final_payout))
        wallet.save()

        return Response({
            "message": "فروش با موفقیت انجام شد و مبلغ به کیف پول واریز شد",
            "details": {
                "sold_weight": round(weight_to_sell, 5),
                "payout_toman": round(final_payout),
                "wallet_balance": round(wallet.balance)
            }
        })
    

class UserAssets(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        price_per_gram = get_live_gold_price()
        inventory, _ = GoldInventory.objects.get_or_create(user=request.user)
        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        gold_weight = Decimal(str(inventory.balance))
        gold_value_toman = gold_weight * price_per_gram
        wallet_balance = Decimal(str(wallet.balance))
        
        # ارزش کل دارایی = ارزش طلای موجود + موجودی نقدی کیف پول
        total_assets_value = gold_value_toman + wallet_balance

        return Response({
            "total_assets_value": round(total_assets_value), # ارزش کل دارایی ب تومان
            "gold_balance_gr": round(gold_weight, 5),        # موجودی طلا ب گرم
            "wallet_balance_toman": round(wallet_balance),   # موجودی ب تومان (کیف پول)
            "live_price": price_per_gram                     # قیمت لحظه‌ای جهت اطلاع
        })