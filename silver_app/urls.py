from django.urls import path
from .views import (
    SilverDashboardAPI, SilverWalletAPI, BuySilver, 
    SellSilver, SilverDeposit, BankCardAPI
)

urlpatterns = [
    path('dashboard/', SilverDashboardAPI.as_view()),
    path('wallet/', SilverWalletAPI.as_view()),
    path('buy/', BuySilver.as_view()),
    path('sell/', SellSilver.as_view()),
    path('deposit/', SilverDeposit.as_view()),
    path('cards/', BankCardAPI.as_view()),
]