import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.graph_objects as go

# 1. Cấu hình trang
st.set_page_config(page_title="R&D Fund Dashboard", layout="wide", page_icon="📊")

st.title("📊 R&D Fund Master Dashboard")
st.markdown("---")

# 2. Khởi tạo kết nối (Sẽ tự lấy info từ [connections.gsheets] trong Secrets)
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. Sidebar chọn năm
years = ["2026", "2025"]
selected_year = st.sidebar.selectbox("📅 Chọn năm báo cáo:", years)
st.sidebar.markdown(f"**Trạng thái:** Đang kết nối dữ liệu năm {selected_year}...")

@st.cache_data(ttl=600)
def load_and_clean_data(year):
    # Đọc dữ liệu từ worksheet tương ứng, tiêu đề nằm ở dòng 2 (header=1)
    df = conn.read(worksheet=year, header=1)
    
    # Lấy vùng dữ liệu chính: Cột B (Name) đến cột N (Tháng cuối cùng)
    # iloc[dòng_bắt_đầu:dòng_kết_thúc, cột_bắt_đầu:cột_kết_thúc]
    df = df.iloc[0:45, 1:14]
    
    # Đặt lại tên cột cho dễ quản lý
    df.columns = ["Name", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    
    # Làm sạch: Bỏ dòng trống Name hoặc dòng tiêu đề lặp lại
    df = df.dropna(subset=["Name"])
    df = df[~df["Name"].str.contains("Full Name|Total|Tổng cộng|Tên", na=False)]
    
    # Ép kiểu dữ liệu các cột tháng về số (loại bỏ dấu phẩy và chữ đ)
    for col in df.columns[1:]:
        df[col] = df[col].astype(str).str.replace(',', '').str.replace('đ', '').str.strip()
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df

try:
    # 4. Tải dữ liệu
    data = load_and_clean_data(selected_year)
    
    # 5. Tính toán tổng hợp cho Dashboard
    total_members = len(data)
    monthly_fee = 100000 # Giả định phí 100k/người
    
    collected_series = data.iloc[:, 1:].sum()
    expected_per_month = total_members * monthly_fee
    
    # 6. Hiển thị các chỉ số nhanh (Metrics)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tổng thành viên", f"{total_members} người")
    with col2:
        total_all_time = collected_series.sum()
        st.metric("Tổng quỹ hiện tại", f"{total_all_time:,.0f} đ")
    with col3:
        current_month_status = collected_series.iloc[-1]
        st.metric("Tháng gần nhất", f"{current_month_status:,.0f} đ")

    # 7. Vẽ biểu đồ Tiến độ đóng quỹ
    months = collected_series.index.tolist()
    vals_collected = collected_series.values
    vals_remaining = [max(0, expected_per_month - v) for v in vals_collected]

    fig = go.Figure(data=[
        go.Bar(name='Đã đóng', x=months, y=vals_collected, marker_color='#1e3a8a'), # Navy
        go.Bar(name='Còn thiếu', x=months, y=vals_remaining, marker_color='#f59e0b')  # Orange
    ])

    fig.update_layout(
        barmode='stack', 
        title=f"Tiến độ đóng quỹ chi tiết năm {selected_year}",
        xaxis_title="Tháng",
        yaxis_title="Số tiền (VNĐ)",
        legend_title="Trạng thái",
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    # 8. Hiển thị bảng dữ liệu chi tiết
    with st.expander("🔍 Xem bảng dữ liệu chi tiết từng thành viên"):
        st.dataframe(data.style.format(subset=data.columns[1:], formatter="{:,.0f}"), use_container_width=True)

except Exception as e:
    st.error(f"❌ Không thể hiển thị dữ liệu: {e}")
    st.info("Kiểm tra lại: \n1. File Sheets đã Share cho Email Service Account chưa?\n2. Tên Sheet trong Excel có đúng là '2026' không?")
