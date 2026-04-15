import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="R&D Fund Dashboard", layout="wide")
st.title("📊 R&D Fund Master Dashboard")

# Ép kết nối tìm đúng key 'gsheets' trong secrets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Lỗi kết nối Secrets: {e}")
    st.stop()

years = ["2026", "2025"]
selected_year = st.sidebar.selectbox("📅 Chọn năm:", years)

@st.cache_data(ttl=600)
def load_data(year):
    # Đọc dữ liệu, tiêu đề ở dòng 2
    df = conn.read(worksheet=year, header=1)
    df = df.iloc[0:45, 1:14]
    df.columns = ["Name", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    df = df.dropna(subset=["Name"])
    df = df[~df["Name"].str.contains("Full Name|Total|Tổng cộng|Tên", na=False)]
    
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('đ', ''), errors='coerce').fillna(0)
    return df

try:
    data = load_data(selected_year)
    
    # Vẽ biểu đồ
    collected = data.iloc[:, 1:].sum()
    fig = go.Figure(data=[
        go.Bar(name='Đã đóng', x=collected.index, y=collected.values, marker_color='#1e3a8a'),
        go.Bar(name='Còn thiếu', x=collected.index, y=[max(0, len(data)*100000 - v) for v in collected.values], marker_color='#f59e0b')
    ])
    fig.update_layout(barmode='stack', title=f"Tiến độ quỹ năm {selected_year}")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(data, use_container_width=True)

except Exception as e:
    st.warning(f"Đang chờ dữ liệu: {e}")
