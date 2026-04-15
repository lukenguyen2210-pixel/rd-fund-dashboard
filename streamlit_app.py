import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.title("📊 R&D Fund Master")

# Lấy URL từ Secrets
url = st.secrets["gsheets"]["public_url"]
conn = st.connection("gsheets", type=GSheetsConnection)

# Đọc thử sheet 2026
try:
    # Chỉ dùng tham số spreadsheet và worksheet, bỏ hết các thứ khác
    df = conn.read(spreadsheet=url, worksheet="2026")
    
    st.success("Kết nối thành công!")
    st.write("Dữ liệu thô từ Excel của bro:")
    st.dataframe(df)
    
except Exception as e:
    st.error(f"Lỗi rồi bro ơi: {e}")
