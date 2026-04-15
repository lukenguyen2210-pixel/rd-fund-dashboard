import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import json

st.set_page_config(page_title="R&D Fund Dashboard", layout="wide")

# Bước phá băng: Tự parse JSON từ Secrets
try:
    info = json.loads(st.secrets["GCP_JSON_CREDENTIALS"])
    
    # Kết nối bằng cách truyền trực tiếp dict đã parse
    conn = st.connection("gsheets", type=GSheetsConnection, **info)
    
    selected_year = st.sidebar.selectbox("📅 Chọn năm:", ["2026", "2025"])
    
    # URL file sheet của bro
    sheet_url = "https://docs.google.com/spreadsheets/d/1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0/edit"
    
    df = conn.read(spreadsheet=sheet_url, worksheet=selected_year, header=1)
    st.dataframe(df)

except Exception as e:
    st.error(f"Lỗi hệ thống: {e}")
