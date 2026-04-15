import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="R&D Fund Dashboard", layout="wide")

try:
    # Kết nối thẳng bằng cách lấy các biến ở cấp ngoài cùng của Secrets
    conn = st.connection(
        "gsheets",
        type=GSheetsConnection,
        project_id=st.secrets["project_id"],
        private_key=st.secrets["private_key"],
        client_email=st.secrets["client_email"],
        token_uri=st.secrets["token_uri"]
    )

    url = "https://docs.google.com/spreadsheets/d/1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0/edit"
    
    # Lấy dữ liệu năm 2026
    df = conn.read(spreadsheet=url, worksheet="2026", header=1)
    
    st.success("Đã kết nối thành công!")
    st.dataframe(df)

except Exception as e:
    st.error(f"Vẫn lỗi: {e}")
