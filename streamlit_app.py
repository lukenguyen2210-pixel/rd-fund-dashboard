import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="R&D Fund Dashboard", layout="wide")

# Kiểm tra kết nối
if "gsheets" not in st.secrets:
    st.error("Lỗi: Chưa cấu hình [gsheets] trong Secrets!")
    st.stop()

url = st.secrets["gsheets"]["public_url"]
conn = st.connection("gsheets", type=GSheetsConnection)

years = ["2026", "2025"]
selected_year = st.sidebar.selectbox("Năm báo cáo:", years)

@st.cache_data(ttl=600) # Lưu nháp 10 phút để load cho nhanh
def load_data(year):
    # Sử dụng hàm read cơ bản nhất để tránh lỗi 400
    df = conn.read(spreadsheet=url, worksheet=year, header=1)
    
    # Lấy đúng vùng dữ liệu dựa trên ảnh sheet của bro
    df = df.iloc[0:41, 1:14] 
    df.columns = ["Name", "Th10", "Th11", "Th12", "Th1", "Th2", "Th3", "Th4", "Th5", "Th6", "Th7", "Th8", "Th9"]
    
    # Dọn dẹp tên và ép kiểu số
    df = df.dropna(subset=["Name"])
    df = df[~df["Name"].str.contains("Full Name|Total|Tổng", na=False)]
    
    for col in df.columns[1:]:
        df[col] = df[col].astype(str).str.replace(',', '').str.replace('đ', '')
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

try:
    data = load_data(selected_year)
    
    # Tính toán hiển thị
    collected = data.iloc[:, 1:].sum()
    expected = len(data) * 100000
    remaining = [max(0, expected - v) for v in collected]
    
    # Vẽ biểu đồ
    fig = go.Figure(data=[
        go.Bar(name='Đã đóng', x=collected.index, y=collected.values, marker_color='#1e3a8a'),
        go.Bar(name='Còn thiếu', x=collected.index, y=remaining, marker_color='#f59e0b')
    ])
    fig.update_layout(barmode='stack', title=f"Tình hình đóng quỹ năm {selected_year}")
    
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(data, use_container_width=True)

except Exception as e:
    st.error(f"Vẫn còn lỗi: {e}")
    st.info("Bro thử mở lại file Sheets, nhấn Share -> Anyone with the link lần nữa để 'refresh' quyền nhé.")
