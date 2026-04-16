import streamlit as st
import pandas as pd

# 1. CẤU HÌNH TRANG & GIAO DIỆN
st.set_page_config(page_title="R&D Fund Master", layout="wide")

SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"
# Danh sách tháng chuẩn để gán nhãn cố định
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]

def clean_money(v):
    if pd.isna(v) or str(v).strip() in ["", "-", "0", "0.0"]: return 0
    s = str(v).lower().replace('đ', '').replace(',', '').replace('.', '').replace(' ', '').strip()
    try: return float(s)
    except: return 0

# 2. TỰ ĐỘNG LẤY DANH SÁCH CÁC NĂM (SHEETS)
@st.cache_data(ttl=60)
def get_all_years():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=xlsx"
        all_sheets = pd.read_excel(url, sheet_name=None)
        # Lọc các sheet có tên là số (2025, 2026, 2027...)
        years = [s for s in all_sheets.keys() if str(s).isdigit()]
        return sorted(years)
    except:
        return ["2025", "2026"] # Fallback nếu không quét được

# 3. LOAD DỮ LIỆU CHI TIẾT
@st.cache_data(ttl=5)
def load_data(years_list):
    db = {}
    g_inc, g_exp = 0, 0
    for y in years_list:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}"
        df_raw = pd.read_csv(url, header=None)
        
        # --- THU (B3:N43) - Dòng 3 là index 2 ---
        # Bốc rộng hơn 1 chút rồi lọc để đảm bảo không mất người đầu tiên
        df_temp = df_raw.iloc[1:45, 1:14].copy()
        df_temp.columns = ["Full Name"] + MONTHS
        
        # Lọc bỏ dòng tiêu đề và dòng rác
        df_inc = df_temp[~df_temp["Full Name"].astype(str).str.contains("Full Name|Tên NV|No\.|STT", na=False, case=False)].copy()
        df_inc = df_inc.dropna(subset=["Full Name"])
        df_inc["Full Name"] = df_inc["Full Name"].astype(str).str.strip()
        df_inc = df_inc[df_inc["Full Name"].str.len() > 1]
        df_inc = df_inc.head(41) # Khóa đúng số lượng dòng tối đa
        
        for m in MONTHS:
            df_inc[m] = df_inc[m].apply(clean_money)
        y_inc = df_inc[MONTHS].sum().sum()
        
        # --- CHI (Q3:S43) - Cột Q là index 16 ---
        df_ex = df_raw.iloc[2:45, 16:19].copy()
        df_ex.columns = ['Date', 'Amount', 'Explanation']
        df_ex['Amount'] = df_ex['Amount'].apply(clean_money)
        df_ex = df_ex[df_ex['Amount'] > 0].dropna(subset=['Explanation'])
        y_exp = df_ex['Amount'].sum()
        
        db[y] = {"inc_df": df_inc, "exp_df": df_ex, "y_inc": y_inc, "y_exp": y_exp}
        g_inc += y_inc
        g_exp += y_exp
        
    return db, (g_inc - g_exp)

# 4. HIỂN THỊ GIAO DIỆN
try:
    available_years = get_all_years()
    data, balance = load_data(available_years)
    
    # Header số dư tổng
    st.markdown(f"""
    <div style="background-color:#1e3a8a; padding:30px; border-radius:15px; border-left: 10px solid #f59e0b; margin-bottom:20px">
        <p style="color:white; margin:0; font-size:16px; font-weight:bold; opacity:0.8">TỔNG SỐ DƯ QUỸ HIỆN TẠI</p>
        <h1 style="color:white; margin:0; font-size:64px; font-weight:bold">{balance:,.0f} <span style="font-size:24px">VND</span></h1>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar chọn năm
    y_sel = st.sidebar.selectbox("Chọn năm xem dữ liệu:", available_years[::-1])
    curr = data[y_sel]
    
    # Chỉ số nhanh theo năm
    col1, col2, col3 = st.columns(3)
    col1.metric(f"Tổng thu {y_sel}", f"{curr['y_inc']:,.0f} VND")
    col2.metric(f"Tổng chi {y_sel}", f"{curr['y_exp']:,.0f} VND")
    col3.metric("Còn lại trong năm", f"{(curr['y_inc'] - curr['y_exp']):,.0f} VND")

    # Bảng chi tiết đóng quỹ
    with st.expander(f"Chi tiết danh sách đóng quỹ {y_sel}", expanded=True):
        res = curr["inc_df"].copy()
        for m in MONTHS:
            res[m] = res[m].apply(lambda x: "✔" if x > 0 else "-")
        
        # Reset STT chuẩn
        res = res.reset_index(drop=True)
        res.index = range(1, len(res) + 1)
        res.index.name = "STT"
        
        # Căn lề trái mặc định cho text, bảng rộng hết cỡ
        st.dataframe(res, use_container_width=True)

    # Bảng chi tiết chi tiêu (Option thêm cho đầy đủ)
    if not curr["exp_df"].empty:
        with st.expander(f"Lịch sử chi tiêu {y_sel}"):
            st.table(curr["exp_df"])

except Exception as e:
    st.error(f"Đã xảy ra lỗi hệ thống: {e}")
