import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="R&D Fund Dashboard", layout="wide")

# Ép code dùng thẳng dữ liệu từ [gsheets] trong Secrets
try:
    conn = st.connection("gsheets", 
                         type=GSheetsConnection, 
                         spreadsheet=st.secrets["gsheets"]["spreadsheet"],
                         project_id=st.secrets["gsheets"]["project_id"],
                         private_key=st.secrets["gsheets"]["private_key"],
                         client_email=st.secrets["gsheets"]["client_email"])
    
    selected_year = st.sidebar.selectbox("📅 Chọn năm:", ["2026", "2025"])
    
    # Thử đọc data
    df = conn.read(worksheet=selected_year, header=1)
    st.success(f"Đã kết nối thành công năm {selected_year}!")
    st.dataframe(df)

except Exception as e:
    st.error(f"Vẫn lỗi: {e}")
    st.write("Dữ liệu Secrets hiện có:", list(st.secrets.keys()))
