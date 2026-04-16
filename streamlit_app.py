import streamlit as st
import pandas as pd

st.set_page_config(page_title="R&D Fund Master Pro", layout="wide")

SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
YEARS_LIST = ["2025", "2026"]

def clean_money(value):
    if pd.isna(value) or str(value).strip() in ["", "-", "0", "0.0"]:
        return 0
    s = str(value).lower().replace('đ', '').replace(',', '').replace('.', '').replace(' ', '').strip()
    try:
        return float(s)
    except:
        return 0

@st.cache_data(ttl=10)
def fetch_data():
    all_data = {}
    g_total_inc = 0
    g_total_exp = 0
    
    for y in YEARS_LIST:
        # 1. LOAD THU: Bốc từ B3 đến N43 (né tiêu đề gộp và dòng SUM 44)
        url_inc = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}&range=B3:N43"
        df = pd.read_csv(url_inc, header=None)
        
        # Đảm bảo lấy đúng 13 cột (Tên + 12 tháng), thiếu thì bù trống
        if df.shape[1] < 13:
            for i in range(df.shape[1], 13):
                df[i] = 0
        df = df.iloc[:, :13]
        df.columns = ["Full Name"] + MONTHS
        
        # Dọn dẹp danh sách tên: xóa dòng trống, dòng rác, dòng tiêu đề dính vào
        df = df.dropna(subset=["Full Name"])
        df["Full Name"] = df["Full Name"].astype(str).str.strip()
        exclude = ["Tên NV", "SUM", "Tổng cộng", "Total", "Đoàn Thị"]
        df = df[~df["Full Name"].str.contains('|'.join(exclude), case=False, na=False)]
        df = df[df["Full Name"].map(len) < 35] # Loại bỏ các dòng gộp tên dài bất thường
        
        # Ép kiểu tiền tệ cho 12 tháng
        for m in MONTHS:
            df[m] = df[m].apply(clean_money)
            
        y_inc = df[MONTHS].sum().sum()
        
        # 2. LOAD CHI: Cột Q đến S
        url_exp = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}&range=Q3:S43"
        df_ex = pd.read_csv(url_exp, header=None)
        y_exp = 0
        if not df_ex.empty:
            df_ex = df_ex.iloc[:, :3]
            df_ex.columns = ['Date', 'Amount', 'Explanation']
            df_ex['Amount'] = df_ex['Amount'].apply(clean_money)
            df_ex = df_ex[df_ex['Amount'] > 0].dropna(subset=['Explanation'])
            y_exp = df_ex['Amount'].sum()
            
        all_data[y] = {"inc_df": df, "exp_df": df_ex, "y_inc": y_inc, "y_exp": y_exp}
        g_total_inc += y_inc
        g_total_exp += y_exp
        
    return all_data, (g_total_inc - g_total_exp)

try:
    data, balance = fetch_data()
    
    # BANNER TỔNG SỐ DƯ
    st.markdown(f"""
    <div style="background-color:#1e3a8a; padding:30px; border-radius:15px; border-left: 10px solid #f59e0b; margin-bottom:30px">
        <p style="color:white; margin:0; font-size:16px; font-weight:bold; opacity:0.8">SỐ DƯ QUỸ HIỆN TẠI</p>
        <h1 style="color:white; margin:0; font-size:64px; font-weight:bold">{balance:,.0f} <span style="font-size:24px">VND</span></h1>
    </div>
    """, unsafe_allow_html=True)

    year = st.sidebar.selectbox("Chọn năm báo cáo:", YEARS_LIST[::-1])
    curr = data[year]
    
    # Chỉ số nhanh
    c1, c2, c3 = st.columns(3)
    c1.metric("Tổng thu", f"{curr['y_inc']:,.0f} VND")
    c2.metric("Tổng chi", f"{curr['y_exp']:,.0f} VND")
    c3.metric("Số dư năm", f"{(curr['y_inc'] - curr['y_exp']):,.0f} VND")

    # Bảng chi tiết
    with st.expander(f"Chi tiết đóng quỹ {year}", expanded=True):
        res = curr["inc_df"].copy()
        for m in MONTHS:
            res[m] = res[m].apply(lambda x: "✔" if x > 0 else "-")
        res.index = range(1, len(res) + 1)
        res.index.name = "STT"
        st.dataframe(res, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi rồi bro: {e}")
