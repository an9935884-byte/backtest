import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from FinMind.data import DataLoader
from datetime import datetime, timedelta

st.set_page_config(page_title="台指期 60分K 回測", layout="wide")

# 1. 記憶進度 (Session State)
if 'idx' not in st.session_state:
    st.session_state.idx = 100 # 小時線數據較多，起始顯示 100 根

# 2. 抓取 60分K 資料
@st.cache_data
def load_60min_data(start_date):
    dl = DataLoader()
    # 抓取台指期分鐘層級資料 (dataset="TaiwanFuturesTick" 再轉 K線)
    # 為了簡化流程，這裡直接使用 FinMind 的分K抓取語法
    df = dl.taiwan_futures_kline(
        futures_id='TX',
        start_date=start_date,
        kline_type='60'  # 這裡設定 60 代表 60分K
    )
    df['date'] = pd.to_datetime(df['date'])
    df = df.rename(columns={
        'open': 'Open', 'max': 'High', 'min': 'Low', 'close': 'Close', 'volume': 'Volume'
    })
    return df

# 3. 介面控制
st.sidebar.title("🕹️ 60分K 回測控制")
start_d = st.sidebar.date_input("開始日期", datetime.now() - timedelta(days=60)) # 小時線建議日期不要太長

if st.sidebar.button("下一根 (1小時) ➡️"):
    st.session_state.idx += 1
if st.sidebar.button("重置回測 ⏪"):
    st.session_state.idx = 100

# 4. 執行抓取與顯示
try:
    raw_df = load_60min_data(start_d.strftime('%Y-%m-%d'))
    
    if len(raw_df) == 0:
        st.warning("該日期範圍內無資料，請嘗試更早的日期。")
        st.stop()

    view_df = raw_df.iloc[:st.session_state.idx]

    # 繪製圖表
    fig = go.Figure(data=[go.Candlestick(
        x=view_df['date'], open=view_df['Open'], high=view_df['High'],
        low=view_df['Low'], close=view_df['Close'],
        increasing_line_color='red', decreasing_line_color='green'
    )])
    
    fig.update_layout(
        xaxis_rangeslider_visible=False, 
        height=650, 
        template="plotly_dark",
        title=f"台指期 60分鐘K線圖 (目前進度: {view_df.iloc[-1]['date']})"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 5. 當前數據面板
    k = view_df.iloc[-1]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("時間", k['date'].strftime('%H:%M'))
    c2.metric("收盤", f"{int(k['Close'])}")
    c3.metric("成交量", int(k['Volume']))
    c4.metric("進度", f"{st.session_state.idx} 根")

except Exception as e:
    st.error(f"發生錯誤: {e}")
