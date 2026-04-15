import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Cấu hình giao diện
st.set_page_config(page_title="R&D Fund Dashboard", layout="wide")

st.markdown("# 📊 R&D Fund Dashboard")
st.info("Dữ liệu được cập nhật trực tiếp từ Google Sheets")

# Khởi tạo kết nối (Tự tìm [connections.gsheets] trong Secrets)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Lỗi khởi tạo kết nối: {e}")
    st.stop()

# Chọn năm từ Sidebar
selected_year = st.sidebar.selectbox("📅 Chọn năm:", ["2026", "2025"])

@st.cache_data(ttl=300) # Lưu cache 5 phút
def get_data(year):
    # Đọc worksheet theo tên năm, tiêu đề ở dòng 2 (index 1)
    return conn.read(worksheet=year, header=1)

try:
    df = get_data(selected_year)
    
    if df is not None:
        st.success(f"✅ Đã tải dữ liệu năm {selected_year}")
        
        # Tiền xử lý: Lấy vùng dữ liệu từ cột B đến cột N
        # (Chỉnh lại iloc nếu số dòng/cột thực tế của bro khác đi một chút)
        data_display = df.iloc[0:45, 1:14] 
        
        # Hiển thị bảng dữ liệu
        st.dataframe(data_display, use_container_width=True)
        
    else:
        st.warning("Không tìm thấy dữ liệu trong Worksheet này.")

except Exception as e:
    st.error(f"Lỗi khi đọc dữ liệu: {e}")
    st.markdown("""
    **Hướng dẫn xử lý nhanh:**
    1. Đảm bảo tên tab trong Google Sheets đúng là `2026` hoặc `2025`.
    2. Đảm bảo đã dán `url` chính xác vào Secrets.
    3. Nhấn **Manage app** -> **Reboot app** để cập nhật cấu hình mới nhất.
    """)
