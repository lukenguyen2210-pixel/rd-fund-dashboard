import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="R&D Fund Master Pro", layout="wide")

# Link file và cấu hình
SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"
STANDARD_FEE = 100000
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]

def get_data(year):
    # 1. Logic lấy dữ liệu Thu (Range B3:M43 tương đương rawData trong Script)
    url_income = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={year}&range=B3:N43"
    df_income = pd.read_csv(url_income)
    
    # Clean dữ liệu Member (Lọc bỏ các dòng tổng cộng)
    df_members = df_income.dropna(subset=[df_income.columns[0]])
    exclude_list = ["SUM", "Tổng cộng", "Tên NV", "Total", "TOTAL"]
    df_members = df_members[~df_members.iloc[:, 0].isin(exclude_list)]
    
    # 2. Logic lấy dữ liệu Chi (Range Q3:S43 tương đương getExpenseDetail)
    url_expense = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={year}&range=Q3:S43"
    df_expense = pd.read_csv(url_expense)
    df_expense.columns = ['Date', 'Amount', 'Content']
    df_expense = df_expense.dropna(subset=['Amount'])
    df_expense = df_expense[df_expense['Amount'] > 0]

    return df_members, df_expense

# Giao diện Header
st.title("📊 R&D Fund Master Pro")
year = st.sidebar.selectbox("Chọn năm tài chính:", ["2026", "2025"])

try:
    df_members, df_expense = get_data(year)
    
    # TÍNH TOÁN LOGIC
    total_income = df_members.iloc[:, 1:13].sum().sum()
    total_expense = df_expense['Amount'].sum()
    balance = total_income - total_expense
    
    # HIỂN THỊ STAT CARDS
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng Thu (Income)", f"{total_income:,.0f} VND")
    col2.metric("Tổng Chi (Expense)", f"{total_expense:,.0f} VND", delta_color="inverse")
    col3.metric("Số dư (Balance)", f"{balance:,.0f} VND")

    # BIỂU ĐỒ TIẾN ĐỘ (Giống Chart.js trong Index.html)
    st.subheader(f"Collection Progress - Year {year}")
    monthly_collected = df_members.iloc[:, 1:13].sum()
    expected_per_month = len(df_members) * STANDARD_FEE
    
    fig = go.Figure(data=[
        go.Bar(name='Collected', x=MONTHS, y=monthly_collected, marker_color='#1e3a8a'),
        go.Bar(name='Remaining', x=MONTHS, y=[max(0, expected_per_month - v) for v in monthly_collected], marker_color='#f59e0b')
    ])
    fig.update_layout(barmode='stack', height=400, margin=dict(l=20, r=20, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # CHI TIẾT ĐÓNG QUỸ (Bảng có Tick xanh giống Script)
    st.subheader("1. Member Payment Status")
    # Tạo bảng tick
    df_tick = df_members.copy()
    for col in df_tick.columns[1:13]:
        df_tick[col] = df_tick[col].apply(lambda x: "✔" if x > 0 else "-")
    st.dataframe(df_tick.iloc[:, 0:13], use_container_width=True)

    # NHẬT KÝ CHI TIÊU
    st.subheader("2. Expense Log")
    if not df_expense.empty:
        st.table(df_expense)
    else:
        st.info("Chưa có bản ghi chi tiêu nào.")

except Exception as e:
    st.error(f"Lỗi: {e}")
    st.info("Bro hãy chắc chắn Tab trong Google Sheets được đặt tên chính xác là '2026' hoặc '2025'.")
