import pandas as pd
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import time

# 예시 티커 리스트 (확장 가능)
KOSPI_CODES = ["005930.KS", "000660.KS", "035420.KQ"]

def get_stock_info(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        df = stock.history(period="3mo")
        df.reset_index(inplace=True)
        last_close = df['Close'].iloc[-1] if not df.empty else 0
        first_close = df['Close'].iloc[0] if len(df) > 0 else 0
        return {
            'ticker': ticker,
            'name': info.get('shortName', 'N/A'),
            'PER': info.get('trailingPE', 0),
            'PBR': info.get('priceToBook', 0),
            '배당률': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
            '거래량': info.get('volume', 0),
            '3개월수익률': ((last_close - first_close) / first_close * 100) if first_close else 0
        }
    except:
        return None

def get_dividend_from_naver(name):
    try:
        url = f"https://finance.naver.com/item/main.nhn?query={name}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        d = soup.select_one(".rate_info .per_table td")
        if d:
            val = d.text.strip().replace('%','')
            return float(val)
    except:
        pass
    return 0

def update_all():
    results = []
    for ticker in KOSPI_CODES:
        print(f"[+] 수집중: {ticker}")
        info = get_stock_info(ticker)
        if info:
            naver_div = get_dividend_from_naver(info['name'])
            if naver_div:
                info['배당률'] = naver_div
            results.append(info)
        time.sleep(0.5)

    df = pd.DataFrame(results)

    # 필터링 예시
    df = df[(df['거래량'] > 100000) & (df['PER'] > 0) & (df['3개월수익률'] > -50)]

    df.to_csv("filtered_stocks.csv", index=False, encoding="utf-8-sig")
    print("[✔] filtered_stocks.csv 저장 완료")

if __name__ == "__main__":
    update_all()
