import streamlit as st
import pandas as pd

st.set_page_config(page_title="R&D Fund Master", layout="wide")

SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
YEARS = ["2025", "2026"]

def clean_money(v):
    if pd.isna(v) or str(v).strip() in ["", "-", "0"]: return 0
    try:
        return float(str(v).lower().replace('đ', '').replace(',', '').replace('.', '').replace(' ', '').strip())
    except: return 0

@st.cache_data(ttl=5)
def load_data():
    db = {}
    total_inc, total_exp = 0, 0
    
    for y in YEARS:
        # Load Thu: Bốc từ B3 đến N43 (né tiêu đề và dòng SUM 44)
        url_inc = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}&range=B3:N43"
        df_inc = pd.read_csv(url_inc, header=None)
        
        # Chỉ lấy 13 cột đầu, đặt tên chuẩn để không lệch tháng
        df_inc = df_inc.iloc[:, :13]
        df_inc.columns = ["Full Name"] + MONTHS
        
        # QUAN TRỌNG: Chỉ lấy dòng có tên, bỏ qua các ô trống bro để ở cuối list
        df_inc = df_inc.dropna(subset=["Full Name"])
        df_inc["Full Name"] = df_inc["Full Name"].astype(str).str.strip()
        df_inc = df_inc[df_inc["Full Name"] != ""]
        
        # Chuyển đổi tiền
        for m in MONTHS:
            df_inc[m] = df_inc[m].apply(clean_money)
            
        y_inc = df_inc[MONTHS].sum().sum()
        
        # Load Chi: Q3:S43
        url_exp = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}&range=Q3:S43"
        df_ex = pd.read_csv(url_exp, header=None)
        y_exp = 0
        if not df_ex.empty:
            df_ex = df_ex.iloc[:, :3]
            df_ex.columns = ['Date', 'Amount', 'Explanation']
            df_ex['Amount'] = df_ex['Amount'].apply(clean_money)
            df_ex = df_ex[df_ex['Amount'] > 0].dropna(subset=['Explanation'])
            y_exp = df_ex['Amount'].sum()
            
        db[y] = {"inc_df": df_inc, "exp_df": df_ex, "y_inc": y_inc, "y_exp": y_exp}
        total_inc += y_inc
        total_exp += y_exp
        
    return db, (total_inc - total_exp)

try:
    data, balance = load_data()
    
    # Banner số dư
    st.markdown(f"""
    <div style="background-color:#1e3a8a; padding:30px; border-radius:15px; border-left: 10px solid #f59e0b; margin-bottom:20px">
        <p style="color:white; margin:0; font-size:16px; font-weight:bold; opacity:0.8">SỐ DƯ QUỸ HIỆN TẠI</p>
        <h1 style="color:white; margin:0; font-size:64px; font-weight:bold">{balance:,.0f} <span style="font-size:24px">VND</span></h1>
    </div>
    """, unsafe_allow_html=True)

    y_choice = st.sidebar.selectbox("Năm:", YEARS[::-1])
    c = data[y_choice]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng thu", f"{c['y_inc']:,.0f} VND")
    col2.metric("Tổng chi", f"{c['y_exp']:,.0f} VND")
    col3.metric("Còn lại", f"{(c['y_inc'] - c['y_exp']):,.0f} VND")

    with st.expander(f"Chi tiết đóng quỹ {y_choice}", expanded=True):
        display = c["inc_df"].copy()
        for m in MONTHS:
            display[m] = display[m].apply(lambda x: "✔" if x > 0 else "-")
        display.index = range(1, len(display) + 1)
        display.index.name = "STT"
        st.dataframe(display, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi: {e}")
