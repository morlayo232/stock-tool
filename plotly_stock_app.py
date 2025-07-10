import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import ta

# --- 종목 리스트 로드 ---
@st.cache_data(ttl=86400)
def load_stock_list():
    df = pd.read_csv("filtered_stocks.csv")
    return df

stocks_df = load_stock_list()

# --- 투자 성향별 점수 산출 함수 (예시 단순화) ---
def calculate_score(df, style):
    if df.empty:
        return 0
    vol_ma5 = df['Volume'].rolling(5).mean()
    close_diff3 = df['Close'].diff().rolling(3).sum()
    cross_diff = df['EMA5'] - df['EMA20']
    ema_cross_recent = (cross_diff.shift(1) < 0) & (cross_diff > 0)
    rsi = df['RSI']

    score = 0
    if style == '공격적':
        score += ((df['Volume'] > vol_ma5 * 2).astype(int) * 40).iloc[-1]
        score += ((close_diff3 > 0).astype(int) * 30).iloc[-1]
        score += (ema_cross_recent.astype(int) * 20).iloc[-1]
        score += ((rsi.between(30, 60)).astype(int) * 10).iloc[-1]
    elif style == '안정적':
        score += ((df['Volume'] > vol_ma5).astype(int) * 20).iloc[-1]
        score += ((close_diff3 > 0).astype(int) * 20).iloc[-1]
        score += ((~ema_cross_recent).astype(int) * 30).iloc[-1]
        score += ((rsi.between(40, 60)).astype(int) * 10).iloc[-1]
    else:  # 배당형
        score += ((df['Volume'] > vol_ma5).astype(int) * 15).iloc[-1]
        score += ((close_diff3 > 0).astype(int) * 10).iloc[-1]
        score += ((~ema_cross_recent).astype(int) * 20).iloc[-1]
        score += ((rsi.between(40, 60)).astype(int) * 15).iloc[-1]

    return score

# --- 종목명 검색 함수 ---
def search_tickers_by_name(keyword):
    if not keyword:
        return []
    result = stocks_df[stocks_df['name'].str.contains(keyword, case=False)]
    return result[['ticker', 'name']].values.tolist()

# --- 주가 데이터 로드 함수 ---
@st.cache_data(ttl=86400)
def load_stock_data(ticker, period='6mo'):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            raise ValueError("데이터가 없습니다.")
        df.reset_index(inplace=True)
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

# --- UI: 투자 성향 선택 (사이드바 최상단) ---
investment_style = st.sidebar.radio(
    "투자 성향 선택",
    ('공격적', '안정적', '배당형'),
    index=0
)

# --- UI: 종목명 검색 ---
search_keyword = st.sidebar.text_input("종목명 검색")

# --- UI: 검색 결과 표시 및 선택 ---
if search_keyword:
    matches = search_tickers_by_name(search_keyword)
    if matches:
        options = [f"{name} ({ticker})" for ticker, name in matches]
        selected = st.sidebar.selectbox("종목 선택", options)
        ticker = selected.split("(")[-1][:-1]
        selected_name = selected.split("(")[0].strip()
    else:
        st.sidebar.error("검색된 종목이 없습니다.")
        st.stop()
else:
    # 초기 기본값 (예: 삼성전자)
    ticker = "005930.KS"
    selected_name = "삼성전자"

# --- 데이터 로드 및 기술 지표 계산 ---
df = load_stock_data(ticker)
if df.empty:
    st.stop()

df['EMA5'] = ta.trend.EMAIndicator(df['Close'], window=5).ema_indicator()
df['EMA20'] = ta.trend.EMAIndicator(df['Close'], window=20).ema_indicator()
df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
macd = ta.trend.MACD(df['Close'])
df['MACD'] = macd.macd()
df['Signal'] = macd.macd_signal()

# 골든/데드크로스 표시
df['Cross'] = df['EMA5'] - df['EMA20']
df['Signal_Point'] = df['Cross'].apply(lambda x: 1 if x > 0 else -1)
df['Crossover'] = df['Signal_Point'].diff()
buy_signals = df[df['Crossover'] == 2]
sell_signals = df[df['Crossover'] == -2]

# --- 투자 성향별 점수 ---
score = calculate_score(df, investment_style)

