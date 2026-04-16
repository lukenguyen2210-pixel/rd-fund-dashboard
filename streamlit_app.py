import streamlit as st
import pandas as pd

st.set_page_config(page_title="R&D Fund Master", layout="wide")

SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
YEARS = ["2025", "2026"]

def clean_money(v):
    if pd.isna(v) or str(v).strip() in ["", "-", "0", "0.0"]: return 0
    s = str(v).lower().replace('đ', '').replace(',', '').replace('.', '').replace(' ', '').strip()
    try: return float(s)
    except: return 0

@st.cache_data(ttl=2)
def load_data():
    db = {}
    g_inc, g_exp = 0, 0
    for y in YEARS:
        # Tải toàn bộ sheet về, không dùng &range trong URL để tránh lỗi kết nối
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}"
        df_raw = pd.read_csv(url, header=None)
        
        # --- TRÍCH XUẤT CỨNG VÙNG B3:N43 ---
        # iloc[row_start:row_end, col_start:col_end]
        # Hàng 3 (index 2) đến hàng 43 (index 43)
        # Cột B (index 1) đến cột N (index 14)
        df_inc = df_raw.iloc[2:43, 1:14].copy()
        df_inc.columns = ["Full Name"] + MONTHS
        
        # Loại bỏ dòng trống trong list B3:B43
        df_inc = df_inc.dropna(subset=["Full Name"])
        df_inc["Full Name"] = df_inc["Full Name"].astype(str).str.strip()
        df_inc = df_inc[df_inc["Full Name"] != ""]
        
        for m in MONTHS:
            df_inc[m] = df_inc[m].apply(clean_money)
        y_inc = df_inc[MONTHS].sum().sum()
        
        # --- TRÍCH XUẤT CỨNG VÙNG Q3:S43 (Chi tiêu) ---
        df_ex = df_raw.iloc[2:43, 16:19].copy()
        df_ex.columns = ['Date', 'Amount', 'Explanation']
        df_ex['Amount'] = df_ex['Amount'].apply(clean_money)
        df_ex = df_ex[df_ex['Amount'] > 0].dropna(subset=['Explanation'])
        y_exp = df_ex['Amount'].sum()
        
        db[y] = {"inc_df": df_inc, "exp_df": df_ex, "y_inc": y_inc, "y_exp": y_exp}
        g_inc += y_inc
        g_exp += y_exp
        
    return db, (g_inc - g_exp)

try:
    data, balance = load_data()
    
    # Banner tổng số dư
    st.markdown(f"""
    <div style="background-color:#1e3a8a; padding:30px; border-radius:15px; border-left: 10px solid #f59e0b; margin-bottom:20px">
        <p style="color:white; margin:0; font-size:16px; font-weight:bold; opacity:0.8">TỔNG SỐ DƯ QUỸ (2025 + 2026)</p>
        <h1 style="color:white; margin:0; font-size:64px; font-weight:bold">{balance:,.0f} <span style="font-size:24px">VND</span></h1>
    </div>
    """, unsafe_allow_html=True)

    y_sel = st.sidebar.selectbox("Năm xem báo cáo:", YEARS[::-1])
    curr = data[y_sel]
    
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Tổng thu {y_sel}", f"{curr['y_inc']:,.0f} VND")
    c2.metric(f"Tổng chi {y_sel}", f"{curr['y_exp']:,.0f} VND")
    c3.metric("Còn lại", f"{(curr['y_inc'] - curr['y_exp']):,.0f} VND")

    with st.expander(f"Chi tiết đóng quỹ {y_sel}", expanded=True):
        res = curr["inc_df"].copy()
        for m in MONTHS:
            res[m] = res[m].apply(lambda x: "✔" if x > 0 else "-")
        
        # Reset index để làm STT chuẩn
        res = res.reset_index(drop=True)
        res.index = range(1, len(res) + 1)
        res.index.name = "STT"
        st.dataframe(res, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi rồi bro: {e}")
