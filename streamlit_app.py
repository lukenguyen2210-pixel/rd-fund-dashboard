import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="R&D Fund Dashboard", layout="wide")
st.title("📊 R&D Fund Dashboard")

# Thêm nút clear cache để app luôn nhận data mới nhất
if st.sidebar.button("🔄 Làm mới dữ liệu"):
    st.cache_data.clear()

try:
    # Kết nối tự động lấy từ [connections.gsheets]
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    selected_year = st.sidebar.selectbox("📅 Chọn năm:", ["2026", "2025"])

    # Đọc dữ liệu (header dòng 2)
    df = conn.read(worksheet=selected_year, header=1)
    
    if df is not None:
        st.success(f"✅ Đã tải dữ liệu năm {selected_year}")
        # Hiển thị bảng từ cột B đến N
        st.dataframe(df.iloc[:, 1:14], use_container_width=True)
    else:
        st.warning("Sheet trống hoặc không tìm thấy tab.")

except Exception as e:
    # Hiện lỗi chi tiết để debug nếu còn bị PEM
    st.error(f"Lỗi hệ thống: {str(e)}")
