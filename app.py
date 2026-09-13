import base64
import hashlib
import sqlite3
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Spiritual Trader Pro | Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- THEME CONFIG -----------------
theme_mode = st.sidebar.selectbox("🎨 Display Theme", ["Dark Mode", "Light Mode"])

if theme_mode == "Dark Mode":
    bg_color, text_color, sidebar_bg = "#0b0f19", "#e2e8f0", "#111827"
    metric_bg, border_col = "#1e293b", "#1f2937"
else:
    bg_color, text_color, sidebar_bg = "#f8fafc", "#0f172a", "#f1f5f9"
    metric_bg, border_col = "#ffffff", "#cbd5e1"

st.markdown(f"""
<style>
.stApp {{ background-color: {bg_color}; color: {text_color}; }}
section[data-testid="stSidebar"] {{ background-color: {sidebar_bg}; }}
.stMetric {{ background-color: {metric_bg}; border: 1px solid {border_col}; padding: 15px; border-radius: 10px; }}
</style>
""", unsafe_allow_html=True)

# ----------------- AUTHENTICATION -----------------
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<h2 style='text-align: center;'>⚡ Spiritual Trader Pro</h2>", unsafe_allow_html=True)
        with st.form("login_box"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login", use_container_width=True):
                # अपने क्रेडेंशियल्स सुरक्षित रखें
                if u == "admin" and p == "trader9":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid Credentials!")
    return False

if not check_password():
    st.stop()

# ----------------- DATABASE SETUP -----------------
DB_FILE = "journal.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE,
                trade_date TEXT,
                symbol TEXT,
                trade_type TEXT,
                quantity INTEGER,
                entry_price REAL,
                exit_price REAL,
                stop_loss REAL,
                pnl REAL,
                execution_type TEXT DEFAULT 'MANUAL'
            )
        """)
        c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, val TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS daily_journal (trade_date TEXT PRIMARY KEY, notes TEXT)")
        conn.commit()

init_db()

def get_db_val(k):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT val FROM settings WHERE key = ?", (k,))
        row = c.fetchone()
        return row[0] if row else ""

def set_db_val(k, v):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO settings (key, val) VALUES (?, ?)", (k, str(v)))
        conn.commit()

# ----------------- PROFILE SECTION -----------------
if "profile_pic_b64" not in st.session_state:
    st.session_state["profile_pic_b64"] = get_db_val("profile_pic")

p_pic = st.session_state["profile_pic_b64"]
col_p1, col_p2 = st.sidebar.columns([1, 3])
with col_p1:
    if p_pic:
        st.markdown(f'<img src="data:image/png;base64,{p_pic}" width="50" style="border-radius:50%;">', unsafe_allow_html=True)
    else:
        st.markdown('👤')
with col_p2:
    st.markdown("<b>Mittalkumar M.</b>", unsafe_allow_html=True)

with st.sidebar.expander("📷 Profile Photo", expanded=False):
    up_img = st.file_uploader("Choose Photo", type=["jpg", "png", "jpeg"], key="profile_uploader")
    if up_img is not None:
        b64_data = base64.b64encode(up_img.getvalue()).decode()
        st.session_state["profile_pic_b64"] = b64_data
        set_db_val("profile_pic", b64_data)
        st.success("Photo Updated!")
        st.rerun()

# ----------------- FYERS API INTEGRATION -----------------
st.sidebar.markdown("---")
st.sidebar.markdown("⚡ **Fyers Auto-Pilot Sync**")

app_id_val = st.sidebar.text_input("App ID", value=get_db_val("f_app_id"))
sec_id_val = st.sidebar.text_input("Secret ID", value=get_db_val("f_sec_id"), type="password")
redirect_url = st.sidebar.text_input("Redirect URI", value=get_db_val("f_redir") or "http://localhost:8501")

if st.sidebar.button("Save API Keys"):
    set_db_val("f_app_id", app_id_val)
    set_db_val("f_sec_id", sec_id_val)
    set_db_val("f_redir", redirect_url)
    st.sidebar.success("Keys Saved!")

# Auth Code Exchange
query_params = st.query_params
if "auth_code" in query_params or "code" in query_params:
    auth_code_extracted = query_params.get("auth_code") or query_params.get("code")
    if auth_code_extracted and app_id_val and sec_id_val:
        try:
            hash_v = hashlib.sha256(f"{app_id_val}:{sec_id_val}".encode()).hexdigest()
            val_resp = requests.post(
                "https://api-t1.fyers.in/api/v3/validate-authcode",
                json={
                    "grant_type": "authorization_code",
                    "appIdHash": hash_v,
                    "code": auth_code_extracted.strip()
                },
                timeout=10
            ).json()
            if val_resp.get("s") == "ok":
                set_db_val("f_token", val_resp["access_token"])
                st.query_params.clear()
                st.sidebar.success("Connected to FYERS!")
                st.rerun()
            else:
                st.sidebar.error(f"Auth Error: {val_resp.get('message', 'Failed')}")
        except Exception as e:
            st.sidebar.error(f"Request Error: {e}")

if app_id_val and redirect_url:
    login_target_url = f"https://api-t1.fyers.in/api/v3/generate-authcode?client_id={app_id_val}&redirect_uri={redirect_url}&response_type=code&state=sample_state"
    st.sidebar.markdown(f'<a href="{login_target_url}" target="_self"><button style="width:100%;background-color:#16a34a;color:white;padding:8px;border:none;border-radius:5px;cursor:pointer;font-weight:bold;">Login with FYERS</button></a>', unsafe_allow_html=True)

live_tok = get_db_val("f_token")
if live_tok:
    st.sidebar.success("● Live Token Active")

# Fetch Funds and Auto-Sync Tradebook
default_capital = float(get_db_val("tot_cap") or 10000.0)
if app_id_val and live_tok:
    headers_dict = {"Authorization": f"{app_id_val}:{live_tok}"}
    
    # 1. Fetch Balance
    try:
        funds_resp = requests.get("https://api-t1.fyers.in/api/v3/funds", headers=headers_dict, timeout=5).json()
        if funds_resp.get("s") == "ok":
            for item in funds_resp.get("fund_limit", []):
                if item.get("title") in ["Total Balance", "Client Balance"]:
                    bal = float(item.get("equityAmount", 0.0))
                    if bal > 0:
                        default_capital = bal
    except Exception:
        pass

    # 2. Sync Trades safely (Prevent Duplicates)
    if st.sidebar.button("🔄 Sync TradeBook Now"):
        try:
            trades_resp = requests.get("https://api-t1.fyers.in/api/v3/tradebook", headers=headers_dict, timeout=5).json()
            if trades_resp.get("s") == "ok":
                with sqlite3.connect(DB_FILE) as conn_db:
                    cur_db = conn_db.cursor()
                    added_count = 0
                    for t in trades_resp.get("tradeBook", []):
                        t_num = str(t.get("tradeNumber", t.get("id", "")))
                        sym_name = t.get("symbol", "NIFTY")
                        t_side = "BUY" if t.get("side") == 1 else "SELL"
                        t_qty = int(t.get("tradedQty", 0))
                        t_prc = float(t.get("tradePrice", 0.0))
                        t_time = str(t.get("tradeTime", datetime.now().strftime("%Y-%m-%d")))[:10]

                        # INSERT OR IGNORE avoids duplicate records based on trade_id
                        cur_db.execute("""
                            INSERT OR IGNORE INTO trades 
                            (trade_id, trade_date, symbol, trade_type, quantity, entry_price, exit_price, stop_loss, pnl, execution_type) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (t_num, t_time, sym_name, t_side, t_qty, t_prc, t_prc, 0.0, 0.0, "FYERS_API"))
                        if cur_db.rowcount > 0:
                            added_count += 1
                    conn_db.commit()
                st.sidebar.info(f"Synced! Added {added_count} new trades.")
        except Exception as e:
            st.sidebar.error(f"Sync failed: {e}")

