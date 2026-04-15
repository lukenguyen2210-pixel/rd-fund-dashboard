import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="R&D Fund Master Pro", layout="wide")

SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"
STANDARD_FEE = 100000
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]
YEARS_LIST = ["2025", "2026"] # Bro có thể thêm năm vào đây

def clean_money(value):
    if pd.isna(value) or str(value).strip() == "":
        return 0
    s = str(value).lower()
    s = s.replace('đ', '').replace(',', '').replace('.', '').replace(' ', '').strip()
    try:
        return float(s)
    except:
        return 0

@st.cache_data(ttl=600) # Lưu bộ nhớ tạm 10p để load cho nhanh
def get_year_stats(year_str):
    """Hàm phụ để tính nhanh số dư của một năm cụ thể"""
    try:
        # Load Thu
        url_inc = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={year_str}&range=C3:N43"
        df_inc = pd.read_csv(url_inc, header=None)
        inc = df_inc.applymap(clean_money).sum().sum()
        
        # Load Chi
        url_exp = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={year_str}&range=R3:R43"
        df_exp = pd.read_csv(url_exp, header=None)
        exp = df_exp[0].apply(clean_money).sum()
        
        return inc, exp
    except:
        return 0, 0

def get_detailed_data(year_choice):
    # Lấy dữ liệu Thu chi tiết (B3:N43)
    url_income = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={year_choice}&range=B3:N43"
    df_inc = pd.read_csv(url_income, header=None)
    df_inc.columns = ["Full Name"] + MONTHS
    
    if not df_inc.empty and str(df_inc.iloc[0, 0]).count(" ") > 5:
        df_inc = df_inc.iloc[1:].reset_index(drop=True)

    exclude = ["SUM", "Tổng cộng", "Tên NV", "Total", "TOTAL", "nan"]
    df_inc = df_inc.dropna(subset=["Full Name"])
    df_inc = df_inc[~df_inc["Full Name"].astype(str).str.contains('|'.join(exclude), case=False, na=False)]
    
    for col in MONTHS:
        df_inc[col] = df_inc[col].apply(clean_money)
    
    # Lấy dữ liệu Chi chi tiết (Q3:S43)
    url_exp = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={year_choice}&range=Q3:S43"
    df_ex = pd.read_csv(url_exp, header=None)
    if not df_ex.empty:
        df_ex.columns = ['Date', 'Amount', 'Explanation']
        df_ex['Amount'] = df_ex['Amount'].apply(clean_money)
        df_ex = df_ex[df_ex['Amount'] > 0].dropna(subset=['Explanation'])

    return df_inc, df_ex

# --- GIAO DIỆN CHÍNH ---
st.title("🚀 R&D Fund Master Dashboard")

# 1. TÍNH TỔNG SỐ DƯ TẤT CẢ CÁC NĂM (Grand Total)
grand_income = 0
grand_expense = 0
for y in YEARS_LIST:
    y_inc, y_exp = get_year_stats(y)
    grand_income += y_inc
    grand_expense += y_exp

grand_balance = grand_income - grand_expense

# Hiển thị số dư tổng ngay trên đầu
st.markdown(f"""
<div style="background-color:#1e3a8a; padding:20px; border-radius:10px; border-left: 10px solid #f59e0b; margin-bottom:25px">
    <h3 style="color:white; margin:0; font-size:16px; opacity:0.8">TỔNG SỐ DƯ QUỸ HIỆN TẠI (ALL YEARS)</h3>
    <h1 style="color:white; margin:0; font-size:42px">{grand_balance:,.0f} <span style="font-size:20px">VND</span></h1>
</div>
""", unsafe_allow_html=True)

# 2. LỰA CHỌN CHI TIẾT TỪNG NĂM
year = st.sidebar.selectbox("Xem chi tiết năm tài chính:", YEARS_LIST[::-1])

try:
    df_members, df_expense = get_detailed_data(year)
    
    total_income = df_members[MONTHS].sum().sum()
    total_expense = df_expense['Amount'].sum() if not df_expense.empty else 0
    balance = total_income - total_expense
    
    st.subheader(f"📍 Chi tiết tài chính năm {year}")
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Thu năm {year}", f"{total_income:,.0f} VND")
    c2.metric(f"Chi năm {year}", f"{total_expense:,.0f} VND")
    c3.metric(f"Số dư {year}", f"{balance:,.0f} VND")

    # Biểu đồ tiến độ
    fig = go.Figure(data=[
        go.Bar(name='Đã thu', x=MONTHS, y=df_members[MONTHS].sum(), marker_color='#1e3a8a'),
        go.Bar(name='Còn thiếu', x=MONTHS, y=[max(0, (len(df_members)*STANDARD_FEE) - v) for v in df_members[MONTHS].sum()], marker_color='#f59e0b')
    ])
    fig.update_layout(barmode='stack', height=300, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, use_container_width=True)

    # Bảng chi tiết đóng quỹ
    with st.expander(f"Xem danh sách đóng quỹ {year}", expanded=True):
        df_display = df_members.copy()
        for col in MONTHS:
            df_display[col] = df_display[col].apply(lambda x: "✔" if x > 0 else "-")
        df_display.index = range(1, len(df_display) + 1)
        df_display.index.name = "STT"
        st.dataframe(df_display[["Full Name"] + MONTHS], use_container_width=True)

    # Nhật ký chi tiêu
    with st.expander(f"Xem nhật ký chi tiêu {year}"):
        if not df_expense.empty:
            df_exp_show = df_expense.copy()
            df_exp_show.index = range(1, len(df_exp_show) + 1)
            df_exp_show['Amount'] = df_exp_show['Amount'].apply(lambda x: f"{x:,.0f}")
            st.dataframe(df_exp_show, use_container_width=True)
        else:
            st.write("Không có dữ liệu chi tiêu.")

except Exception as e:
    st.error(f"Lỗi: {e}")
