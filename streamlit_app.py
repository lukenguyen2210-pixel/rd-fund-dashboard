import streamlit as st
import pandas as pd

st.set_page_config(page_title="R&D Fund Master Pro", layout="wide")

SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"
# Danh sách tháng khớp chuẩn thứ tự C->N
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

@st.cache_data(ttl=30) # Giảm TTL để load nhanh hơn khi debug
def fetch_all_data():
    all_data = {}
    total_g_income = 0
    total_g_expense = 0
    
    for y in YEARS_LIST:
        # Range B3:N43 để lấy từ tên đến hết 12 tháng, né dòng SUM 44
        url_inc = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}&range=B3:N43"
        
        # Đọc dữ liệu và không lấy dòng đầu làm header để tránh lệch cột
        df_raw = pd.read_csv(url_inc, header=None)
        
        # Chỉ lấy 13 cột đầu tiên (Cột B + 12 tháng) để tránh cột Unnamed rác
        df_inc = df_raw.iloc[:, :13].copy()
        df_inc.columns = ["Full Name"] + MONTHS
        
        # Loại bỏ dòng trống hoặc dòng có tên quá dài (do gộp ô Nhung-Hiếu-Long)
        df_inc = df_inc.dropna(subset=["Full Name"])
        df_inc = df_inc[df_inc["Full Name"].astype(str).map(len) < 35]
        df_inc = df_inc[~df_inc["Full Name"].astype(str).str.contains("Tên NV|SUM|Tổng cộng", case=False, na=False)]
        
        # Chuyển đổi tiền
        for col in MONTHS:
            df_inc[col] = df_inc[col].apply(clean_money)
            
        y_inc_val = df_inc[MONTHS].sum().sum()
        
        # Load Chi tiêu (Cột Q đến S)
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

# --- UI GIỮ NGUYÊN ---
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
    c1.metric("Thu năm nay", f"{curr['y_inc']:,.0f} VND")
    c2.metric("Chi năm nay", f"{curr['y_exp']:,.0f} VND")
    c3.metric("Còn lại", f"{(curr['y_inc'] - curr['y_exp']):,.0f} VND")

    with st.expander(f"Chi tiết đóng quỹ {year_choice}", expanded=True):
        res = curr["income_df"].copy()
        for m in MONTHS:
            res[m] = res[m].apply(lambda x: "✔" if x > 0 else "-")
        res.index = range(1, len(res) + 1)
        res.index.name = "STT"
        st.dataframe(res, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi: {e}")
    st.info("Bro kiểm tra lại quyền chia sẻ link Google Sheets nhé!")
