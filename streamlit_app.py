import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="R&D Fund Dashboard", layout="wide")

# Lấy URL từ secrets
if "gsheets" in st.secrets:
    full_url = st.secrets["gsheets"]["public_url"]
    # Tách lấy ID file để tránh lỗi 400 (đoạn mã nằm giữa /d/ và /edit)
    try:
        sheet_id = full_url.split("/d/")[1].split("/")[0]
        clean_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit#gid=0"
    except:
        clean_url = full_url
else:
    st.error("Thiếu cấu hình Secrets!")
    st.stop()

conn = st.connection("gsheets", type=GSheetsConnection)

years = ["2026", "2025"]
selected_year = st.sidebar.selectbox("Chọn năm:", years)

def load_data(year):
    # Dùng clean_url đã được chuẩn hóa ID
    df = conn.read(spreadsheet=clean_url, worksheet=year, header=1)
    
    # Lấy vùng dữ liệu: Cột B (index 1) đến cột N (index 13)
    df = df.iloc[0:41, 1:14]
    df.columns = ["Name", "Th10", "Th11", "Th12", "Th1", "Th2", "Th3", "Th4", "Th5", "Th6", "Th7", "Th8", "Th9"]
    
    # Dọn dẹp dữ liệu
    df = df.dropna(subset=["Name"])
    df = df[~df["Name"].str.contains("Full Name|Total|Tổng|Tên", na=False)]
    
    # Ép kiểu số (xử lý dấu phẩy và chữ đ)
    for col in df.columns[1:]:
        df[col] = df[col].astype(str).str.replace(',', '').str.replace('đ', '').str.strip()
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

try:
    data = load_data(selected_year)
    
    # Tính toán
    collected = data.iloc[:, 1:].sum()
    expected = len(data) * 100000 # 100k mỗi người
    remaining = [max(0, expected - v) for v in collected]
    
    # Vẽ biểu đồ Navy & Orange
    fig = go.Figure(data=[
        go.Bar(name='Đã đóng', x=collected.index, y=collected.values, marker_color='#1e3a8a'),
        go.Bar(name='Còn thiếu', x=collected.index, y=remaining, marker_color='#f59e0b')
    ])
    fig.update_layout(barmode='stack', title=f"Tình hình quỹ R&D {selected_year} (Dự kiến: {expected:,.0f}đ/tháng)")
    
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Bảng chi tiết")
    st.dataframe(data, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi: {e}")
    st.info("Kiểm tra lại tên Sheet trong file Excel có đúng là '2026' và '2025' chưa nhé bro.")
