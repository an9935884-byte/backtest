import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from FinMind.data import DataLoader
from datetime import datetime, timedelta

st.set_page_config(page_title="台指期回測工具", layout="wide")

# 1. 記憶進度
if 'idx' not in st.session_state:
    st.session_state.idx = 50

# 2. 抓取資料 (改用更穩定的 fetch 方式)
@st.cache_data
def load_data(start_date):
    dl = DataLoader()
    try:
        # 改用 fetch 這種通用型指令，避開特定名稱不存在的問題
        df = dl.taiwan_futures_daily(
            futures_id='TX',
            start_date=start_date
        )
        
        # 整理欄位 (FinMind 回傳格式統一處理)
        df['date'] = pd.to_datetime(df['date'])
        df = df.rename(columns={
            'open': 'Open', 'max': 'High', 'min': 'Low', 'close': 'Close', 'volume': 'Volume'
        })
        return df
    except Exception as e:
        st.error(f"API 抓取失敗: {e}")
        return pd.DataFrame()

# 3. 介面控制
st.sidebar.title("🕹️ 回測控制")
# 由於分K API 較不穩定，我們先確保日線能跑通，再進階到分K
start_d = st.sidebar.date_input("開始日期", datetime.now() - timedelta(days=365))

if st.sidebar.button("下一根 ➡️"):
    st.session_state.idx += 1
if st.sidebar.button("重置回測 ⏪"):
    st.session_state.idx = 50

# 4. 執行與顯示
df = load_data(start_d.strftime('%Y-%m-%d'))

if not df.empty:
    if st.session_state.idx > len(df):
        st.session_state.idx = len(df)
        
    view_df = df.iloc[:st.session_state.idx]

    # 繪製 K 線圖
    fig = go.Figure(data=[go.Candlestick(
        x=view_df['date'], open=view_df['Open'], high=view_df['High'],
        low=view_df['Low'], close=view_df['Close'],
        increasing_line_color='red', decreasing_line_color='green'
    )])
    
    fig.update_layout(
        xaxis_rangeslider_visible=False, 
        height=650, 
        template="plotly_dark",
        title=f"台指期 K線圖 (目前日期: {view_df.iloc[-1]['date'].date()})"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 5. 數據面板
    k = view_df.iloc[-1]
    c1, c2, c3 = st.columns(3)
    c1.metric("當前時間", k['date'].strftime('%Y-%m-%d'))
    c2.metric("收盤價", f"{int(k['Close'])}")
    c3.metric("進度", f"第 {st.session_state.idx} 根")
else:
    st.warning("目前無法獲取資料，請檢查網路連線或更換開始日期。")
