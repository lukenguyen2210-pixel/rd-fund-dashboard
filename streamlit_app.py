import streamlit as st
import pandas as pd

st.set_page_config(page_title="R&D Fund Master Pro", layout="wide")

SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
YEARS = ["2025", "2026"]

def clean_val(v):
    if pd.isna(v) or str(v).strip() in ["", "-", "0", "0.0"]: return 0
    try:
        return float(str(v).lower().replace('đ', '').replace(',', '').replace('.', '').replace(' ', '').strip())
    except: return 0

@st.cache_data(ttl=5)
def load_all():
    db = {}
    g_total_inc = 0
    g_total_exp = 0
    
    for y in YEARS:
        # Tải thô toàn bộ sheet về xử lý sau
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}"
        df_raw = pd.read_csv(url, header=None)
        
        # 1. XỬ LÝ THU (Cột B đến N, dòng 3 đến 43)
        # Bốc dữ liệu từ hàng index 2 (dòng 3) và cột index 1 (cột B)
        df_inc = df_raw.iloc[2:43, 1:14].copy() 
        df_inc.columns = ["Full Name"] + MONTHS
        
        # Lọc sạch tên: bỏ dòng trống hoặc dòng tiêu đề gộp
        df_inc = df_inc.dropna(subset=["Full Name"])
        df_inc["Full Name"] = df_inc["Full Name"].astype(str).str.strip()
        df_inc = df_inc[df_inc["Full Name"].map(len) < 30] 
        df_inc = df_inc[~df_inc["Full Name"].str.contains("Tên NV|SUM|Tổng cộng|Đoàn Thị", case=False, na=False)]
        
        for m in MONTHS:
            df_inc[m] = df_inc[m].apply(clean_val)
        
        y_inc = df_inc[MONTHS].sum().sum()
        
        # 2. XỬ LÝ CHI (Cột Q đến S, dòng 3 đến 43)
        df_exp = df_raw.iloc[2:43, 16:19].copy()
        df_exp.columns = ["Date", "Amount", "Explanation"]
        df_exp["Amount"] = df_exp["Amount"].apply(clean_val)
        df_exp = df_exp[df_exp["Amount"] > 0].dropna(subset=["Explanation"])
        
        y_exp = df_exp["Amount"].sum()
        
        db[y] = {"inc_df": df_inc, "exp_df": df_exp, "y_inc": y_inc, "y_exp": y_exp}
        g_total_inc += y_inc
        g_total_exp += y_exp
        
    return db, (g_total_inc - g_total_exp)

try:
    data, balance = load_all()
    
    st.markdown(f"""
    <div style="background-color:#1e3a8a; padding:30px; border-radius:15px; border-left: 10px solid #f59e0b; margin-bottom:30px">
        <p style="color:white; margin:0; font-size:16px; font-weight:bold; opacity:0.8">TỔNG SỐ DƯ QUỸ (2025 + 2026)</p>
        <h1 style="color:white; margin:0; font-size:64px; font-weight:bold">{balance:,.0f} <span style="font-size:24px">VND</span></h1>
    </div>
    """, unsafe_allow_html=True)

    year_sel = st.sidebar.selectbox("Năm báo cáo:", YEARS[::-1])
    curr = data[year_sel]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Tổng thu", f"{curr['y_inc']:,.0f} VND")
    col2.metric("Tổng chi", f"{curr['y_exp']:,.0f} VND")
    col3.metric("Số dư năm", f"{(curr['y_inc'] - curr['y_exp']):,.0f} VND")

    with st.expander(f"Chi tiết đóng quỹ {year_sel}", expanded=True):
        res = curr["inc_df"].copy()
        for m in MONTHS:
            res[m] = res[m].apply(lambda x: "✔" if x > 0 else "-")
        res.index = range(1, len(res) + 1)
        res.index.name = "STT"
        st.dataframe(res, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi hệ thống: {e}")
