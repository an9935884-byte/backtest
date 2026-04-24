import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from FinMind.data import DataLoader
from datetime import datetime, timedelta

st.set_page_config(page_title="台指期專業回測版", layout="wide")

# 1. 記憶進度
if 'idx' not in st.session_state:
    st.session_state.idx = 50

# 2. 抓取資料並嚴格校正欄位
@st.cache_data
def load_data_v2(start_date):
    dl = DataLoader()
    # 抓取台指期日線
    df = dl.taiwan_futures_daily(futures_id='TX', start_date=start_date)
    
    if df.empty:
        return pd.DataFrame()
        
    # 關鍵：轉換格式並確保數字類型正確
    df['date'] = pd.to_datetime(df['date'])
    
    # 校正：FinMind 的欄位名稱有時是 open, max, min, close
    df = df.rename(columns={
        'open': 'Open', 
        'max': 'High', 
        'min': 'Low', 
        'close': 'Close', 
        'volume': 'Volume'
    })
    
    # 強制將價格轉換為浮點數，避免繪圖錯誤
    for col in ['Open', 'High', 'Low', 'Close']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 依照日期排序，避免圖形連線亂跳
    df = df.sort_values('date').reset_index(drop=True)
    return df

# 3. 介面控制
st.sidebar.title("🕹️ 交易回測控制")
start_d = st.sidebar.date_input("開始日期", datetime.now() - timedelta(days=365))

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("⬅️ 上一根"):
        if st.session_state.idx > 1: st.session_state.idx -= 1
with col2:
    if st.button("➡️ 下一根"):
        st.session_state.idx += 1

if st.sidebar.button("⏪ 重置"):
    st.session_state.idx = 50

# 4. 繪製圖表
df = load_data_v2(start_d.strftime('%Y-%m-%d'))

if not df.empty:
    # 避免索引超出範圍
    current_max = len(df)
    if st.session_state.idx > current_max:
        st.session_state.idx = current_max
        
    view_df = df.iloc[:st.session_state.idx]

    # 繪製 K 線圖
    fig = go.Figure(data=[go.Candlestick(
        x=view_df['date'],
        open=view_df['Open'],
        high=view_df['High'],
        low=view_df['Low'],
        close=view_df['Close'],
        increasing_line_color='#FF3333', # 漲：亮紅色
        increasing_fill_color='#FF3333',
        decreasing_line_color='#00AA00', # 跌：亮綠色
        decreasing_fill_color='#00AA00',
        line_width=1
    )])
    
    # 5. 優化圖表視覺（避免圖形長得奇怪）
    fig.update_layout(
        xaxis_rangeslider_visible=False, # 關閉下方滑桿，讓主圖比例正常
        height=700, 
        template="plotly_dark",
        xaxis=dict(type='category', nticks=20), # 將 X 軸設為類別，消除假日造成的空隙
        yaxis=dict(autorange=True, fixedrange=False), # 讓 Y 軸隨資料縮放
        margin=dict(t=30, b=30, l=10, r=10)
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # 數據資訊
    k = view_df.iloc[-1]
    st.info(f"📅 日期: {k['date'].date()} | 開: {k['Open']} | 高: {k['High']} | 低: {k['Low']} | 收: {int(k['Close'])}")
else:
    st.warning("目前沒有資料。")
