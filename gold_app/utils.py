import requests
from decimal import Decimal

def get_live_gold_price():
    """دریافت قیمت لحظه‌ای از API"""
    url = "https://api.wallgold.ir/api/v1/price?side=buy&symbol=GLD_18C_750TMN"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # قیمت از API به صورت رشته می‌آید، آن را به عدد تبدیل می‌کنیم
            return Decimal(data['result']['price'])
    except Exception as e:
        print(f"Error fetching gold price: {e}")
    return None