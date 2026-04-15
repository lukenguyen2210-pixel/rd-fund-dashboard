import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="R&D Fund Master Pro", layout="wide")

SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"
STANDARD_FEE = 100000
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]

def get_data(year_choice):
    # Lấy dữ liệu Thu - Range B3:N43 (Bỏ qua dòng header rác của Sheets)
    url_income = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={year_choice}&range=B3:N43"
    df_inc = pd.read_csv(url_income, header=None) # Đọc không header để tự định nghĩa
    
    # Gán lại tên cột chuẩn để không bao giờ bị KeyError
    df_inc.columns = ["Full Name"] + MONTHS
    
    # Lọc thành viên rác
    exclude = ["SUM", "Tổng cộng", "Tên NV", "Total", "TOTAL"]
    df_inc = df_inc.dropna(subset=["Full Name"])
    df_inc = df_inc[~df_inc["Full Name"].astype(str).str.contains('|'.join(exclude), case=False, na=False)]
    
    # Ép kiểu số cho dữ liệu đóng tiền
    for col in MONTHS:
        df_inc[col] = df_inc[col].astype(str).str.replace(',', '').str.replace(' ', '')
        df_inc[col] = pd.to_numeric(df_inc[col], errors='coerce').fillna(0)
    
    # Lấy dữ liệu Chi (Q3:S43)
    url_exp = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={year_choice}&range=Q3:S43"
    df_ex = pd.read_csv(url_exp, header=None)
    if not df_ex.empty:
        df_ex.columns = ['Date', 'Amount', 'Content']
        df_ex['Amount'] = pd.to_numeric(df_ex['Amount'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        df_ex = df_ex[df_ex['Amount'] > 0]

    return df_inc, df_ex

st.title("📊 R&D Fund Master Pro")
year = st.sidebar.selectbox("Năm tài chính:", ["2026", "2025"])

try:
    df_members, df_expense = get_data(year)
    
    # Hiển thị Metrics
    total_income = df_members[MONTHS].sum().sum()
    total_expense = df_expense['Amount'].sum() if not df_expense.empty else 0
    balance = total_income - total_expense
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng Thu", f"{total_income:,.0f} VND")
    c2.metric("Tổng Chi", f"{total_expense:,.0f} VND")
    c3.metric("Số dư hiện tại", f"{balance:,.0f} VND")

    # Biểu đồ tiến độ
    st.subheader(f"Tiến độ thu quỹ (Năm {year})")
    monthly_collected = df_members[MONTHS].sum()
    expected_per_month = len(df_members) * STANDARD_FEE
    
    fig = go.Figure(data=[
        go.Bar(name='Đã thu', x=MONTHS, y=monthly_collected, marker_color='#1e3a8a'),
        go.Bar(name='Còn thiếu', x=MONTHS, y=[max(0, expected_per_month - v) for v in monthly_collected], marker_color='#f59e0b')
    ])
    fig.update_layout(barmode='stack', height=350, margin=dict(l=0, r=0, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # Bảng chi tiết - Nơi bị lỗi KeyError 'Apr'
    st.subheader("Chi tiết đóng quỹ")
    df_display = df_members.copy()
    for col in MONTHS:
        # Chốt hạ: Cứ có đóng tiền là tick
        df_display[col] = df_display[col].apply(lambda x: "✔" if x > 0 else "-")
    
    # Chỉ hiển thị những cột cần thiết
    st.dataframe(df_display[["Full Name"] + MONTHS], use_container_width=True, height=450)

    # Nhật ký chi tiêu
    st.subheader("Nhật ký chi tiêu")
    if not df_expense.empty:
        st.dataframe(df_expense, use_container_width=True)
    else:
        st.info("Năm này chưa có dữ liệu chi tiêu.")

except Exception as e:
    st.error(f"Phát sinh lỗi: {e}")
