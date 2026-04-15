import streamlit as st
import pandas as pd

# Cấu hình trang
st.set_page_config(page_title="R&D Fund Dashboard", layout="wide")
st.title("📊 R&D Fund Master Dashboard")

# Link file của bro
SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"

# Hàm để lấy URL tải CSV cho từng tab
def get_csv_url(sheet_id, sheet_name):
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"

try:
    # Cho phép chọn năm trực tiếp trên giao diện
    year = st.sidebar.selectbox("Chọn năm xem báo cáo:", ["2026", "2025"])
    
    # Tạo URL tải dữ liệu
    data_url = get_csv_url(SHEET_ID, year)
    
    # Đọc dữ liệu (skiprows=1 nếu dòng đầu tiên của bro là tiêu đề trống hoặc merge)
    df = pd.read_csv(data_url)
    
    st.success(f"Đã tải dữ liệu năm {year} thành công!")
    
    # Hiển thị bảng dữ liệu
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi kết nối: {e}")
    st.info("Bro nhớ kiểm tra xem đã Share file ở chế độ 'Anyone with the link' chưa nhé!")
