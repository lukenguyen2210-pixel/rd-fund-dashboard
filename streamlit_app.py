import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="R&D Fund Master Pro", layout="wide")

SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
YEARS_LIST = ["2025", "2026"]
STANDARD_FEE = 100000

def clean_money(value):
    if pd.isna(value) or str(value).strip() == "":
        return 0
    s = str(value).lower().replace('đ', '').replace(',', '').replace('.', '').replace(' ', '').strip()
    try:
        return float(s)
    except:
        return 0

@st.cache_data(ttl=300)
def fetch_all_data():
    all_data = {}
    total_g_income = 0
    total_g_expense = 0
    
    for y in YEARS_LIST:
        # 1. Load Thu (B3:N45 - tăng range lên để tránh sót)
        url_inc = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}&range=B3:N45"
        df_inc = pd.read_csv(url_inc, header=None)
        df_inc.columns = ["Full Name"] + MONTHS
        
        # --- BỘ LỌC THÔNG MINH ---
        # Loại bỏ dòng trống
        df_inc = df_inc.dropna(subset=["Full Name"])
        
        # Loại bỏ dòng gộp tiêu đề (Thường rất dài, chứa nhiều tên hoặc từ khóa hệ thống)
        # Nếu tên dài hơn 40 ký tự hoặc chứa các từ khóa tiêu đề -> Loại bỏ
        exclude_keywords = ['SUM', 'TỔNG', 'Tên NV', 'Total', 'TOTAL', 'đã đóng', 'ghi chú']
        df_inc = df_inc[~df_inc["Full Name"].astype(str).str.contains('|'.join(exclude_keywords), case=False, na=False)]
        df_inc = df_inc[df_inc["Full Name"].astype(str).map(len) < 40] 
        
        # Ép kiểu số
        for col in MONTHS:
            df_inc[col] = df_inc[col].apply(clean_money)
        
        y_inc_val = df_inc[MONTHS].sum().sum()
        
        # 2. Load Chi (Q3:S45)
        url_exp = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}&range=Q3:S45"
        df_ex = pd.read_csv(url_exp, header=None)
        y_exp_val = 0
        if not df_ex.empty:
            df_ex.columns = ['Date', 'Amount', 'Explanation']
            df_ex['Amount'] = df_ex['Amount'].apply(clean_money)
            df_ex = df_ex[df_ex['Amount'] > 0].dropna(subset=['Explanation'])
            y_exp_val = df_ex['Amount'].sum()
            
        all_data[y] = {"income_df": df_inc, "expense_df": df_ex, "y_inc": y_inc_val, "y_exp": y_exp_val}
        total_g_income += y_inc_val
        total_g_expense += y_exp_val
        
    return all_data, (total_g_income - total_g_expense)

# --- GIAO DIỆN ---
try:
    data_store, grand_balance = fetch_all_data()
    st.title("🚀 R&D Fund Master Dashboard")

    # Grand Total Banner
    st.markdown(f"""
    <div style="background-color:#1e3a8a; padding:25px; border-radius:15px; border-left: 10px solid #f59e0b; margin-bottom:30px">
        <p style="color:white; margin:0; font-size:14px; font-weight:bold; opacity:0.8; text-transform:uppercase; letter-spacing:1px">Tổng số dư quỹ (Tất cả các năm)</p>
        <h1 style="color:white; margin:0; font-size:54px; font-weight:bold">{grand_balance:,.0f} <span style="font-size:22px">VND</span></h1>
    </div>
    """, unsafe_allow_html=True)

    year_choice = st.sidebar.selectbox("Chọn năm xem báo cáo:", YEARS_LIST[::-1])
    curr = data_store[year_choice]
    
    # Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Thu trong năm", f"{curr['y_inc']:,.0f} VND")
    c2.metric("Chi trong năm", f"{curr['y_exp']:,.0f} VND")
    c3.metric("Số dư năm này", f"{(curr['y_inc'] - curr['y_exp']):,.0f} VND")

    # Bảng chi tiết
    with st.expander(f"Chi tiết đóng quỹ {year_choice}", expanded=True):
        df_tick = curr["income_df"].copy()
        for col in MONTHS:
            df_tick[col] = df_tick[col].apply(lambda x: "✔" if x > 0 else "-")
        df_tick.index = range(1, len(df_tick) + 1)
        df_tick.index.name = "STT"
        st.dataframe(df_tick[["Full Name"] + MONTHS], use_container_width=True)

except Exception as e:
    st.error(f"Lỗi: {e}")
