import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="R&D Fund Master Pro", layout="wide")

SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"
STANDARD_FEE = 100000
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]

def get_data(year_choice):
    # Lấy dữ liệu Thu - mở rộng dải ô để chắc chắn không sót
    url_income = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={year_choice}&range=B2:N45"
    df_inc = pd.read_csv(url_income)
    
    # 1. Xử lý Header: Lấy dòng đầu tiên làm tên cột nếu nó bị lệch
    if "Full Name" not in df_inc.columns:
        df_inc.columns = ["Full Name"] + MONTHS
        
    # 2. Lọc thành viên (Logic từ Apps Script của bro)
    exclude = ["SUM", "Tổng cộng", "Tên NV", "Total", "TOTAL", "nan"]
    df_inc = df_inc.dropna(subset=[df_inc.columns[0]])
    df_inc = df_inc[~df_inc.iloc[:, 0].astype(str).str.contains('|'.join(exclude), case=False, na=False)]
    
    # 3. Ép kiểu số cực mạnh (Xử lý dấu phẩy, khoảng trắng)
    for col in df_inc.columns[1:13]:
        df_inc[col] = df_inc[col].astype(str).str.replace(',', '').str.replace(' ', '')
        df_inc[col] = pd.to_numeric(df_inc[col], errors='coerce').fillna(0)
    
    # 4. Lấy dữ liệu Chi (Q3:S43)
    url_exp = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={year_choice}&range=Q3:S43"
    df_ex = pd.read_csv(url_exp)
    if not df_ex.empty:
        df_ex.columns = ['Date', 'Amount', 'Content']
        df_ex['Amount'] = pd.to_numeric(df_ex['Amount'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        df_ex = df_ex[df_ex['Amount'] > 0]

    return df_inc, df_ex

st.title("📊 R&D Fund Master Pro")
year = st.sidebar.selectbox("Năm tài chính:", ["2026", "2025"])

try:
    df_members, df_expense = get_data(year)
    
    # Tính toán tổng hợp
    total_income = df_members.iloc[:, 1:13].sum().sum()
    total_expense = df_expense['Amount'].sum() if not df_expense.empty else 0
    balance = total_income - total_expense
    
    # Dashboard Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng Thu", f"{total_income:,.0f} VND")
    c2.metric("Tổng Chi", f"{total_expense:,.0f} VND")
    c3.metric("Số dư hiện tại", f"{balance:,.0f} VND")

    # Biểu đồ tiến độ (Fix màu sắc và dữ liệu)
    st.subheader(f"Tiến độ đóng quỹ tháng (Năm {year})")
    monthly_collected = df_members.iloc[:, 1:13].sum().values
    expected_per_month = len(df_members) * STANDARD_FEE
    
    fig = go.Figure(data=[
        go.Bar(name='Đã thu', x=MONTHS, y=monthly_collected, marker_color='#1e3a8a'),
        go.Bar(name='Còn thiếu', x=MONTHS, y=[max(0, expected_per_month - v) for v in monthly_collected], marker_color='#f59e0b')
    ])
    fig.update_layout(barmode='stack', height=350, margin=dict(l=0, r=0, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    # Bảng chi tiết (Tick xanh)
    st.subheader("Chi tiết đóng quỹ")
    df_display = df_members.copy()
    # Chỉ giữ lại các cột tháng để làm tick
    for col in MONTHS:
        df_display[col] = df_display[col].apply(lambda x: "✔" if x >= 1000 else "-")
    
    st.dataframe(df_display[["Full Name"] + MONTHS], use_container_width=True, height=400)

    # Nhật ký chi tiêu
    st.subheader("Nhật ký chi tiêu")
    if not df_expense.empty:
        st.dataframe(df_expense, use_container_width=True)
    else:
        st.write("Chưa có dữ liệu chi tiêu cho năm này.")

except Exception as e:
    st.error(f"Lỗi hệ thống: {e}")
