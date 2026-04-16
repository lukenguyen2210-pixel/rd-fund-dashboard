import streamlit as st
import pandas as pd

# 1. THIẾT LẬP GIAO DIỆN
st.set_page_config(page_title="R&D Fund Master", layout="wide")

SHEET_ID = "1xSTOFCGZ2vVEHz5CZV7fP4rpnNnKK9-6guGu5EIMdX0"
MONTHS = ["Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar"]

def clean_money(v):
    if pd.isna(v) or str(v).strip() in ["", "-", "0", "0.0"]: return 0
    s = str(v).lower().replace('đ', '').replace(',', '').replace('.', '').replace(' ', '').strip()
    try: return float(s)
    except: return 0

# 2. LOGIC TỰ ĐỘNG DÒ TÌM CÁC NĂM
@st.cache_data(ttl=5)
def load_all_years_data():
    db = {}
    g_inc, g_exp = 0, 0
    # Dò từ năm 2025 đến 2035. Bro thích thì tăng lên 2050 cũng được.
    potential_years = [str(y) for y in range(2025, 2036)]
    found_years = []

    for y in potential_years:
        try:
            url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={y}"
            # Thiết lập timeout ngắn để nếu sheet không tồn tại nó sẽ bỏ qua nhanh
            df_raw = pd.read_csv(url, header=None, timeout=3)
            
            # --- XỬ LÝ THU (B3:N43) ---
            # Index 1:14 là cột B đến N. Index 2:43 là dòng 3 đến 43.
            df_inc = df_raw.iloc[2:43, 1:14].copy()
            df_inc.columns = ["Full Name"] + MONTHS
            
            # Làm sạch dữ liệu và lọc dòng rác (tránh mất chị Nhung)
            df_inc = df_inc.dropna(subset=["Full Name"])
            df_inc["Full Name"] = df_inc["Full Name"].astype(str).str.strip()
            df_inc = df_inc[df_inc["Full Name"].str.len() > 1]
            
            for m in MONTHS:
                df_inc[m] = df_inc[m].apply(clean_money)
            
            y_inc = df_inc[MONTHS].sum().sum()
            
            # --- XỬ LÝ CHI (Q3:S43) ---
            df_ex = df_raw.iloc[2:43, 16:19].copy()
            df_ex.columns = ['Date', 'Amount', 'Explanation']
            df_ex['Amount'] = df_ex['Amount'].apply(clean_money)
            df_ex = df_ex[df_ex['Amount'] > 0].dropna(subset=['Explanation'])
            y_exp = df_ex['Amount'].sum()
            
            db[y] = {"inc_df": df_inc, "exp_df": df_ex, "y_inc": y_inc, "y_exp": y_exp}
            g_inc += y_inc
            g_exp += y_exp
            found_years.append(y)
        except:
            # Nếu không tìm thấy sheet (404), Python sẽ bỏ qua và chạy tiếp năm sau
            continue
            
    return db, (g_inc - g_exp), sorted(found_years, reverse=True)

# 3. HIỂN THỊ LÊN APP
try:
    data_db, total_balance, years_list = load_all_years_data()

    # Banner Số dư tổng (Giữ UI bro thích)
    st.markdown(f"""
    <div style="background-color:#1e3a8a; padding:30px; border-radius:15px; border-left: 10px solid #f59e0b; margin-bottom:25px">
        <p style="color:white; margin:0; font-size:16px; font-weight:bold; opacity:0.8">TỔNG SỐ DƯ QUỸ (ALL YEARS)</p>
        <h1 style="color:white; margin:0; font-size:64px; font-weight:bold">{total_balance:,.0f} <span style="font-size:24px">VND</span></h1>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar chọn năm - Tự động cập nhật danh sách year
    y_sel = st.sidebar.selectbox("Chọn năm xem chi tiết:", years_list)
    curr = data_db[y_sel]

    # Metrics nhanh
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Thu {y_sel}", f"{curr['y_inc']:,.0f}")
    c2.metric(f"Chi {y_sel}", f"{curr['y_exp']:,.0f}")
    c3.metric("Còn lại", f"{(curr['y_inc'] - curr['y_exp']):,.0f}")

    # Bảng chi tiết
    with st.expander(f"Bảng danh sách đóng quỹ {y_sel}", expanded=True):
        res = curr["inc_df"].copy()
        for m in MONTHS:
            res[m] = res[m].apply(lambda x: "✔" if x > 0 else "-")
        
        # Đánh STT từ 1 và căn lề trái mặc định
        res = res.reset_index(drop=True)
        res.index = range(1, len(res) + 1)
        res.index.name = "STT"
        st.dataframe(res, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi: {e}")
