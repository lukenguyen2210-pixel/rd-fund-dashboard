import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.graph_objects as go

# Cấu hình trang
st.set_page_config(page_title="R&D Fund Master Pro", layout="wide", page_icon="📊")

st.markdown("# 📊 R&D Fund Master Pro")
st.markdown("---")

# Kết nối lấy từ Secrets [gsheets]
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Lỗi kết nối: {e}")
    st.stop()

# Sidebar chọn năm
selected_year = st.sidebar.selectbox("📅 Chọn năm xem báo cáo:", ["2026", "2025"])

@st.cache_data(ttl=600)
def load_and_clean_data(year):
    # Đọc dữ liệu từ sheet tương ứng, header ở dòng 2 (index 1)
    df = conn.read(worksheet=year, header=1)
    
    # Lấy vùng dữ liệu: Cột B (Name) đến cột N (Tháng 9)
    df = df.iloc[0:45, 1:14]
    df.columns = ["Name", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    
    # Làm sạch dữ liệu
    df = df.dropna(subset=["Name"])
    df = df[~df["Name"].str.contains("Full Name|Total|Tổng cộng|Tên", na=False)]
    
    # Chuyển đổi số
    for col in df.columns[1:]:
        df[col] = df[col].astype(str).str.replace(',', '').str.replace('đ', '').str.strip()
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

try:
    data = load_and_clean_data(selected_year)
    
    # Tính toán chỉ số
    total_members = len(data)
    collected_series = data.iloc[:, 1:].sum()
    target_monthly = total_members * 100000 # Giả định mức đóng 100k
    
    # Hiển thị Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng thành viên", f"{total_members} người")
    c2.metric("Tổng quỹ tích lũy", f"{collected_series.sum():,.0f} đ")
    c3.metric("Tháng gần nhất", f"{collected_series.iloc[-1]:,.0f} đ")

    # Vẽ biểu đồ Navy & Orange
    fig = go.Figure(data=[
        go.Bar(name='Đã đóng', x=collected_series.index, y=collected_series.values, marker_color='#1e3a8a'),
        go.Bar(name='Còn thiếu', x=collected_series.index, 
               y=[max(0, target_monthly - v) for v in collected_series.values], 
               marker_color='#f59e0b')
    ])
    fig.update_layout(barmode='stack', title=f"Tiến độ đóng quỹ năm {selected_year}", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # Hiển thị bảng
    with st.expander("🔍 Chi tiết danh sách"):
        st.dataframe(data, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi xử lý dữ liệu: {e}")
    st.info("Check lại tên Sheet trong file Google Sheets xem có đúng là '2026' chưa bro.")
