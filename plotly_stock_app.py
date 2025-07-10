import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import ta

# --- 사이드바: 종목 입력 ---
st.sidebar.markdown("📌 **종목 선택**")
ticker = st.sidebar.text_input("티커 입력 (예: 삼성전자 → 005930.KS)", "005930.KS")

# --- 종목 데이터 로딩 ---
@st.cache_data
def load_data(ticker):
    stock = yf.Ticker(ticker)
    df = stock.history(period="6mo")
    df.reset_index(inplace=True)
    return df

df = load_data(ticker)

# --- 기술 지표 계산 ---
df['EMA5'] = ta.trend.ema_indicator(df['Close'], window=5).
df['EMA20'] = ta.trend.ema_indicator(df['Close'], window=20).
df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
macd = ta.trend.MACD(df['Close'])
df['MACD'] = macd.macd()
df['Signal'] = macd.macd_signal()

# --- 본문 제목 ---
st.markdown(f"### 📈 {ticker} 주가 차트 + 기술적 지표")

# --- 주가 + 이동평균 ---
fig_price = go.Figure()
fig_price.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='종가', line=dict(color='blue')))
fig_price.add_trace(go.Scatter(x=df['Date'], y=df['EMA5'], name='EMA 5일', line=dict(color='orange')))
fig_price.add_trace(go.Scatter(x=df['Date'], y=df['EMA20'], name='EMA 20일', line=dict(color='green')))
fig_price.update_layout(title="📊 주가 + 이동평균", xaxis_title="날짜", yaxis_title="가격", hovermode="x unified")

# --- RSI + MACD ---
fig_tech = go.Figure()
fig_tech.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], name='RSI', line=dict(color='purple')))
fig_tech.add_trace(go.Scatter(x=df['Date'], y=[70]*len(df), name='과매수선 (70)', line=dict(color='red', dash='dot')))
fig_tech.add_trace(go.Scatter(x=df['Date'], y=[30]*len(df), name='과매도선 (30)', line=dict(color='blue', dash='dot')))
fig_tech.add_trace(go.Scatter(x=df['Date'], y=df['MACD'], name='MACD', line=dict(color='black')))
fig_tech.add_trace(go.Scatter(x=df['Date'], y=df['Signal'], name='Signal', line=dict(color='orange')))
fig_tech.update_layout(title="📉 RSI & MACD 분석", xaxis_title="날짜", hovermode="x unified")

# --- 차트 출력 ---
st.plotly_chart(fig_price, use_container_width=True)
st.plotly_chart(fig_tech, use_container_width=True)

# --- 추천 포인트 판단 ---
latest_rsi = df['RSI'].iloc[-1]
latest_macd = df['MACD'].iloc[-1]
latest_signal = df['Signal'].iloc[-1]

st.markdown("### 💡 투자 판단 요약")
if latest_rsi > 70:
    st.warning("⚠️ RSI 70 이상 → 과매수 구간으로 매도 고려")
elif latest_rsi < 30:
    st.success("✅ RSI 30 이하 → 과매도 구간으로 매수 기회")
else:
    st.info("ℹ️ RSI 중간값 → 관망")

if latest_macd > latest_signal:
    st.success("📈 MACD > Signal → 상승 전환 신호")
else:
    st.warning("📉 MACD < Signal → 하락 전환 주의")

# --- 지표 설명 ---
with st.sidebar.expander("📖 기술 지표 설명 보기"):
    st.markdown("""
- **RSI (상대강도지수)**: 70 이상이면 과매수, 30 이하면 과매도로 판단  
- **MACD**: 추세 전환 지표 (MACD > Signal 이면 상승 추세로 판단)  
- **EMA**: 최근 가격에 가중치를 둔 이동 평균  
    """)

