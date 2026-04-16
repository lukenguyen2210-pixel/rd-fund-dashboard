import streamlit as st
import pandas as pd
from urllib.parse import quote

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
        # Lấy từ Col2 (Tên) đến Col14 (Tháng 3 năm sau)
        raw_query = "select Col2, Col3, Col4, Col5, Col6, Col7, Col8, Col9, Col10, Col11, Col12, Col13, Col14 where Col2 is not null and not Col2 contains 'SUM' and not Col2 contains 'Tên NV' and not Col2 contains 'Đoàn Thị'"
        encoded_query = quote(raw_query)
        url_inc = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}&tq={encoded_query}&range=A3:N43"
        
        df_inc = pd.read_csv(url_inc)
        
        # --- CHIẾN THUẬT FIX LỖI LENGTH MISMATCH ---
        # 1. Đặt tên cột tạm thời cho những cột đang có
        current_cols = ["Full Name"] + MONTHS[:len(df_inc.columns)-1]
        df_inc.columns = current_cols
        
        # 2. Nếu thiếu cột tháng nào (do Sheets trống), tự thêm cột đó với giá trị 0
        for m in MONTHS:
            if m not in df_inc.columns:
                df_inc[m] = 0
        
        # 3. Sắp xếp lại đúng thứ tự bảng đóng tiền
        df_inc = df_inc[["Full Name"] + MONTHS]
        
        # Làm sạch dữ liệu tiền
        for col in MONTHS:
            df_inc[col] = df_inc[col].apply(clean_money)
            
        y_inc_val = df_inc[MONTHS].sum().sum()
        
        # Load Chi tiêu (Cột Q đến S)
        url_exp = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}&range=Q3:S43"
        df_ex = pd.read_csv(url_exp, header=None)
        y_exp_val = 0
        if not df_ex.empty:
            # Chỉ lấy tối đa 3 cột nếu có, tránh lỗi thừa cột rác
            df_ex = df_ex.iloc[:, :3]
            df_ex.columns = ['Date', 'Amount', 'Explanation']
            df_ex['Amount'] = df_ex['Amount'].apply(clean_money)
            df_ex = df_ex[df_ex['Amount'] > 0].dropna(subset=['Explanation'])
            y_exp_val = df_ex['Amount'].sum()
            
        all_data[y] = {"income_df": df_inc, "expense_df": df_ex, "y_inc": y_inc_val, "y_exp": y_exp_val}
        total_g_income += y_inc_val
        total_g_expense += y_exp_val
        
    return all_data, (total_g_income - total_g_expense)

# --- PHẦN GIAO DIỆN (GIỮ NGUYÊN) ---
try:
    data_store, grand_balance = fetch_all_data()
    st.title("🚀 R&D Fund Master Dashboard")

    st.markdown(f"""
    <div style="background-color:#1e3a8a; padding:30px; border-radius:15px; border-left: 10px solid #f59e0b; margin-bottom:30px">
        <p style="color:white; margin:0; font-size:16px; font-weight:bold; opacity:0.8">TỔNG SỐ DƯ QUỸ (2025 + 2026)</p>
        <h1 style="color:white; margin:0; font-size:64px; font-weight:bold">{grand_balance:,.0f} <span style="font-size:24px">VND</span></h1>
    </div>
    """, unsafe_allow_html=True)

    year_choice = st.sidebar.selectbox("Chọn năm:", YEARS_LIST[::-1])
    curr = data_store[year_choice]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng thu", f"{curr['y_inc']:,.0f} VND")
    c2.metric("Tổng chi", f"{curr['y_exp']:,.0f} VND")
    c3.metric("Số dư năm", f"{(curr['y_inc'] - curr['y_exp']):,.0f} VND")

    with st.expander(f"Chi tiết đóng quỹ {year_choice}", expanded=True):
        res = curr["income_df"].copy()
        for m in MONTHS:
            res[m] = res[m].apply(lambda x: "✔" if x > 0 else "-")
        res.index = range(1, len(res) + 1)
        res.index.name = "STT"
        st.dataframe(res, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi: {e}")
