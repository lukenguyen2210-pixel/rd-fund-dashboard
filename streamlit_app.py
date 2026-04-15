import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.graph_objects as go

# 1. Cấu hình trang
st.set_page_config(page_title="R&D Fund Dashboard", layout="wide", page_icon="📊")

st.title("📊 R&D Fund Master Dashboard")
st.markdown("---")

# 2. Khởi tạo kết nối 
# Code này sẽ thử tìm cả 2 cách đặt tên thông dụng trong Secrets
try:
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        conn = st.connection("gsheets", type=GSheetsConnection)
    else:
        # Nếu bro đặt tên là [gsheets] thay vì [connections.gsheets]
        conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Lỗi cấu hình Secrets: {e}")
    st.stop()

# 3. Sidebar chọn năm
years = ["2026", "2025"]
selected_year = st.sidebar.selectbox("📅 Chọn năm báo cáo:", years)

@st.cache_data(ttl=600)
def load_and_clean_data(year):
    # Đọc dữ liệu từ worksheet, tiêu đề ở dòng 2 (header=1)
    df = conn.read(worksheet=year, header=1)
    
    # Lấy vùng dữ liệu chính: Cột B (Name) đến cột N
    df = df.iloc[0:45, 1:14]
    
    # Đặt lại tên cột
    df.columns = ["Name", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    
    # Làm sạch: Bỏ dòng trống Name hoặc dòng tiêu đề lặp lại
    df = df.dropna(subset=["Name"])
    df = df[~df["Name"].str.contains("Full Name|Total|Tổng cộng|Tên", na=False)]
    
    # Ép kiểu dữ liệu số
    for col in df.columns[1:]:
        df[col] = df[col].astype(str).str.replace(',', '').str.replace('đ', '').str.strip()
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

try:
    # 4. Tải dữ liệu
    data = load_and_clean_data(selected_year)
    
    # 5. Tính toán metrics
    total_members = len(data)
    monthly_fee = 100000 
    collected_series = data.iloc[:, 1:].sum()
    expected_per_month = total_members * monthly_fee
    
    # 6. Hiển thị Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tổng thành viên", f"{total_members} người")
    with col2:
        st.metric("Tổng quỹ hiện tại", f"{collected_series.sum():,.0f} đ")
    with col3:
        st.metric("Tháng gần nhất", f"{collected_series.iloc[-1]:,.0f} đ")

    # 7. Vẽ biểu đồ Navy & Orange
    fig = go.Figure(data=[
        go.Bar(name='Đã đóng', x=collected_series.index, y=collected_series.values, marker_color='#1e3a8a'),
        go.Bar(name='Còn thiếu', x=collected_series.index, y=[max(0, expected_per_month - v) for v in collected_series.values], marker_color='#f59e0b')
    ])

    fig.update_layout(barmode='stack', title=f"Tiến độ đóng quỹ năm {selected_year}", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # 8. Bảng chi tiết
    with st.expander("🔍 Xem chi tiết thành viên"):
        st.dataframe(data, use_container_width=True)

except Exception as e:
    st.warning(f"Chưa lấy được dữ liệu: {e}")
    st.info("Bro kiểm tra lại: \n1. Tên tab trong Sheets có đúng là '2026' chưa? \n2. Đã nhấn Save trong phần Secrets chưa?")
