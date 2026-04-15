import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="R&D Fund Dashboard", layout="wide")
st.title("📊 R&D Fund Master Pro")

# Kết nối với Service Account
conn = st.connection("gsheets", type=GSheetsConnection)

years = ["2026", "2025"]
selected_year = st.sidebar.selectbox("Chọn năm xem báo cáo:", years)

@st.cache_data(ttl=600)
def load_data(year):
    # Đọc sheet theo tên năm, tiêu đề ở dòng 2 (header=1)
    df = conn.read(worksheet=year, header=1)
    
    # Lấy từ cột B (Full Name) đến cột N (Tháng cuối)
    df = df.iloc[0:45, 1:14]
    df.columns = ["Name", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    
    # Làm sạch dữ liệu
    df = df.dropna(subset=["Name"])
    df = df[~df["Name"].str.contains("Full Name|Total|Tổng", na=False)]
    
    # Chuyển đổi số
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('đ', ''), errors='coerce').fillna(0)
    return df

try:
    data = load_data(selected_year)
    
    # Tính toán tổng hợp
    collected = data.iloc[:, 1:].sum()
    target_per_month = len(data) * 100000 
    remaining = [max(0, target_per_month - v) for v in collected]
    
    # Vẽ biểu đồ
    fig = go.Figure(data=[
        go.Bar(name='Đã đóng', x=collected.index, y=collected.values, marker_color='#1e3a8a'),
        go.Bar(name='Còn thiếu', x=collected.index, y=remaining, marker_color='#f59e0b')
    ])
    fig.update_layout(barmode='stack', title=f"Tiến độ quỹ năm {selected_year}")
    
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Bảng chi tiết đóng phí")
    st.dataframe(data, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi: {e}")
    st.info("Nhớ share file Sheets cho email: streamlit-sheets-access@analog-crossing-455502-j1.iam.gserviceaccount.com nhé!")
