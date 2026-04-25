from django.urls import path
from .views import BuyGold, SellGold, UserAssets

urlpatterns = [
    path('buy/', BuyGold.as_view(), name='buy_gold'),
    path('sell/', SellGold.as_view(), name='sell_gold'),
    path('assets/', UserAssets.as_view(), name='user_assets'),
]