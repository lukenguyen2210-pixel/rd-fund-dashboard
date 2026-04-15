import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("📊 R&D Fund Dashboard")

# Chỉ cần 1 dòng này để kết nối, nó sẽ tự lấy Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

selected_year = st.sidebar.selectbox("📅 Chọn năm:", ["2026", "2025"])

try:
    # Đọc data trực tiếp
    df = conn.read(worksheet=selected_year, header=1)
    st.dataframe(df.iloc[:, 1:14], use_container_width=True)
except Exception as e:
    st.error(f"Lỗi: {e}")
