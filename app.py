import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from FinMind.data import DataLoader
from datetime import datetime, timedelta

st.set_page_config(page_title="台指期專業回測版", layout="wide")

# 1. 記憶進度
if 'idx' not in st.session_state:
    st.session_state.idx = 50

# 2. 抓取資料並嚴格檢查
@st.cache_data
def load_data_final(start_date):
    dl = DataLoader()
    df = dl.taiwan_futures_daily(futures_id='TX', start_date=start_date)
    
    if df is None or df.empty:
        return pd.DataFrame()
        
    # 統一轉換為數字類型，出錯的轉為 NaN
    df['open'] = pd.to_numeric(df['open'], errors='coerce')
    df['max'] = pd.to_numeric(df['max'], errors='coerce')
    df['min'] = pd.to_numeric(df['min'], errors='coerce')
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    
    # 刪除任何含有空值 (NaN) 的列，確保繪圖不崩潰
    df = df.dropna(subset=['open', 'max', 'min', 'close'])
    
    # 日期處理與排序
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    # 重新命名欄位以便讀取
    df = df.rename(columns={
        'open': 'Open', 'max': 'High', 'min': 'Low', 'close': 'Close', 'volume': 'Volume'
    })
    return df

# 3. 介面控制
st.sidebar.title("🕹️ 回測控制")
start_d = st.sidebar.date_input("開始日期", datetime.now() - timedelta(days=365))

# 控制按鈕
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("⬅️ 上一根"):
        if st.session_state.idx > 1: st.session_state.idx -= 1
with col2:
    if st.button("➡️ 下一根"):
        st.session_state.idx += 1

if st.sidebar.button("⏪ 重置進度"):
    st.session_state.idx = 50

# 4. 取得資料並切片
all_df = load_data_final(start_d.strftime('%Y-%m-%d'))

if not all_df.empty:
    # 確保索引不會超過資料總長度
    if st.session_state.idx > len(all_df):
        st.session_state.idx = len(all_df)
    
    # 取得目前要顯示的部分資料
    view_df = all_df.iloc[:st.session_state.idx].copy()

    # 5. 繪製圖表 (加上錯誤捕捉保護)
    try:
        fig = go.Figure()
        
        # 建立 K 線圖物件
        # 關鍵：先確保 view_df['date'] 轉成字串，避免 Plotly 處理時間物件時崩潰
        fig.add_trace(go.Candlestick(
            x=view_df['date'].dt.strftime('%Y-%m-%d'), 
            open=view_df['Open'],
            high=view_df['High'],
            low=view_df['Low'],
            close=view_df['Close'],
            increasing_line_color='red',
            decreasing_line_color='green',
            name="TX"
        ))

        fig.update_layout(
            xaxis_rangeslider_visible=False,
            height=700,
            template="plotly_dark",
            # 解決假日空隙與奇怪圖形的關鍵：
            xaxis=dict(type='category', categoryorder='category ascending'),
            yaxis=dict(title="價格", autorange=True, fixedrange=False)
        )

        st.plotly_chart(fig, use_container_width=True)

        # 6. 狀態顯示
        last_k = view_df.iloc[-1]
        st.success(f"目前位置：{last_k['date'].date()} | 第 {st.session_state.idx} 根 K 線")

    except Exception as e:
        st.error(f"繪圖引擎發生錯誤: {e}")
else:
    st.warning("抓不到資料，請更換日期範圍再試一次。")
