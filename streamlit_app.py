import streamlit as st
import pandas as pd

st.set_page_config(page_title="R&D Fund Master Pro", layout="wide")

SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
YEARS_LIST = ["2025", "2026"]

def clean_money(value):
    if pd.isna(value) or str(value).strip() in ["", "-", "0"]:
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
        # CHIẾN THUẬT MỚI: Dùng SQL Query để ép Google Sheets trả về đúng cột B và C->N
        # Select Col2 (B), Col3..Col14 (C..N) 
        # Where Col2 is not null and not like 'SUM'
        query = "select Col2, Col3, Col4, Col5, Col6, Col7, Col8, Col9, Col10, Col11, Col12, Col13, Col14 where Col2 is not null and not Col2 contains 'SUM' and not Col2 contains 'Tên NV' and not Col2 contains 'Đoàn Thị'"
        url_inc = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}&tq={query}&range=A3:N43"
        
        df_inc = pd.read_csv(url_inc)
        df_inc.columns = ["Full Name"] + MONTHS
        
        # Chuyển đổi tiền
        for col in MONTHS:
            df_inc[col] = df_inc[col].apply(clean_money)
            
        y_inc_val = df_inc[MONTHS].sum().sum()
        
        # Load Chi tiêu (Cột Q đến S) - Lấy từ dòng 3
        url_exp = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}&range=Q3:S43"
        df_ex = pd.read_csv(url_exp, header=None)
        y_exp_val = 0
        if not df_ex.empty:
            df_ex = df_ex.iloc[:, :3]
            df_ex.columns = ['Date', 'Amount', 'Explanation']
            df_ex['Amount'] = df_ex['Amount'].apply(clean_money)
            df_ex = df_ex[df_ex['Amount'] > 0].dropna(subset=['Explanation'])
            y_exp_val = df_ex['Amount'].sum()
            
        all_data[y] = {"income_df": df_inc, "expense_df": df_ex, "y_inc": y_inc_val, "y_exp": y_exp_val}
        total_g_income += y_inc_val
        total_g_expense += y_exp_val
        
    return all_data, (total_g_income - total_g_expense)

try:
    data_store, grand_balance = fetch_all_data()
    st.title("🚀 R&D Fund Master Dashboard")

    # Banner Số dư tổng
    st.markdown(f"""
    <div style="background-color:#1e3a8a; padding:30px; border-radius:15px; border-left: 10px solid #f59e0b; margin-bottom:30px">
        <p style="color:white; margin:0; font-size:16px; font-weight:bold; opacity:0.8">TỔNG SỐ DƯ QUỸ (2025 + 2026)</p>
        <h1 style="color:white; margin:0; font-size:64px; font-weight:bold">{grand_balance:,.0f} <span style="font-size:24px">VND</span></h1>
    </div>
    """, unsafe_allow_html=True)

    year_choice = st.sidebar.selectbox("Năm tài chính:", YEARS_LIST[::-1])
    curr = data_store[year_choice]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng thu", f"{curr['y_inc']:,.0f} VND")
    c2.metric("Tổng chi", f"{curr['y_exp']:,.0f} VND")
    c3.metric("Số dư năm", f"{(curr['y_inc'] - curr['y_exp']):,.0f} VND")

    with st.expander(f"Danh sách đóng quỹ {year_choice}", expanded=True):
        res = curr["income_df"].copy()
        for m in MONTHS:
            res[m] = res[m].apply(lambda x: "✔" if x > 0 else "-")
        res.index = range(1, len(res) + 1)
        res.index.name = "STT"
        st.dataframe(res, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi: {e}")
