import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="R&D Fund Master", layout="wide")
st.title("📊 R&D Fund Master Pro")

# Kiểm tra xem Secrets có tồn tại không để tránh lỗi đỏ
if "gsheets" in st.secrets:
    sheet_url = st.secrets["gsheets"]["public_url"]
else:
    st.error("Chưa tìm thấy URL file Sheets trong phần Secrets của Streamlit Cloud!")
    st.stop()

conn = st.connection("gsheets", type=GSheetsConnection)

# Dựa trên ảnh của bro, mình lấy 2 năm này
years = ["2026", "2025"] 
selected_year = st.sidebar.selectbox("Chọn năm xem báo cáo:", years)

def load_data(year):
    # Header=1 vì tiêu đề nằm ở dòng 2 của Sheets
    df = conn.read(spreadsheet=sheet_url, worksheet=year, header=1)
    
    # Lấy từ cột B (Full Name) đến cột N (Mar 2026)
    # Trong Python index bắt đầu từ 0, nên cột B là 1, cột N là 13
    df = df.iloc[0:41, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]]
    df.columns = ["Name", "Th1", "Th2", "Th3", "Th4", "Th5", "Th6", "Th7", "Th8", "Th9", "Th10", "Th11", "Th12"]
    
    # Loại bỏ dòng không có tên
    df = df.dropna(subset=["Name"])
    df = df[~df["Name"].isin(["SUM", "TOTAL", "Tổng cộng", "Total expense"])]
    
    # Chuyển đổi dữ liệu sang số, xóa dấu phẩy nếu có
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        
    standard_fee = 100000
    monthly_collected = df.iloc[:, 1:].sum()
    monthly_expected = len(df) * standard_fee
    
    return monthly_collected, monthly_expected, df

try:
    monthly_col, monthly_exp, raw_df = load_data(selected_year)

    # Vẽ biểu đồ
    months = monthly_col.index.tolist()
    collected_vals = monthly_col.values
    remaining_vals = [max(0, monthly_exp - v) for v in collected_vals]

    fig = go.Figure(data=[
        go.Bar(name='Đã đóng', x=months, y=collected_vals, marker_color='#1e3a8a'),
        go.Bar(name='Còn thiếu', x=months, y=remaining_vals, marker_color='#f59e0b')
    ])

    fig.update_layout(barmode='stack', title=f"Báo cáo quỹ R&D năm {selected_year}", 
                      xaxis_title="Tháng", yaxis_title="Số tiền (VND)")

    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Bảng chi tiết thành viên")
    st.dataframe(raw_df, use_container_width=True)
    
except Exception as e:
    st.warning(f"Đang đợi dữ liệu hoặc có lỗi: {e}")
