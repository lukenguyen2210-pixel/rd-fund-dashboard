import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="R&D Fund Master Pro", layout="wide")

SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"
STANDARD_FEE = 100000
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]

def get_data(year_choice):
    # --- 1. LẤY DỮ LIỆU THU (Dải ô B3:N43) ---
    url_income = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={year_choice}&range=B3:N43"
    df_inc = pd.read_csv(url_income, header=None)
    df_inc.columns = ["Full Name"] + MONTHS
    
    # Lọc dòng gộp tiêu đề hoặc dòng trống
    if not df_inc.empty:
        # Nếu dòng đầu chứa quá nhiều khoảng trắng (lỗi gộp tên), bỏ qua dòng đó
        if str(df_inc.iloc[0, 0]).count(" ") > 5:
            df_inc = df_inc.iloc[1:].reset_index(drop=True)

    exclude = ["SUM", "Tổng cộng", "Tên NV", "Total", "TOTAL", "nan"]
    df_inc = df_inc.dropna(subset=["Full Name"])
    df_inc = df_inc[~df_inc["Full Name"].astype(str).str.contains('|'.join(exclude), case=False, na=False)]
    
    # Ép kiểu số cho 12 tháng (Xóa dấu phẩy, khoảng trắng)
    for col in MONTHS:
        df_inc[col] = df_inc[col].astype(str).str.replace(',', '').str.replace(' ', '')
        df_inc[col] = pd.to_numeric(df_inc[col], errors='coerce').fillna(0)
    
    # --- 2. LẤY DỮ LIỆU CHI (Dải ô Q3:S43) ---
    # Lưu ý: Lấy từ cột Q (Ngày), R (Số tiền), S (Nội dung)
    url_exp = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={year_choice}&range=Q3:S43"
    df_ex = pd.read_csv(url_exp, header=None)
    
    if not df_ex.empty:
        df_ex.columns = ['Date', 'Amount', 'Content']
        # Xử lý cột số tiền chi
        df_ex['Amount'] = df_ex['Amount'].astype(str).str.replace(',', '').str.replace(' ', '')
        df_ex['Amount'] = pd.to_numeric(df_ex['Amount'], errors='coerce').fillna(0)
        # Chỉ lấy các dòng thực sự có chi tiền
        df_ex = df_ex[df_ex['Amount'] > 0]

    return df_inc, df_ex

st.title("📊 R&D Fund Master Pro")
year = st.sidebar.selectbox("Năm tài chính:", ["2026", "2025"])

try:
    df_members, df_expense = get_data(year)
    
    # --- TÍNH TOÁN ---
    total_income = df_members[MONTHS].sum().sum()
    total_expense = df_expense['Amount'].sum() if not df_expense.empty else 0
    balance = total_income - total_expense
    
    # --- HIỂN THỊ METRICS ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng Thu (Income)", f"{total_income:,.0f} VND")
    c2.metric("Tổng Chi (Expense)", f"{total_expense:,.0f} VND")
    c3.metric("Số dư (Balance)", f"{balance:,.0f} VND")

    # --- BIỂU ĐỒ TIẾN ĐỘ ---
    st.subheader(f"Tiến độ đóng quỹ (Năm {year})")
    monthly_collected = df_members[MONTHS].sum()
    expected_per_month = len(df_members) * STANDARD_FEE
    
    fig = go.Figure(data=[
        go.Bar(name='Đã thu', x=MONTHS, y=monthly_collected, marker_color='#1e3a8a'),
        go.Bar(name='Còn thiếu', x=MONTHS, y=[max(0, expected_per_month - v) for v in monthly_collected], marker_color='#f59e0b')
    ])
    fig.update_layout(barmode='stack', height=350, margin=dict(l=0, r=0, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # --- BẢNG CHI TIẾT ĐÓNG QUỸ (Fix STT và Tick) ---
    st.subheader("Chi tiết đóng quỹ")
    df_display = df_members.copy()
    
    # Tạo dấu tick
    for col in MONTHS:
        df_display[col] = df_display[col].apply(lambda x: "✔" if x > 0 else "-")
    
    # Ép STT bắt đầu từ 1
    df_display.index = range(1, len(df_display) + 1)
    df_display.index.name = "STT"
    
    # Hiển thị bảng kèm STT
    st.dataframe(df_display[["Full Name"] + MONTHS], use_container_width=True, height=450)

    # --- NHẬT KÝ CHI TIÊU (Fix STT và Hiển thị) ---
    st.subheader("Nhật ký chi tiêu (Expense Log)")
    if not df_expense.empty:
        df_exp_show = df_expense.copy()
        # Ép STT cho bảng chi tiêu
        df_exp_show.index = range(1, len(df_exp_show) + 1)
        df_exp_show.index.name = "STT"
        
        # Định dạng lại cột tiền cho dễ nhìn trong bảng
        df_exp_show['Amount'] = df_exp_show['Amount'].apply(lambda x: f"{x:,.0f}")
        st.dataframe(df_exp_show, use_container_width=True)
    else:
        st.info(f"Năm {year} chưa có dữ liệu chi tiêu hoặc sai định dạng ô Số tiền.")

except Exception as e:
    st.error(f"Lỗi hệ thống: {e}")
