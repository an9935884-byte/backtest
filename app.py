import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from FinMind.data import DataLoader
from datetime import datetime, timedelta

st.set_page_config(page_title="台指期 60分K 回測修正版", layout="wide")

# 1. 記憶進度
if 'idx' not in st.session_state:
    st.session_state.idx = 100

# 2. 抓取 60分K 資料 (修正後的邏輯)
@st.cache_data
def load_60min_data(start_date):
    dl = DataLoader()
    # 使用正式的 dataset 名稱抓取分鐘資料
    # 注意：FinMind 免費版抓取分鐘資料通常有時間限制，建議先抓最近 30 天
    df = dl.taiwan_futures_kline_15minute(
        futures_id='TX',
        start_date=start_date
    )
    
    # 將 15分K 轉合成 60分K (因為 API 直接提供 60分K 有時不穩定)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    
    # 使用 resample 功能將 15T 轉成 60T (即 1小時)
    resample_df = df.resample('60T').agg({
        'open': 'first',
        'max': 'max',
        'min': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna() # 移除沒有交易的時間段（如半夜）

    resample_df = resample_df.reset_index()
    resample_df = resample_df.rename(columns={
        'open': 'Open', 'max': 'High', 'min': 'Low', 'close': 'Close', 'volume': 'Volume'
    })
    return resample_df

# 3. 介面控制
st.sidebar.title("🕹️ 60分K 回測控制")
# 提醒：分K資料建議日期不要選太久以前
start_d = st.sidebar.date_input("開始日期", datetime.now() - timedelta(days=30))

if st.sidebar.button("下一根 ➡️"):
    st.session_state.idx += 1
if st.sidebar.button("重置回測 ⏪"):
    st.session_state.idx = 100

# 4. 執行與顯示
try:
    # 呼叫修正後的函式
    raw_df = load_60min_data(start_d.strftime('%Y-%m-%d'))
    
    if len(raw_df) == 0:
        st.warning("查無資料，請縮短日期範圍（例如最近 30 天內）再試一次。")
        st.stop()

    view_df = raw_df.iloc[:st.session_state.idx]

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
        title=f"台指期 60分鐘K線圖 (目前時間: {view_df.iloc[-1]['date']})"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 5. 數據面板
    k = view_df.iloc[-1]
    c1, c2, c3 = st.columns(3)
    c1.metric("當前時間", k['date'].strftime('%m/%d %H:%M'))
    c2.metric("收盤價", f"{int(k['Close'])}")
    c3.metric("進度", f"第 {st.session_state.idx} 根")

except Exception as e:
    st.error(f"捕捉到錯誤: {e}")
    st.info("提示：這可能是因為 FinMind API 暫時無法提供該時段的分鐘資料。請嘗試更換日期。")
