import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="R&D Fund Dashboard", layout="wide")

st.title("📊 R&D Fund Master Pro")

# Kết nối: Streamlit sẽ tự tìm mục [connections.gsheets] trong Secrets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    selected_year = st.sidebar.selectbox("📅 Chọn năm:", ["2026", "2025"])

    # Đọc dữ liệu - Header ở dòng 2 (index 1)
    # Không cần truyền URL ở đây vì nó đã nằm trong Secrets rồi
    df = conn.read(worksheet=selected_year, header=1)
    
    if df is not None:
        st.success(f"✅ Đã kết nối thành công năm {selected_year}!")
        
        # Làm sạch dữ liệu sơ bộ để check
        df_clean = df.iloc[0:45, 1:14] # Lấy từ cột B đến N
        st.dataframe(df_clean, use_container_width=True)
    else:
        st.error("Không tìm thấy dữ liệu trong Sheet.")

except Exception as e:
    st.error(f"❌ Lỗi: {e}")
    st.info("Bro kiểm tra lại 2 thứ: \n1. File Sheets đã Share 'Anyone with link' chưa? \n2. Tên tab có đúng là '2026' (không có dấu cách thừa) không?")
