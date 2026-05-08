from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from .serializers import FinancialReportSerializer, GiftCardOrderSerializer, GiftCardSerializer, GoldTransactionReportSerializer, PriceAlertSerializer, ProductSerializer, CartSerializer, OrderSerializer
from silver_app.models import SilverInventory, SilverTransaction
from .models import AdminBankInfo, FinancialTransaction, GiftCard, GiftCardOrder, GoldInventory, GoldTransaction, PriceAlert, ReferralEarning
from .utils import get_live_gold_price
from .models import GoldInventory, GoldTransaction, Wallet
from .utils import get_live_gold_price
from silver_app.models import SilverInventory
from .utils import get_live_gold_price, get_live_silver_price
from .utils import get_live_silver_price 
from decimal import Decimal, InvalidOperation
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Product, Cart, Order, OrderItem, GoldInventory, Wallet
from .utils import get_live_gold_price
from decimal import Decimal
from rest_framework import status
from .utils import get_live_gold_price
from django.db.models import Sum
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import GoldTransaction, GoldInventory, Wallet, ReferralEarning, FinancialTransaction
from .utils import get_live_gold_price
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from decimal import Decimal
from .models import GoldInventory, GoldTransaction, Wallet, FinancialTransaction, GiftCard
from .utils import get_live_gold_price # فرض بر اینکه این تابع را دارید




# --- داشبورد طلاینه (تحلیلی) ---
class GoldDashboardAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        gold_price = get_live_gold_price() # قیمت لحظه‌ای طلا ۱۸ یا ۲۴
        
        gold_inv, _ = GoldInventory.objects.get_or_create(user=user)
        wallet, _ = Wallet.objects.get_or_create(user=user)

        gold_balance = Decimal(str(gold_inv.balance))
        toman_balance = Decimal(str(wallet.balance))
        gold_value = gold_balance * gold_price

        # دیتای نمودار (استاتیک برای فرانت)
        chart_data = {
            "labels": ["01/20", "01/25", "02/05", "02/18"],
            "values": [2800000, 2950000, 3100000, 3250000], # نمونه قیمت طلا
            "highest": 3300000,
            "lowest": 2700000,
            "change_percent": 4.2
        }

        return Response({
            "assets": {
                "total_assets_value": round(gold_value + toman_balance),
                "gold_balance_gr": round(gold_balance, 5),
                "toman_balance": round(toman_balance)
            },
            "price_info": {
                "current_price": gold_price,
                "change_percent": 4.2,
                "chart": chart_data
            }
        })

