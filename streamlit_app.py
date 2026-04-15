import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="R&D Fund Master Pro", layout="wide")

# Cấu hình ID và Danh sách năm
SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
YEARS_LIST = ["2025", "2026"]
STANDARD_FEE = 100000

def clean_money(value):
    """Xử lý triệt để tiền tệ rác"""
    if pd.isna(value) or str(value).strip() == "":
        return 0
    s = str(value).lower()
    s = s.replace('đ', '').replace(',', '').replace('.', '').replace(' ', '').strip()
    try:
        return float(s)
    except:
        return 0

@st.cache_data(ttl=300)
def fetch_all_data():
    """Tải và tính toán toàn bộ dữ liệu"""
    all_data = {}
    total_g_income = 0
    total_g_expense = 0
    
    for y in YEARS_LIST:
        # 1. Load Thu (B3:N43)
        url_inc = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}&range=B3:N43"
        df_inc = pd.read_csv(url_inc, header=None)
        df_inc.columns = ["Full Name"] + MONTHS
        
        # Lọc rác
        df_inc = df_inc.dropna(subset=["Full Name"])
        df_inc = df_inc[~df_inc["Full Name"].astype(str).str.contains('SUM|Tổng cộng|Tên NV|Total|nan', case=False, na=False)]
        
        for col in MONTHS:
            df_inc[col] = df_inc[col].apply(clean_money)
        
        y_inc_val = df_inc[MONTHS].sum().sum()
        
        # 2. Load Chi (Q3:S43)
        url_exp = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}&range=Q3:S43"
        df_ex = pd.read_csv(url_exp, header=None)
        y_exp_val = 0
        if not df_ex.empty:
            df_ex.columns = ['Date', 'Amount', 'Explanation']
            df_ex['Amount'] = df_ex['Amount'].apply(clean_money)
            df_ex = df_ex[df_ex['Amount'] > 0].dropna(subset=['Explanation'])
            y_exp_val = df_ex['Amount'].sum()
            
        all_data[y] = {"income_df": df_inc, "expense_df": df_ex, "y_inc": y_inc_val, "y_exp": y_exp_val}
        total_g_income += y_inc_val
        total_g_expense += y_exp_val
        
    return all_data, (total_g_income - total_g_expense)

# --- THỰC THI ---
try:
    data_store, grand_balance = fetch_all_data()

    # --- GIAO DIỆN ---
    st.title("🚀 R&D Fund Master Dashboard")

    # FIX LỖI: Đổi unsafe_allow_True thành unsafe_allow_html=True
    st.markdown(f"""
    <div style="background-color:#1e3a8a; padding:25px; border-radius:15px; border-left: 10px solid #f59e0b; margin-bottom:30px">
        <p style="color:white; margin:0; font-size:14px; font-weight:bold; opacity:0.8; text-transform:uppercase; letter-spacing:1px">Tổng số dư quỹ (Tất cả các năm)</p>
        <h1 style="color:white; margin:0; font-size:54px; font-weight:bold">{grand_balance:,.0f} <span style="font-size:22px">VND</span></h1>
    </div>
    """, unsafe_allow_html=True)

    year_choice = st.sidebar.selectbox("Chọn năm xem báo cáo:", YEARS_LIST[::-1])
    current_year_data = data_store[year_choice]
    
    # Hiển thị Metrics năm hiện tại
    st.subheader(f"📍 Báo cáo tài chính năm {year_choice}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Thu trong năm", f"{current_year_data['y_inc']:,.0f} VND")
    c2.metric("Chi trong năm", f"{current_year_data['y_exp']:,.0f} VND")
    c3.metric("Số dư năm này", f"{(current_year_data['y_inc'] - current_year_data['y_exp']):,.0f} VND")

    # Biểu đồ
    st.plotly_chart(go.Figure(data=[
        go.Bar(name='Đã thu', x=MONTHS, y=current_year_data["income_df"][MONTHS].sum(), marker_color='#1e3a8a'),
        go.Bar(name='Còn thiếu', x=MONTHS, y=[max(0, (len(current_year_data["income_df"])*STANDARD_FEE) - v) for v in current_year_data["income_df"][MONTHS].sum()], marker_color='#f59e0b')
    ]).update_layout(barmode='stack', height=350, margin=dict(l=0, r=0, t=20, b=0)), use_container_width=True)

    # Bảng chi tiết
    with st.expander(f"Chi tiết đóng quỹ {year_choice}", expanded=True):
        df_tick = current_year_data["income_df"].copy()
        for col in MONTHS:
            df_tick[col] = df_tick[col].apply(lambda x: "✔" if x > 0 else "-")
        df_tick.index = range(1, len(df_tick) + 1)
        df_tick.index.name = "STT"
        st.dataframe(df_tick[["Full Name"] + MONTHS], use_container_width=True)

    # Nhật ký chi tiêu
    with st.expander(f"Nhật ký chi tiêu {year_choice}"):
        df_exp_show = current_year_data["expense_df"].copy()
        if not df_exp_show.empty:
            df_exp_show.index = range(1, len(df_exp_show) + 1)
            df_exp_show.index.name = "STT"
            df_exp_show['Amount'] = df_exp_show['Amount'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(df_exp_show, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu chi tiêu.")

except Exception as e:
    st.error(f"Đã xảy ra lỗi: {e}")