# --- 상위 10개 종목 추천 (투자성향별 점수 산출 & 정렬) ---
@st.cache_data(ttl=86400)
def calc_scores_for_all(style):
    scores = []
    for t in stocks_df['ticker']:
        d = load_stock_data(t)
        if d.empty:
            scores.append((t, 0))
            continue
        d['EMA5'] = ta.trend.EMAIndicator(d['Close'], window=5).ema_indicator()
        d['EMA20'] = ta.trend.EMAIndicator(d['Close'], window=20).ema_indicator()
        d['RSI'] = ta.momentum.RSIIndicator(d['Close']).rsi()
        macd = ta.trend.MACD(d['Close'])
        d['MACD'] = macd.macd()
        d['Signal'] = macd.macd_signal()
        s = calculate_score(d, style)
        scores.append((t, s))
    # 점수 내림차순 정렬 후 상위 10개만 반환
    return sorted(scores, key=lambda x: x[1], reverse=True)[:10]

top10_scores = calc_scores_for_all(investment_style)

top10_df = pd.DataFrame(top10_scores, columns=['ticker', 'score'])
top10_df = top10_df.merge(stocks_df[['ticker','name']], on='ticker', how='left')

# --- UI 출력 ---
st.title("📊 종목별 투자성향별 점수 및 추천")

st.markdown(f"### 선택한 종목: {selected_name} ({ticker})")
st.markdown(f"### 투자성향: {investment_style} / 점수: {score:.2f}")

fig_price = go.Figure()
fig_price.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='종가', line=dict(color='blue')))
fig_price.add_trace(go.Scatter(x=df['Date'], y=df['EMA5'], name='EMA 5일', line=dict(color='orange')))
fig_price.add_trace(go.Scatter(x=df['Date'], y=df['EMA20'], name='EMA 20일', line=dict(color='green')))
fig_price.add_trace(go.Scatter(
    x=buy_signals['Date'], y=buy_signals['Close'],
    mode='markers', name='📈 골든크로스 매수',
    marker=dict(color='green', size=10, symbol='triangle-up')
))
fig_price.add_trace(go.Scatter(
    x=sell_signals['Date'], y=sell_signals['Close'],
    mode='markers', name='📉 데드크로스 매도',
    marker=dict(color='red', size=10, symbol='triangle-down')
))
fig_price.update_layout(title="📈 주가 + 이동평균 + 매수/매도 신호", xaxis_title="날짜", yaxis_title="가격", hovermode="x unified")
st.plotly_chart(fig_price, use_container_width=True)

fig_tech = go.Figure()
fig_tech.add_trace(go.Scatter(x=df['Date'], y=df['RSI'], name='RSI', line=dict(color='purple')))
fig_tech.add_trace(go.Scatter(x=df['Date'], y=[70]*len(df), name='과매수선 (70)', line=dict(color='red', dash='dot')))
fig_tech.add_trace(go.Scatter(x=df['Date'], y=[30]*len(df), name='과매도선 (30)', line=dict(color='blue', dash='dot')))
fig_tech.add_trace(go.Scatter(x=df['Date'], y=df['MACD'], name='MACD', line=dict(color='black')))
fig_tech.add_trace(go.Scatter(x=df['Date'], y=df['Signal'], name='Signal', line=dict(color='orange')))
fig_tech.update_layout(title="📉 RSI & MACD 분석", xaxis_title="날짜", hovermode="x unified")
st.plotly_chart(fig_tech, use_container_width=True)

st.markdown("### 💡 투자 판단 요약")
latest_rsi = df['RSI'].iloc[-1]
latest_macd = df['MACD'].iloc[-1]
latest_signal = df['Signal'].iloc[-1]

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

# --- 상위 10개 점수화 종목 표시 ---
st.markdown("### 🏆 투자성향별 상위 10개 추천 종목")
for idx, row in top10_df.iterrows():
    st.write(f"{idx+1}. {row['name']} ({row['ticker']}) - 점수: {row['score']:.2f}")

# --- 기술 지표 설명 ---
with st.sidebar.expander("📖 기술 지표 설명 보기"):
    st.markdown("""
- **투자 성향**: 공격적, 안정적, 배당형별로 수급과 추세 지표 반영 다름  
- **RSI (상대강도지수)**: 70 이상 과매수, 30 이하 과매도 판단  
- **MACD**: 추세 전환 신호 (MACD > Signal 상승 추세)  
- **EMA 골든크로스/데드크로스**: 매수/매도 신호로 활용  
    """)
