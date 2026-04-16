import streamlit as st
import pandas as pd
import requests
import re

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="R&D Fund Master", layout="wide")

SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]

def clean_money(v):
    if pd.isna(v) or str(v).strip() in ["", "-", "0", "0.0"]: return 0
    s = str(v).lower().replace('đ', '').replace(',', '').replace('.', '').replace(' ', '').strip()
    try: return float(s)
    except: return 0

# 2. LOGIC TỰ ĐỘNG LẤY TẤT CẢ SHEET NĂM (KHÔNG CẦN ADD TAY)
@st.cache_data(ttl=10)
def get_dynamic_years():
    try:
        # Dùng link này để lấy cấu trúc JSON của cả file Sheets
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:json"
        response = requests.get(url)
        # Parse tên các sheet từ chuỗi JSON trả về
        all_text = response.text
        # Tìm tất cả các đoạn "sheet":"Tên_Sheet"
        sheet_names = re.findall(r'"sheet":"([^"]+)"', all_text)
        # Chỉ lấy những tên là số (năm) và loại bỏ trùng lặp
        years = sorted(list(set([s for s in sheet_names if s.isdigit()])))
        return years if years else ["2025", "2026"]
    except:
        return ["2025", "2026"]

# 3. LOAD DỮ LIỆU
@st.cache_data(ttl=5)
def load_all_data(years_list):
    db = {}
    g_inc, g_exp = 0, 0
    for y in years_list:
        try:
            url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}"
            df_raw = pd.read_csv(url, header=None)
            
            # --- THU (B3:N43) ---
            df_temp = df_raw.iloc[1:45, 1:14].copy()
            df_temp.columns = ["Full Name"] + MONTHS
            df_inc = df_temp[~df_temp["Full Name"].astype(str).str.contains("Full Name|Tên NV|No\.|STT", na=False, case=False)].copy()
            df_inc = df_inc.dropna(subset=["Full Name"])
            df_inc["Full Name"] = df_inc["Full Name"].astype(str).str.strip()
            df_inc = df_inc[df_inc["Full Name"].str.len() > 1]
            df_inc = df_inc.head(41)
            
            for m in MONTHS:
                df_inc[m] = df_inc[m].apply(clean_money)
            y_inc = df_inc[MONTHS].sum().sum()
            
            # --- CHI (Q3:S43) ---
            df_ex = df_raw.iloc[2:45, 16:19].copy()
            df_ex.columns = ['Date', 'Amount', 'Explanation']
            df_ex['Amount'] = df_ex['Amount'].apply(clean_money)
            df_ex = df_ex[df_ex['Amount'] > 0].dropna(subset=['Explanation'])
            y_exp = df_ex['Amount'].sum()
            
            db[y] = {"inc_df": df_inc, "exp_df": df_ex, "y_inc": y_inc, "y_exp": y_exp}
            g_inc += y_inc
            g_exp += y_exp
        except:
            continue
    return db, (g_inc - g_exp)

# 4. GIAO DIỆN CHÍNH
try:
    # Tự động quét các năm đang có trên Sheets
    dynamic_years = get_dynamic_years()
    data, balance = load_all_data(dynamic_years)
    
    st.markdown(f"""
    <div style="background-color:#1e3a8a; padding:30px; border-radius:15px; border-left: 10px solid #f59e0b; margin-bottom:20px">
        <p style="color:white; margin:0; font-size:16px; font-weight:bold; opacity:0.8">TỔNG SỐ DƯ QUỸ (TẤT CẢ CÁC NĂM)</p>
        <h1 style="color:white; margin:0; font-size:64px; font-weight:bold">{balance:,.0f} <span style="font-size:24px">VND</span></h1>
    </div>
    """, unsafe_allow_html=True)

    y_sel = st.sidebar.selectbox("Chọn năm báo cáo:", dynamic_years[::-1])
    
    if y_sel in data:
        curr = data[y_sel]
        col1, col2, col3 = st.columns(3)
        col1.metric(f"Tổng thu {y_sel}", f"{curr['y_inc']:,.0f} VND")
        col2.metric(f"Tổng chi {y_sel}", f"{curr['y_exp']:,.0f} VND")
        col3.metric("Số dư năm", f"{(curr['y_inc'] - curr['y_exp']):,.0f} VND")

        with st.expander(f"Chi tiết danh sách {y_sel}", expanded=True):
            res = curr["inc_df"].copy()
            for m in MONTHS:
                res[m] = res[m].apply(lambda x: "✔" if x > 0 else "-")
            res = res.reset_index(drop=True)
            res.index = range(1, len(res) + 1)
            res.index.name = "STT"
            st.dataframe(res, use_container_width=True)
            
except Exception as e:
    st.error(f"Lỗi: {e}")
