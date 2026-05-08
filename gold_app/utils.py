import requests
from decimal import Decimal

def get_live_gold_price():
    """دریافت قیمت لحظه‌ای طلا از API وال‌گلد"""
    url = "https://api.wallgold.ir/api/v1/price?side=buy&symbol=GLD_18C_750TMN"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return Decimal(str(data['result']['price']))
    except Exception as e:
        print(f"Error fetching gold price: {e}")
    return None

def get_live_silver_price():
    """دریافت قیمت لحظه‌ای نقره از API نقره‌سیء"""
    url = "https://api.noghresea.ir/api/market/getSilverPrice"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # توجه: اینجا فقط دیتای خام رو می‌گیریم، 
            # اگر در طلاینه هم می‌خوای قیمت به تومان باشه، مثل فایل نقرینه ضرب در ۱۰۰۰ کن
            return Decimal(str(data['price']))
    except Exception as e:
        print(f"Error fetching silver price: {e}")
    return None