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
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}"
        # Đọc thô hoàn toàn
        df_raw = pd.read_csv(url, header=None)
        
        # --- LẤY DỮ LIỆU THU ---
        # Bốc một vùng rộng hơn một chút (từ dòng 2 đến 44) để kiểm tra
        df_temp = df_raw.iloc[1:45, 1:14].copy()
        df_temp.columns = ["Full Name"] + MONTHS
        
        # Loại bỏ các dòng tiêu đề "No.", "Full Name" hoặc "Tên NV" nếu dính vào
        # Chỉ giữ lại dòng nào mà cột tên không phải là tiêu đề
        df_inc = df_temp[~df_temp["Full Name"].astype(str).str.contains("Full Name|Tên NV|No\.|STT", na=False, case=False)].copy()
        
        # Loại bỏ dòng trống
        df_inc = df_inc.dropna(subset=["Full Name"])
        df_inc["Full Name"] = df_inc["Full Name"].astype(str).str.strip()
        df_inc = df_inc[df_inc["Full Name"] != ""]
        df_inc = df_inc[df_inc["Full Name"] != "nan"]
        
        # Giới hạn đúng 41 dòng như bro yêu cầu (từ B3:B43)
        df_inc = df_inc.head(41)
        
        for m in MONTHS:
            df_inc[m] = df_inc[m].apply(clean_money)
        y_inc = df_inc[MONTHS].sum().sum()
        
        # --- LẤY DỮ LIỆU CHI ---
        df_ex = df_raw.iloc[2:45, 16:19].copy()
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
    
    st.markdown(f"""
    <div style="background-color:#1e3a8a; padding:30px; border-radius:15px; border-left: 10px solid #f59e0b; margin-bottom:20px">
        <p style="color:white; margin:0; font-size:16px; font-weight:bold; opacity:0.8">TỔNG SỐ DƯ QUỸ</p>
        <h1 style="color:white; margin:0; font-size:64px; font-weight:bold">{balance:,.0f} <span style="font-size:24px">VND</span></h1>
    </div>
    """, unsafe_allow_html=True)

    y_sel = st.sidebar.selectbox("Năm:", YEARS[::-1])
    curr = data[y_sel]
    
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Thu {y_sel}", f"{curr['y_inc']:,.0f} VND")
    c2.metric(f"Chi {y_sel}", f"{curr['y_exp']:,.0f} VND")
    c3.metric("Còn lại", f"{(curr['y_inc'] - curr['y_exp']):,.0f} VND")

    with st.expander(f"Chi tiết {y_sel}", expanded=True):
        res = curr["inc_df"].copy()
        for m in MONTHS:
            res[m] = res[m].apply(lambda x: "✔" if x > 0 else "-")
        
        res = res.reset_index(drop=True)
        res.index = range(1, len(res) + 1)
        res.index.name = "STT"
        st.dataframe(res, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi: {e}")
