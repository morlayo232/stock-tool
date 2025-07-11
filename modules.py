import yfinance as yf
import ta
import pandas as pd

# Hover 툴팁 용어 설명
TOOLTIP_EXPLANATIONS = {
    "RSI": "상대강도지수: 과매수/과매도 상태 판단 (70↑ 과매수, 30↓ 과매도)",
    "EMA": "지수이동평균선: 최근 가격에 가중치를 둔 추세 지표",
    "MACD": "이동평균 간 차이를 이용한 추세 반전 지표",
    "PER": "주가수익비율: 수익 대비 주가의 수준 (낮을수록 저평가)",
    "PBR": "주가순자산비율: 자산 대비 주가 수준 (1보다 낮으면 저평가)",
    "배당수익률": "연 배당금 ÷ 주가 = 배당 투자 수익률",
    "매수 추천가": "최근 골든크로스 발생 지점의 종가",
    "매도 추천가": "최근 데드크로스 발생 지점의 종가"
}

def load_stock_price(ticker):
    try:
        df = yf.Ticker(ticker).history(period="6mo")
        df.reset_index(inplace=True)
        if df.empty or len(df) < 10:
            raise ValueError("No data")
        return df
    except:
        return pd.DataFrame()

def calculate_indicators(df):
    df['EMA5'] = ta.trend.EMAIndicator(df['Close'], window=5).ema_indicator()
    df['EMA20'] = ta.trend.EMAIndicator(df['Close'], window=20).ema_indicator()
    df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['Signal'] = macd.macd_signal()
    return df
