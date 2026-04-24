import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from FinMind.data import DataLoader
from datetime import datetime, timedelta

st.set_page_config(page_title="台指期逐根回測", layout="wide")

# 1. 記憶進度 (Session State)
if 'idx' not in st.session_state:
    st.session_state.idx = 50

# 2. 抓取資料
@st.cache_data
def load_data(start, end):
    dl = DataLoader()
    df = dl.taiwan_futures_daily(futures_id='TX', start_date=start, end_date=end)
    df['date'] = pd.to_datetime(df['date'])
    return df.rename(columns={'open':'Open','max':'High','min':'Low','close':'Close','volume':'Volume'})

# 3. 介面控制
st.sidebar.title("控制台")
start_d = st.sidebar.date_input("開始日期", datetime.now() - timedelta(days=365))

if st.sidebar.button("下一根 ➡️"):
    st.session_state.idx += 1
if st.sidebar.button("重置回測 ⏪"):
    st.session_state.idx = 50

# 4. 顯示圖表
raw_df = load_data(start_d.strftime('%Y-%m-%d'), datetime.now().strftime('%Y-%m-%d'))
view_df = raw_df.iloc[:st.session_state.idx]

fig = go.Figure(data=[go.Candlestick(
    x=view_df['date'], open=view_df['Open'], high=view_df['High'],
    low=view_df['Low'], close=view_df['Close'],
    increasing_line_color='red', decreasing_line_color='green'
)])
fig.update_layout(xaxis_rangeslider_visible=False, height=600, template="plotly_dark")
st.plotly_chart(fig, use_container_width=True)

# 5. 數據呈現
k = view_df.iloc[-1]
st.write(f"目前日期：{k['date'].date()} | 收盤：{k['Close']}")
