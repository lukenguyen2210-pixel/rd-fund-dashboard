import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import json

st.set_page_config(page_title="R&D Fund Dashboard", layout="wide")

try:
    # Tự parse JSON thủ công để tránh lỗi PEM của Streamlit
    creds_dict = json.loads(st.secrets["GCP_JSON_CREDENTIALS"])
    
    # Kết nối bằng cách truyền trực tiếp thông tin đã parse
    conn = st.connection("gsheets", type=GSheetsConnection, **creds_dict)
    
    selected_year = st.sidebar.selectbox("📅 Chọn năm:", ["2026", "2025"])
    
    # Link file của bro
    url = "https://docs.google.com/spreadsheets/d/1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0/edit"
    
    df = conn.read(spreadsheet=url, worksheet=selected_year, header=1)
    st.dataframe(df)

except Exception as e:
    st.error(f"Lỗi: {e}")
