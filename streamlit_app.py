import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.graph_objects as go

# Cấu hình trang Dashboard
st.set_page_config(page_title="R&D Fund Master", layout="wide")
st.title("📊 R&D Fund Master Pro")

# Kết nối Google Sheets (Sử dụng URL file của bro)
# URL này bro nên cấu hình trong phần Secrets của Streamlit sau này
sheet_url = st.secrets["gsheets"]["public_url"]
conn = st.connection("gsheets", type=GSheetsConnection)

# Giả sử bro có các sheet tên là 2025, 2026...
years = ["2026", "2025"] 
selected_year = st.sidebar.selectbox("Chọn năm xem báo cáo:", years)

def load_data(year):
    # Đọc dữ liệu từ sheet năm tương ứng (Vùng B3:N43)
    df = conn.read(spreadsheet=sheet_url, worksheet=year, usecols=range(1, 14), nrows=41, header=2)
    df.columns = ["Name", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
    df = df[~df["Name"].isin(["SUM", "TOTAL", "Tổng cộng", None])]
    
    standard_fee = 100000
    monthly_collected = df.iloc[:, 1:].sum()
    monthly_expected = len(df) * standard_fee
    return monthly_collected, monthly_expected, df

monthly_col, monthly_exp, raw_df = load_data(selected_year)

# Hiển thị Biểu đồ cột chồng (Collected vs Remaining) - Màu Navy & Orange
months = monthly_col.index.tolist()
collected_vals = monthly_col.values
remaining_vals = [max(0, monthly_exp - v) for v in collected_vals]

fig = go.Figure(data=[
    go.Bar(name='Collected', x=months, y=collected_vals, marker_color='#1e3a8a'),
    go.Bar(name='Remaining', x=months, y=remaining_vals, marker_color='#f59e0b')
])

fig.update_layout(barmode='stack', title=f"Tiến độ đóng quỹ năm {selected_year}", 
                  xaxis_title="Tháng", yaxis_title="Số tiền (VND)")

st.plotly_chart(fig, use_container_width=True)
st.subheader("Bảng chi tiết đóng phí")
st.dataframe(raw_df, use_container_width=True)
