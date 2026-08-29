import gspread
import json
import os
import time

import requests


def get_stock_price(symbol):
    try:
        # Fetch Yahoo Finance prices without its Python library to avoid websocket issues.
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["chart"]["result"][0]["meta"]["regularMarketPrice"]
    except (KeyError, requests.RequestException, ValueError, TypeError) as error:
        print(f"Could not fetch {symbol}: {error}")
        return "N/A"


def update_stock():
    creds_json = os.environ.get("GOOGLE_SHEETS_CREDS")
    if not creds_json:
        raise RuntimeError("GOOGLE_SHEETS_CREDS is not configured")

    creds_dict = json.loads(creds_json)
    gc = gspread.service_account_from_dict(creds_dict)
    worksheet = gc.open("stock-updater").get_worksheet(0)

    stocks = [
        "THAIBEV19.BK", "DBS19.BK", "UOB19.BK", "SEMB19.BK", "SGX19.BK",
        "FERRARI80.BK", "HERMES80.BK", "LOREAL80.BK", "SANOFI80.BK", "NOVOB80.BK",
        "TRIPCOM80.BK", "POPMART80.BK", "MEITUAN80.BK", "JD80.BK", "NONGFU80.BK",
        "SMIC23.BK", "KUAISH23.BK", "HUAHONG23.BK", "AIA23.BK", "HKEX23.BK",
        "VNM19.BK", "FPTVN19.BK", "VCB19.BK", "MWG19.BK", "GEELY80.BK",
        "ADVANT19.BK", "ADVANT23.BK", "HONDA19.BK", "ITOCHU19.BK", "KEYENCE23.BK",
        "MITSU19.BK", "MUFG19.BK", "NINTENDO19.BK", "SANRIO23.BK", "SMFG19.BK",
        "SOFTBANK23.BK", "SUSHI23.BK", "TEL23.BK", "TOYOTA80.BK", "UNIQLO80.BK",
        "ASML01.BK", "XIAOMI80.BK", "TENCENT80.BK", "PINGAN80.BK", "SINGTEL80.BK",
        "NETEASE80.BK", "VENTURE19.BK", "STEG19.BK",
    ]

    values = []
    for symbol in stocks:
        price = get_stock_price(symbol)
        values.append([price])
        print(f"Fetched {symbol}: {price}")
        time.sleep(0.5)

    worksheet.update(f"AI2:AI{1 + len(stocks)}", values)
    print("--- Update Completed ---")


if __name__ == "__main__":
    update_stock()