# --- کیف پول طلاینه (عملیاتی و فعالیت‌ها) ---
class GoldWalletAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        gold_price = get_live_gold_price()
        
        gold_inv, _ = GoldInventory.objects.get_or_create(user=user)
        wallet, _ = Wallet.objects.get_or_create(user=user)
        
        gold_balance = Decimal(str(gold_inv.balance))
        toman_balance = Decimal(str(wallet.balance))
        gold_value = gold_balance * gold_price

        # ۱. مجموع دارایی
        total_assets = gold_value + toman_balance

        # ۲. محاسبه سود (تفاضل ارزش فعلی از کل مبالغ خرید)
        total_spent = GoldTransaction.objects.filter(
            user=user, type='BUY', is_completed=True
        ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        profit = gold_value - Decimal(str(total_spent))

        # ۳. طلا و تومان در انتظار پردازش
        pending_toman = FinancialTransaction.objects.filter(
            user=user, status='PENDING', type='WITHDRAW'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        pending_gold = GoldTransaction.objects.filter(
            user=user, is_completed=False, type='BUY'
        ).aggregate(Sum('amount_gr'))['amount_gr__sum'] or 0

        # ۴. کارت‌های هدیه (ارزش ریالی کارت‌های فعال شده)
        gift_cards_value = GiftCard.objects.filter(
            activated_by=user
        ).aggregate(Sum('weight'))['weight__sum'] or 0
        gift_cards_toman = gift_cards_value * gold_price

        return Response({
            "wallet_header": {
                "total_assets_value": round(total_assets),
                "description": "ارزش دارایی مجموع دارایی طلا و دارایی نقدی شماست",
                "gold_balance_gr": round(gold_balance, 5),
                "toman_balance": round(toman_balance)
            },
            "activity_summary": {
                "total_assets": round(total_assets),
                "profit": round(profit),
                "withdrawn_gold_gr": 0, # فیلد کمکی اگر در مدل اینونتوری باشد
                "gift_cards_toman": round(gift_cards_toman),
                "pending_toman": round(pending_toman),
                "pending_gold_gr": round(pending_gold, 5)
            },
            "current_gold_price": gold_price
        })













class BuyGold(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        price_per_gram = get_live_gold_price()
        
        if not price_per_gram:
            return Response({"error": "خطا در دریافت قیمت لحظه‌ای طلا"}, status=500)

        toman_amount = request.data.get('toman')
        weight_amount = request.data.get('weight')
        fee_rate = Decimal('0.01')  # کارمزد ۱ درصد کل

        # ۱. محاسبات بر اساس ورودی
        if toman_amount:
            total_toman = Decimal(str(toman_amount))
            fee = total_toman * fee_rate
            net_amount = total_toman - fee
            weight = net_amount / price_per_gram
        elif weight_amount:
            weight = Decimal(str(weight_amount))
            net_amount = weight * price_per_gram
            fee = net_amount * fee_rate
            total_toman = net_amount + fee
        else:
            return Response({"error": "لطفاً مبلغ یا وزن را وارد کنید"}, status=400)

        # ۲. بررسی موجودی کیف پول ریالی
        try:
            wallet = Wallet.objects.get(user=user)
        except Wallet.DoesNotExist:
            return Response({"error": "کیف پول یافت نشد"}, status=404)

        if wallet.balance < total_toman:
            return Response({"error": "موجودی کیف پول کافی نیست"}, status=400)

        # ۳. کسر از کیف پول و آپدیت موجودی طلا
        wallet.balance -= total_toman
        wallet.save()

        inventory, _ = GoldInventory.objects.get_or_create(user=user)
        inventory.balance += weight
        inventory.save()

        # ۴. ثبت تراکنش خرید طلا
        transaction = GoldTransaction.objects.create(
            user=user,
            type='BUY',
            amount_gr=weight,
            price_per_gram=price_per_gram,
            fee=fee,
            total_amount=total_toman,
            is_completed=True
        )

        # ۵. منطق سود معرف (۲۰ درصد از کارمزد)
        referrer = user.referred_by
        if referrer and fee > 0:
            referral_bonus = fee * Decimal('0.20')  # ۲۰٪ از ۱٪ کارمزد
            
            # واریز به کیف پول معرف
            ref_wallet, _ = Wallet.objects.get_or_create(user=referrer)
            ref_wallet.balance += referral_bonus
            ref_wallet.save()
            
            # ثبت گزارش سود معرف
            ReferralEarning.objects.create(
                referrer=referrer,
                referred_user=user,
                amount=referral_bonus
            )
            
            # ثبت تراکنش مالی برای معرف (جهت نمایش در گزارشات)
            FinancialTransaction.objects.create(
                user=referrer,
                amount=referral_bonus,
                type='DEPOSIT',
                method='REFERRAL', # مطمئن شو در مدل FinancialTransaction این گزینه در choices هست
                status='COMPLETED',
                description=f"سود دعوت از کاربر {user.mobile}"
            )

        # ۶. پاسخ نهایی
        return Response({
            "message": "خرید با موفقیت انجام شد",
            "details": {
                "weight_gr": round(weight, 5),
                "price_per_gram": format(price_per_gram, ','),
                "fee_toman": round(fee),
                "total_paid_toman": round(total_toman),
                "new_wallet_balance": round(wallet.balance)
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
        # دریافت قیمت‌های لحظه‌ای
        gold_price = get_live_gold_price()
        silver_price = get_live_silver_price()

        # دریافت موجودی‌ها (اگر رکورد نباشد، ساخته می‌شود)
        gold_inv, _ = GoldInventory.objects.get_or_create(user=request.user)
        silver_inv, _ = SilverInventory.objects.get_or_create(user=request.user)
        wallet, _ = Wallet.objects.get_or_create(user=request.user)

        # تبدیل مقادیر به Decimal برای محاسبات دقیق
        gold_weight = Decimal(str(gold_inv.balance))
        silver_weight = Decimal(str(silver_inv.balance))
        wallet_balance = Decimal(str(wallet.balance))

        # محاسبه ارزش ریالی هر دارایی
        gold_value = gold_weight * gold_price
        silver_value = silver_weight * silver_price
        
        # مجموع کل دارایی‌ها
        total_assets_value = gold_value + silver_value + wallet_balance

        return Response({
            "total_assets_value": round(total_assets_value), # جمع کل (ریال + طلا + نقره)
            "gold_balance_gr": round(gold_weight, 5),
            "silver_balance_gr": round(silver_weight, 5),
            "wallet_balance_toman": round(wallet_balance),
            "gold_value_toman": round(gold_value),     # ارزش طلای کاربر به تومان
            "silver_value_toman": round(silver_value), # ارزش نقره کاربر به تومان
            "live_gold_price": gold_price,
            "live_silver_price": silver_price
        })


class DepositMoney(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """نمایش اطلاعات حساب جهت واریز کاربر"""
        bank_info = AdminBankInfo.get_active_info()
        return Response(bank_info)

    def post(self, request):
        """ثبت رسید واریز وجه"""
        amount = request.data.get('amount')
        receipt = request.FILES.get('receipt')

        if not amount or not receipt:
            return Response({"error": "مبلغ و تصویر رسید الزامی است"}, status=400)

        FinancialTransaction.objects.create(
            user=request.user,
            amount=Decimal(str(amount)),
            type='DEPOSIT',
            method='CARD',
            receipt_image=receipt,
            status='PENDING'
        )
        return Response({"message": "رسید با موفقیت ثبت شد. پس از تایید مدیریت، کیف پول شارژ می‌شود."}, status=201)


class WithdrawMoney(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """درخواست برداشت وجه یا تبدیل به نقره"""
        amount_raw = request.data.get('amount')
        target = request.data.get('target')  # 'bank' or 'silver'

        if not amount_raw or not target:
            return Response({"error": "مبلغ و مقصد (target) الزامی هستند"}, status=400)

        try:
            # تبدیل امن به Decimal برای جلوگیری از خطای نوع داده
            amount = Decimal(str(amount_raw))
        except InvalidOperation:
            return Response({"error": "مبلغ وارد شده معتبر نیست"}, status=400)

        if amount <= 0:
            return Response({"error": "مبلغ باید بیشتر از صفر باشد"}, status=400)

        # دریافت کیف پول ریالی
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        # اطمینان از Decimal بودن موجودی کیف پول
        current_wallet_balance = Decimal(str(wallet.balance))

        if current_wallet_balance < amount:
            return Response({"error": "موجودی کیف پول کافی نیست"}, status=400)

        # --- سناریو ۱: تبدیل مستقیم به نقره ---
        if target == 'silver':
            silver_price = get_live_silver_price()
            if not silver_price:
                return Response({"error": "خطا در دریافت قیمت لحظه‌ای نقره"}, status=500)
            
            # محاسبه وزن نقره (Decimal / Decimal)
            weight_to_add = amount / silver_price

            # کسر از کیف پول ریالی
            wallet.balance = current_wallet_balance - amount
            wallet.save()

            # اضافه به موجودی نقره
            silver_inv, _ = SilverInventory.objects.get_or_create(user=request.user)
            # تبدیل موجودی فعلی به Decimal قبل از جمع
            silver_inv.balance = Decimal(str(silver_inv.balance)) + weight_to_add
            silver_inv.save()

 
            # ثبت در تاریخچه نقره
            SilverTransaction.objects.create(
                user=request.user,
                amount_gr=weight_to_add,
                total_amount=amount,
                type='CONVERT'
            )
            return Response({
                "message": "مبلغ با موفقیت به موجودی نقره تبدیل شد",
                "added_weight": round(weight_to_add, 5),
                "new_wallet_balance": wallet.balance
            })

        # --- سناریو ۲: درخواست واریز به حساب بانکی ---
        elif target == 'bank':
            card_id = request.data.get('card_id')
            if not card_id:
                return Response({"error": "برای واریز نقدی انتخاب کارت الزامی است"}, status=400)

            # ثبت تراکنش مالی ریالی
            FinancialTransaction.objects.create(
                user=request.user,
                amount=amount,
                type='WITHDRAW',
                method='CARD',
                user_card_id=card_id,
                status='PENDING'
            )
            
            # کسر از کیف پول (پول بلوکه می‌شود تا ادمین واریز کند)
            wallet.balance = current_wallet_balance - amount
            wallet.save()

            return Response({
                "message": "درخواست واریز نقدی ثبت شد و در صف بررسی قرار گرفت.",
                "new_wallet_balance": wallet.balance
            })

        return Response({"error": "مقصد نامعتبر است"}, status=400)
    



class ProductListView(APIView):
    def get(self, request):
        category = request.query_params.get('category')
        products = Product.objects.filter(is_active=True)
        if category:
            products = products.filter(category=category)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)



class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart_items = Cart.objects.filter(user=request.user)
        gold_price = get_live_gold_price()
        
        results = []
        total_gold = Decimal('0')
        total_toman = Decimal('0')

        for item in cart_items:
            item_gold = item.product.total_weight_with_fees * item.quantity
            item_toman = item_gold * gold_price
            total_gold += item_gold
            total_toman += item_toman
            
            results.append({
                "id": item.id,
                "product_name": item.product.name,
                "weight": item_gold,
                "toman": round(item_toman),
                "quantity": item.quantity
            })

        return Response({
            "items": results,
            "total_gold": total_gold,
            "total_toman": round(total_toman),
            "user_gold_balance": GoldInventory.objects.get(user=request.user).balance,
            "user_wallet_balance": Wallet.objects.get(user=request.user).balance
        })

    def post(self, request):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        product = Product.objects.get(id=product_id)
        
        cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()
        return Response({"message": "به سبد خرید اضافه شد"})



class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        payment_method = request.data.get('payment_method') # 'GOLD' or 'TOMAN'
        address = request.data.get('address')
        city = request.data.get('city')
        
        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            return Response({"error": "سبد خرید خالی است"}, status=400)

        gold_price = get_live_gold_price()
        total_gold = sum(item.product.total_weight_with_fees * item.quantity for item in cart_items)
        total_toman = total_gold * gold_price

        # بررسی موجودی
        if payment_method == 'GOLD':
            inv = GoldInventory.objects.get(user=user)
            if inv.balance < total_gold:
                return Response({"error": "موجودی طلا کافی نیست"}, status=400)
            inv.balance -= total_gold
            inv.save()
        else:
            wallet = Wallet.objects.get(user=user)
            if wallet.balance < total_toman:
                return Response({"error": "موجودی تومان کافی نیست"}, status=400)
            wallet.balance -= total_toman
            wallet.save()

        # ثبت سفارش
        order = Order.objects.create(
            user=user, address=address, city=city,
            payment_method=payment_method,
            total_gold_amount=total_gold,
            total_toman_amount=total_toman
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order, product=item.product,
                quantity=item.quantity,
                price_at_time=item.product.total_weight_with_fees * gold_price,
                weight_at_time=item.product.total_weight_with_fees
            )
        
        cart_items.delete()
        return Response({"message": "سفارش شما با موفقیت ثبت شد", "order_id": order.id})




class OrderHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        # سریالایزر ساده برای نمایش تاریخچه
        data = [{
            "id": o.id,
            "status": o.status,
            "total_gold": o.total_gold_amount,
            "created_at": o.created_at
        } for o in orders]
        return Response(data)
    



class GiftCardOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        weight = Decimal(request.data.get('weight', 0))
        quantity = int(request.data.get('quantity', 1))
        
        if weight <= 0:
            return Response({"error": "وزن معتبر نیست"}, status=400)

        gold_price = get_live_gold_price()
        
        # محاسبات طبق طرح شما
        pure_price = weight * gold_price * quantity
        fee_and_tax = Decimal('565442') * quantity # فرضی طبق طرح شما
        packaging = Decimal('600000') # فرضی طبق طرح شما
        total_price = pure_price + fee_and_tax + packaging

        # چک کردن موجودی کیف پول
        wallet = Wallet.objects.get(user=user)
        if wallet.balance < total_price:
            return Response({"error": "موجودی کیف پول کافی نیست"}, status=400)

        # کسر از کیف پول و ثبت سفارش
        wallet.balance -= total_price
        wallet.save()

        order = GiftCardOrder.objects.create(
            user=user,
            weight_per_card=weight,
            quantity=quantity,
            total_price=total_price,
            province=request.data.get('province'),
            city=request.data.get('city'),
            address=request.data.get('address'),
            postal_code=request.data.get('postal_code'),
            plaque=request.data.get('plaque'),
            unit=request.data.get('unit')
        )

        return Response({
            "message": "سفارش کارت هدیه با موفقیت ثبت شد",
            "total_price": total_price,
            "order_id": order.id
        })




class RedeemGiftCardView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serial = request.data.get('serial_number')
        try:
            card = GiftCard.objects.get(serial_number=serial, is_used=False)
        except GiftCard.DoesNotExist:
            return Response({"error": "کد نامعتبر است یا قبلاً استفاده شده"}, status=400)

        # اضافه کردن وزن کارت به موجودی طلای کاربر
        inventory, _ = GoldInventory.objects.get_or_create(user=request.user)
        inventory.balance += card.weight
        inventory.save()

        # سوزاندن کارت
        card.is_used = True
        card.activated_by = request.user
        card.save()

        return Response({
            "message": f"موفق! {card.weight} گرم طلا به حساب شما اضافه شد."
        })





class UserGiftCardListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # لیست کارت‌هایی که این کاربر فعال کرده است
        cards = GiftCard.objects.filter(activated_by=request.user)
        serializer = GiftCardSerializer(cards, many=True)
        return Response(serializer.data)
    



class ReportsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tab = request.query_params.get('tab') # دریافت نوع گزارش از پارامتر URL
        user = request.user

        # ۱. گزارش معاملات (خرید و فروش طلا)
        if tab == 'trades':
            trades = GoldTransaction.objects.filter(user=user).order_by('-created_at')
            serializer = GoldTransactionReportSerializer(trades, many=True)
            return Response(serializer.data)

        # ۲. گزارش واریز (تراکنش‌های ریالی مثبت)
        elif tab == 'deposits':
            deposits = FinancialTransaction.objects.filter(user=user, type='DEPOSIT').order_by('-created_at')
            serializer = FinancialReportSerializer(deposits, many=True)
            return Response(serializer.data)

        # ۳. گزارش برداشت (تراکنش‌های ریالی منفی)
        elif tab == 'withdrawals':
            withdrawals = FinancialTransaction.objects.filter(user=user, type='WITHDRAW').order_by('-created_at')
            serializer = FinancialReportSerializer(withdrawals, many=True)
            return Response(serializer.data)

        # ۴. گزارش کارت هدیه (خریدها و فعال‌سازی‌ها)
        elif tab == 'giftcards':
            # کارت‌هایی که خریده (سفارش داده)
            orders = GiftCardOrder.objects.filter(user=user).order_by('-created_at')
            # کارت‌هایی که فعال کرده (نقد کرده)
            redeemed = GiftCard.objects.filter(activated_by=user).order_by('-created_at')
            
            return Response({
                "purchased_orders": GiftCardOrderSerializer(orders, many=True).data,
                "redeemed_cards": GiftCardSerializer(redeemed, many=True).data
            })

        # ۵. تحویل فیزیکی (سفارشات محصولات مثل شمش و سکه)
        elif tab == 'physical_orders':
            orders = Order.objects.filter(user=user).order_by('-created_at')
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data)

        return Response({"error": "فیلتر نامعتبر است"}, status=400)
    

class PriceAlertView(APIView):
    permission_classes = [IsAuthenticated]

    # لیست آلارم‌های اخیر کاربر
    def get(self, request):
        alerts = PriceAlert.objects.filter(user=request.user).order_by('-created_at')
        serializer = PriceAlertSerializer(alerts, many=True)
        return Response(serializer.data)

    # فعال کردن آلارم جدید
    def post(self, request):
        serializer = PriceAlertSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({"message": "آلارم قیمت با موفقیت فعال شد", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PriceAlertDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            alert = PriceAlert.objects.get(pk=pk, user=request.user)
            alert.delete()
            return Response({"message": "آلارم حذف شد"}, status=status.HTTP_204_NO_CONTENT)
        except PriceAlert.DoesNotExist:
            return Response({"error": "آلارم پیدا نشد"}, status=status.HTTP_404_NOT_FOUND)
        



class ReferralDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # تعداد کل دعوت شده‌ها
        total_invited = user.subscribers.count()
        
        # مجموع سود دریافتی
        total_earned = ReferralEarning.objects.filter(referrer=user).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # لیست تراکنش‌های اخیر رفرال (اختیاری)
        recent_earnings = ReferralEarning.objects.filter(referrer=user).order_by('-transaction_date')[:5]
        
        return Response({
            "referral_code": user.referral_code,
            "total_invited": total_invited,
            "total_earned_toman": total_earned,
            "commission_rate": "20%",
            "message": "با دعوت از دوستان خود ۲۰ درصد از کارمزد هر خرید آن‌ها، برای شما واریز خواهد شد."
        })