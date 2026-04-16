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
        # --- FIX CỨNG DẢI Ô B3:N43 ĐỂ LẤY DANH SÁCH VÀ TIỀN THU ---
        # range=B3:N43 đảm bảo không bao giờ dính dòng 1, 2 hay dòng 44+
        url_inc = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}&range=B3:N43"
        df_inc = pd.read_csv(url_inc, header=None)
        
        # Đảm bảo đủ 13 cột (Tên + 12 tháng)
        df_inc = df_inc.iloc[:, :13]
        df_inc.columns = ["Full Name"] + MONTHS
        
        # Chỉ giữ lại dòng có tên người, loại bỏ các dòng trống trong khoảng B3:B43
        df_inc = df_inc.dropna(subset=["Full Name"])
        df_inc["Full Name"] = df_inc["Full Name"].astype(str).str.strip()
        df_inc = df_inc[df_inc["Full Name"] != ""]
        
        for m in MONTHS:
            df_inc[m] = df_inc[m].apply(clean_money)
        y_inc = df_inc[MONTHS].sum().sum()
        
        # --- FIX CỨNG DẢI Ô Q3:S43 ĐỂ LẤY CHI TIÊU ---
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
        g_inc += y_inc
        g_exp += y_exp
        
    return db, (g_inc - g_exp)

try:
    data, balance = load_data()
    
    # UI Banner
    st.markdown(f"""
    <div style="background-color:#1e3a8a; padding:30px; border-radius:15px; border-left: 10px solid #f59e0b; margin-bottom:20px">
        <p style="color:white; margin:0; font-size:16px; font-weight:bold; opacity:0.8">TỔNG SỐ DƯ QUỸ (2025 + 2026)</p>
        <h1 style="color:white; margin:0; font-size:64px; font-weight:bold">{balance:,.0f} <span style="font-size:24px">VND</span></h1>
    </div>
    """, unsafe_allow_html=True)

    y_sel = st.sidebar.selectbox("Chọn năm:", YEARS[::-1])
    curr = data[y_sel]
    
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Tổng thu {y_sel}", f"{curr['y_inc']:,.0f} VND")
    c2.metric(f"Tổng chi {y_sel}", f"{curr['y_exp']:,.0f} VND")
    c3.metric("Còn lại", f"{(curr['y_inc'] - curr['y_exp']):,.0f} VND")

    with st.expander(f"Chi tiết đóng quỹ {y_sel}", expanded=True):
        res = curr["inc_df"].copy()
        for m in MONTHS:
            res[m] = res[m].apply(lambda x: "✔" if x > 0 else "-")
        res.index = range(1, len(res) + 1)
        res.index.name = "STT"
        # Căn lề trái cho tên và STT theo ý bro
        st.dataframe(res, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi: {e}")
