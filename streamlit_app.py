import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="R&D Fund Master Pro", layout="wide")

SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"
STANDARD_FEE = 100000
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]

def get_data(year_choice):
    # Lấy dữ liệu Thu (B3:N43)
    url_income = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={year_choice}&range=B3:N43"
    df_inc = pd.read_csv(url_income)
    
    # Lọc thành viên
    exclude = ["SUM", "Tổng cộng", "Tên NV", "Total", "TOTAL"]
    df_inc = df_inc.dropna(subset=[df_inc.columns[0]])
    df_inc = df_inc[~df_inc.iloc[:, 0].isin(exclude)]
    
    # Ép kiểu số cho các cột tháng để tránh lỗi so sánh
    for col in df_inc.columns[1:13]:
        df_inc[col] = pd.to_numeric(df_inc[col], errors='coerce').fillna(0)
    
    # Lấy dữ liệu Chi (Q3:S43)
    url_exp = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={year_choice}&range=Q3:S43"
    df_ex = pd.read_csv(url_exp)
    df_ex.columns = ['Date', 'Amount', 'Content']
    df_ex['Amount'] = pd.to_numeric(df_ex['Amount'], errors='coerce').fillna(0)
    df_ex = df_ex[df_ex['Amount'] > 0]

    return df_inc, df_ex

st.title("📊 R&D Fund Master Pro")
year = st.sidebar.selectbox("Năm tài chính:", ["2026", "2025"])

try:
    df_members, df_expense = get_data(year)
    
    # Tính toán
    total_income = df_members.iloc[:, 1:13].sum().sum()
    total_expense = df_expense['Amount'].sum()
    balance = total_income - total_expense
    
    # Hiển thị số liệu nhanh
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng Thu", f"{total_income:,.0f} VND")
    c2.metric("Tổng Chi", f"{total_expense:,.0f} VND")
    c3.metric("Số dư", f"{balance:,.0f} VND")

    # Biểu đồ tiến độ thu quỹ
    st.subheader(f"Tiến độ thu quỹ năm {year}")
    monthly_collected = df_members.iloc[:, 1:13].sum()
    expected_per_month = len(df_members) * STANDARD_FEE
    
    fig = go.Figure(data=[
        go.Bar(name='Đã thu', x=MONTHS, y=monthly_collected, marker_color='#1e3a8a'),
        go.Bar(name='Còn lại', x=MONTHS, y=[max(0, expected_per_month - v) for v in monthly_collected], marker_color='#f59e0b')
    ])
    fig.update_layout(barmode='stack', height=400, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # Bảng trạng thái đóng quỹ (Tick xanh)
    st.subheader("Chi tiết đóng quỹ")
    df_status = df_members.copy()
    for col in df_status.columns[1:13]:
        df_status[col] = df_status[col].apply(lambda x: "✔" if x > 0 else "-")
    st.dataframe(df_status.iloc[:, 0:13], use_container_width=True)

    # Nhật ký chi tiêu
    st.subheader("Nhật ký chi tiêu")
    if not df_expense.empty:
        st.table(df_expense)
    else:
        st.write("Không có dữ liệu chi tiêu.")

except Exception as e:
    st.error(f"Lỗi: {e}")