st.sidebar.markdown("---")
total_capital = st.sidebar.number_input("Trading Capital (₹)", min_value=1000.0, value=default_capital, step=1000.0)
set_db_val("tot_cap", str(total_capital))

# ----------------- TABS & INTERFACE -----------------
st.title("⚡ Spiritual Trader Pro | Terminal")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📝 Manual Trade Entry", "📈 Analytics & Book", "🧘 Mindset Journal"])

with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("Current Capital", f"₹{total_capital:,.2f}")
    c2.metric("Max Trades/Day", "3 Trades")
    c3.metric("Max Daily Risk", f"₹{(total_capital * 0.02):,.2f} (2%)")

with tab2:
    with st.form("manual_trade_form"):
        col1, col2 = st.columns(2)
        with col1:
            m_sym = st.text_input("Symbol", value="NSE:NIFTY50-INDEX")
            m_side = st.selectbox("Action", ["BUY", "SELL"])
            m_qty = st.number_input("Quantity", min_value=1, value=50)
        with col2:
            m_entry = st.number_input("Entry Price", min_value=0.01, value=100.0)
            m_exit = st.number_input("Exit Price", min_value=0.01, value=120.0)
            m_sl = st.number_input("Stop Loss", min_value=0.0, value=90.0)

        if st.form_submit_button("Save Trade Entry"):
            pnl_calc = (m_exit - m_entry) * m_qty if m_side == "BUY" else (m_entry - m_exit) * m_qty
            t_id_manual = f"MANUAL_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            with sqlite3.connect(DB_FILE) as conn:
                c = conn.cursor()
                c.execute("""
                    INSERT INTO trades (trade_id, trade_date, symbol, trade_type, quantity, entry_price, exit_price, stop_loss, pnl, execution_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (t_id_manual, datetime.now().strftime("%Y-%m-%d"), m_sym, m_side, m_qty, m_entry, m_exit, m_sl, pnl_calc, "MANUAL"))
                conn.commit()
            st.success("Trade recorded!")

with tab3:
    with sqlite3.connect(DB_FILE) as conn:
        df_trades = pd.read_sql("SELECT trade_date, symbol, trade_type, quantity, entry_price, exit_price, pnl, execution_type FROM trades ORDER BY id DESC", conn)
    
    if not df_trades.empty:
        total_pnl = df_trades["pnl"].sum()
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Net Realized P&L", f"₹{total_pnl:,.2f}")
        col_m2.metric("Total Executions", len(df_trades))
        st.dataframe(df_trades, use_container_width=True)
    else:
        st.info("No trade data available yet.")

with tab4:
    d_str = datetime.now().strftime("%Y-%m-%d")
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT notes FROM daily_journal WHERE trade_date = ?", (d_str,))
        existing_note = c.fetchone()
        current_text = existing_note[0] if existing_note else ""

    mind_notes = st.text_area("Today's Execution Mindset & Rules Review:", value=current_text, height=150)
    if st.button("Save Daily Journal"):
        with sqlite3.connect(DB_FILE) as conn:
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO daily_journal (trade_date, notes) VALUES (?, ?)", (d_str, mind_notes))
            conn.commit()
        st.success("Journal saved successfully!")
