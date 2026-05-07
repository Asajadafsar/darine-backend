from django.urls import path
from .views import BuyGold, DepositMoney, GiftCardOrderView, PriceAlertDeleteView, PriceAlertView, RedeemGiftCardView, ReferralDashboardView, ReportsView, SellGold, UserAssets, UserGiftCardListView, WithdrawMoney
from .views import ProductListView, CartView, CheckoutView, OrderHistoryView




urlpatterns = [
    path('buy/', BuyGold.as_view(), name='buy_gold'),
    path('sell/', SellGold.as_view(), name='sell_gold'),
    path('assets/', UserAssets.as_view(), name='user_assets'),
    path('deposit/', DepositMoney.as_view(), name='deposit_money'),
    path('withdraw/', WithdrawMoney.as_view(), name='withdraw_money'),
    path('products/', ProductListView.as_view(), name='product_list'),
    path('cart/', CartView.as_view(), name='cart_manage'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('orders/', OrderHistoryView.as_view(), name='order_history'),
    path('giftcard/order/', GiftCardOrderView.as_view(), name='giftcard_order'),
    path('giftcard/redeem/', RedeemGiftCardView.as_view(), name='giftcard_redeem'),
    path('giftcard/list/', UserGiftCardListView.as_view(), name='giftcard_list'),
    path('reports/', ReportsView.as_view(), name='user_reports'),
    path('price-alerts/', PriceAlertView.as_view(), name='price_alerts'),
    path('price-alerts/<int:pk>/', PriceAlertDeleteView.as_view(), name='delete_alert'),
    path('referral/', ReferralDashboardView.as_view(), name='referral_dashboard'),
]
