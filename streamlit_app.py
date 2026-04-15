import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="R&D Fund Master Pro", layout="wide")

SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
YEARS_LIST = ["2025", "2026"]
STANDARD_FEE = 100000

def clean_money(value):
    if pd.isna(value) or str(value).strip() == "":
        return 0
    s = str(value).lower().replace('đ', '').replace(',', '').replace('.', '').replace(' ', '').strip()
    try:
        return float(s)
    except:
        return 0

@st.cache_data(ttl=300)
def fetch_all_data():
    all_data = {}
    total_g_income = 0
    total_g_expense = 0
    
    for y in YEARS_LIST:
        # Load Thu: Quét từ B2 để lấy được cả tên những người không có STT
        url_inc = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}&range=B2:N43"
        df_inc = pd.read_csv(url_inc, header=None)
        df_inc.columns = ["Full Name"] + MONTHS
        
        # Loại bỏ dòng rác (Tiêu đề hoặc dòng tổng)
        exclude = ['Full Name', 'Tên NV', 'SUM', 'Tổng cộng', 'Total', 'nan']
        df_inc = df_inc.dropna(subset=["Full Name"])
        df_inc = df_inc[~df_inc["Full Name"].astype(str).str.contains('|'.join(exclude), case=False, na=False)]
        
        # Đảm bảo tên không bị dính chùm (Trường hợp gộp ô trong Sheets)
        df_inc["Full Name"] = df_inc["Full Name"].astype(str).str.strip()
        
        for col in MONTHS:
            df_inc[col] = df_inc[col].apply(clean_money)
        
        y_inc_val = df_inc[MONTHS].sum().sum()
        
        # Load Chi: Cột Q(Date), R(Amount), S(Explanation)
        url_exp = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}&range=Q3:S43"
        df_ex = pd.read_csv(url_exp, header=None)
        y_exp_val = 0
        if not df_ex.empty:
            df_ex.columns = ['Date', 'Amount', 'Explanation']
            df_ex['Amount'] = df_ex['Amount'].apply(clean_money)
            # Lọc bỏ dòng trống hoặc dòng tổng cộng ở cuối
            df_ex = df_ex[df_ex['Amount'] > 0].dropna(subset=['Explanation'])
            y_exp_val = df_ex['Amount'].sum()
            
        all_data[y] = {"income_df": df_inc, "expense_df": df_ex, "y_inc": y_inc_val, "y_exp": y_exp_val}
        total_g_income += y_inc_val
        total_g_expense += y_exp_val
        
    return all_data, (total_g_income - total_g_expense)

# --- GIAO DIỆN ---
try:
    data_store, grand_balance = fetch_all_data()
    st.title("🚀 R&D Fund Master Dashboard")

    # Hiển thị Tổng số dư cực lớn
    st.markdown(f"""
    <div style="background-color:#1e3a8a; padding:30px; border-radius:15px; border-left: 10px solid #f59e0b; margin-bottom:30px">
        <p style="color:white; margin:0; font-size:16px; font-weight:bold; opacity:0.8; text-transform:uppercase">Tổng số dư quỹ (2025 + 2026)</p>
        <h1 style="color:white; margin:0; font-size:64px; font-weight:bold">{grand_balance:,.0f} <span style="font-size:24px">VND</span></h1>
    </div>
    """, unsafe_allow_html=True)

    year_choice = st.sidebar.selectbox("Chọn năm tài chính:", YEARS_LIST[::-1])
    curr = data_store[year_choice]
    
    # 3 Cột chỉ số nhanh
    c1, c2, c3 = st.columns(3)
    c1.metric("Thu năm nay", f"{curr['y_inc']:,.0f} VND")
    c2.metric("Chi năm nay", f"{curr['y_exp']:,.0f} VND")
    c3.metric("Còn lại", f"{(curr['y_inc'] - curr['y_exp']):,.0f} VND")

    # Bảng chi tiết đóng quỹ
    with st.expander(f"Bảng chi tiết đóng quỹ {year_choice}", expanded=True):
        df_display = curr["income_df"].copy()
        for col in MONTHS:
            df_display[col] = df_display[col].apply(lambda x: "✔" if x > 0 else "-")
        df_display.index = range(1, len(df_display) + 1)
        df_display.index.name = "STT"
        st.dataframe(df_display, use_container_width=True)

    # Bảng nhật ký chi tiêu
    with st.expander(f"Nhật ký chi tiêu {year_choice}"):
        if not curr["expense_df"].empty:
            df_exp_view = curr["expense_df"].copy()
            df_exp_view.index = range(1, len(df_exp_view) + 1)
            df_exp_view['Amount'] = df_exp_view['Amount'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(df_exp_view, use_container_width=True)
        else:
            st.info("Chưa có phát sinh chi tiêu trong năm này.")

except Exception as e:
    st.error(f"Lỗi hệ thống: {e}")
