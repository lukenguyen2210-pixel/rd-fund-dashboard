import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="R&D Fund Master Pro", layout="wide")

SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"
# Danh sách tháng khớp chuẩn với thứ tự cột C -> N trong Sheets
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
YEARS_LIST = ["2025", "2026"]

def clean_money(value):
    if pd.isna(value) or str(value).strip() == "" or str(value).strip() == "-":
        return 0
    s = str(value).lower().replace('đ', '').replace(',', '').replace('.', '').replace(' ', '').strip()
    try:
        return float(s)
    except:
        return 0

@st.cache_data(ttl=60)
def fetch_all_data():
    all_data = {}
    total_g_income = 0
    total_g_expense = 0
    
    for y in YEARS_LIST:
        # Đọc từ B2:N41 để lấy đúng danh sách nhân viên, bỏ qua dòng SUM ở 44
        url_inc = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}&range=B2:N41"
        df_inc = pd.read_csv(url_inc)
        
        # Reset lại tên cột cho chuẩn bộ MONTHS
        df_inc.columns = ["Full Name"] + MONTHS
        
        # Lọc bỏ các dòng tiêu đề thừa nếu có
        df_inc = df_inc[df_inc["Full Name"].notna()]
        df_inc = df_inc[~df_inc["Full Name"].str.contains("Full Name|Tên NV|SUM|Tổng", case=False, na=False)]
        
        # Ép kiểu số cho các tháng
        for col in MONTHS:
            df_inc[col] = df_inc[col].apply(clean_money)
        
        current_y_inc = df_inc[MONTHS].sum().sum()
        
        # Load Chi tiêu từ cột Q đến S
        url_exp = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}&range=Q3:S41"
        df_ex = pd.read_csv(url_exp, header=None)
        current_y_exp = 0
        if not df_ex.empty:
            df_ex.columns = ['Date', 'Amount', 'Explanation']
            df_ex['Amount'] = df_ex['Amount'].apply(clean_money)
            df_ex = df_ex[df_ex['Amount'] > 0].dropna(subset=['Explanation'])
            current_y_exp = df_ex['Amount'].sum()
            
        all_data[y] = {"income_df": df_inc, "expense_df": df_ex, "y_inc": current_y_inc, "y_exp": current_y_exp}
        total_g_income += current_y_inc
        total_g_expense += current_y_exp
        
    return all_data, (total_g_income - total_g_expense)

try:
    data_store, grand_balance = fetch_all_data()
    st.title("🚀 R&D Fund Master Dashboard")

    # Banner Tổng số dư (2 năm)
    st.markdown(f"""
    <div style="background-color:#1e3a8a; padding:30px; border-radius:15px; border-left: 10px solid #f59e0b; margin-bottom:30px">
        <p style="color:white; margin:0; font-size:16px; font-weight:bold; opacity:0.8">TỔNG SỐ DƯ QUỸ HIỆN TẠI (2025 + 2026)</p>
        <h1 style="color:white; margin:0; font-size:64px; font-weight:bold">{grand_balance:,.0f} <span style="font-size:24px">VND</span></h1>
    </div>
    """, unsafe_allow_html=True)

    year_choice = st.sidebar.selectbox("Chọn năm báo cáo:", YEARS_LIST[::-1])
    curr = data_store[year_choice]
    
    # Chỉ số năm hiện tại
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Tổng thu {year_choice}", f"{curr['y_inc']:,.0f} VND")
    c2.metric(f"Tổng chi {year_choice}", f"{curr['y_exp']:,.0f} VND")
    c3.metric(f"Dư năm {year_choice}", f"{(curr['y_inc'] - curr['y_exp']):,.0f} VND")

    # Bảng chi tiết
    with st.expander(f"Bảng chi tiết đóng quỹ {year_choice}", expanded=True):
        df_display = curr["income_df"].copy()
        # Hiển thị tick xanh nếu có tiền
        for col in MONTHS:
            df_display[col] = df_display[col].apply(lambda x: "✔" if x > 0 else "-")
        
        df_display.index = range(1, len(df_display) + 1)
        df_display.index.name = "STT"
        st.dataframe(df_display, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi: {e}")
