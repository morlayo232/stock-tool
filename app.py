import streamlit as st
import subprocess
import os
from datetime import datetime
from modules import TOOLTIP_EXPLANATIONS, load_stock_price, calculate_indicators
from charts import plot_stock_chart, plot_rsi_macd

# 페이지 설정
st.set_page_config(page_title="한국 주식 분석", layout="wide")

# Apple 스타일 CSS 적용
st.markdown("""
    <style>
    /* Apple 스타일 요소: 큰 제목, 여백, 부드러운 둥근 테두리 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stButton>button {
        border-radius: 12px;
        padding: 0.6em 1.2em;
        background: linear-gradient(to right, #007AFF, #00BFFF);
        color: white;
        border: none;
        font-size: 1em;
    }
    .stMarkdown h3, h2 {
        color: #1d1d1f;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📈 종목별 지표 해설 및 수동 업데이트")

# 종목코드 입력 (예시: 종목 검색 박스 대신 간단히 입력)
ticker = st.text_input("종목 코드 입력 (예: 005930)")

if ticker:
    df = load_stock_price(ticker)
    if df.empty:
        st.warning("주가 데이터를 불러올 수 없습니다.")
    else:
        df = calculate_indicators(df)

        # 차트 출력
        st.subheader(f"{ticker} 주가 및 기술 지표 차트")
        st.plotly_chart(plot_stock_chart(df), use_container_width=True)
        st.plotly_chart(plot_rsi_macd(df), use_container_width=True)

        # 투자성향별 점수 및 설명 출력 (예시 공격적)
        investment_style = '공격적'
        st.markdown(f"### 투자 성향: {investment_style}")
        # 투자 점수 계산 함수 (예: modules.py에 구현된 함수 사용)
        # score = calc_investment_score(df, investment_style)
        # st.markdown(f"투자 점수: {score:.2f}")
        # (점수 함수가 준비되어 있으면 여기에 호출해 표시)

# 지표 및 용어 설명 출력
st.markdown("### 🧠 기술 지표 용어 설명")
for key, desc in TOOLTIP_EXPLANATIONS.items():
    st.markdown(f"- **{key}**  ​  ❓")
    st.caption(desc)

# 수동 업데이트 버튼 (사이드바)
st.sidebar.markdown("### ⟳ 수동 데이터 갱신")
if st.sidebar.button("Update Now"):
    with st.spinner("업데이트 중입니다... 잠시만 기다려 주세요."):
        result = subprocess.run(["python", "update_stock_database.py"], capture_output=True, text=True)
        if result.returncode == 0:
            st.success("업데이트가 성공적으로 완료되었습니다.")
        else:
            st.error("업데이트 실패: ")
            st.code(result.stderr)

# 마지막 업데이트 시간 출력 (사이드바)
try:
    last_modified = datetime.fromtimestamp(os.path.getmtime("filtered_stocks.csv"))
    st.sidebar.markdown(f"**🔄 마지막 업데이트:** {last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
except:
    st.sidebar.warning("CSV 파일을 찾을 수 없습니다.")
