
import base64
import hashlib
import io
import os
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pyotp
import requests
import streamlit as st

st.set_page_config(
    page_title="Spiritual Trader Pro | Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

theme_mode = st.sidebar.selectbox("🎨 Display Theme", ["Dark Mode", "Light Mode"])

if theme_mode == "Dark Mode":
    bg_color = "#0b0f19"
    text_color = "#e2e8f0"
    sidebar_bg = "#111827"
    metric_bg = "#1e293b"
    tab_bg = "#161f30"
    border_col = "#1f2937"
    plotly_template = "plotly_dark"
else:
    bg_color = "#f8fafc"
    text_color = "#0f172a"
    sidebar_bg = "#f1f5f9"
    metric_bg = "#ffffff"
    tab_bg = "#e2e8f0"
    border_col = "#cbd5e1"
    plotly_template = "plotly"

st.markdown(f"""
<style>
.stApp {{ background-color: {bg_color}; color: {text_color}; }}
section[data-testid="stSidebar"] {{ background-color: {sidebar_bg}; }}
.stMetric {{ background-color: {metric_bg}; border: 1px solid {border_col}; padding: 15px; border-radius: 10px; }}
</style>
""", unsafe_allow_html=True)

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
                if u == "admin" and p == "trader9":
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("ખોટો પાસવર્ડ!")
    return False

if not check_password():
    st.stop()

FIXED_MAX_TRADES = 3
FIXED_MAX_LOSS = 1000.0
FIXED_RISK_PERCENT = 3.0

def init_db():
    conn = sqlite3.connect("journal.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY AUTOINCREMENT, trade_date TEXT, session TEXT, timeframe TEXT, symbol TEXT, trade_type TEXT, quantity INTEGER, entry_price REAL, exit_price REAL, stop_loss REAL, target_price REAL, risk_reward REAL, pnl REAL, setup_type TEXT, entry_emotion TEXT, exit_reason TEXT, rule_followed TEXT, trade_grade TEXT, setup_notes TEXT, execution_type TEXT DEFAULT 'MANUAL', chart_img TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, val TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS daily_journal (trade_date TEXT PRIMARY KEY, notes TEXT)")
    try:
        c.execute("ALTER TABLE trades ADD COLUMN chart_img TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

init_db()

def get_db_val(k):
    conn = sqlite3.connect("journal.db")
    c = conn.cursor()
    c.execute("SELECT val FROM settings WHERE key = ?", (k,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else ""

def set_db_val(k, v):
    conn = sqlite3.connect("journal.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, val) VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()

if "profile_pic_b64" not in st.session_state:
    st.session_state["profile_pic_b64"] = get_db_val("profile_pic")

p_pic = st.session_state["profile_pic_b64"]

col_p1, col_p2 = st.sidebar.columns([1, 3])
with col_p1:
    if p_pic:
        st.markdown(f'<img src="data:image/png;base64,{p_pic}" width="50" style="border-radius:50%;">', unsafe_allow_html=True)
    else:
        st.markdown('👤', unsafe_allow_html=True)
with col_p2:
    st.markdown("<b>Mittalkumar M.</b>", unsafe_allow_html=True)

with st.sidebar.expander("📷 Profile Photo", expanded=False):
    up_img = st.file_uploader("Choose Photo", type=["jpg", "png", "jpeg"], key="profile_uploader")
    if up_img is not None:
        try:
            b64_data = base64.b64encode(up_img.getvalue()).decode()
            st.session_state["profile_pic_b64"] = b64_data
            set_db_val("profile_pic", b64_data)
            st.success("ફોટો સેવ થઈ ગયો!")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("⚡ Fyers Auto-Pilot Sync", unsafe_allow_html=True)
app_id_val = st.sidebar.text_input("App ID", value=get_db_val("f_app_id") or "8THHZH0S7K-200")
sec_id_val = st.sidebar.text_input("Secret ID", value=get_db_val("f_sec_id") or "RVdcb1TLXE7r9ftE", type="password")

query_params = st.query_params
if "code" in query_params:
    auth_code_extracted = query_params["code"]
    if auth_code_extracted and app_id_val and sec_id_val:
        try:
            hash_v = hashlib.sha256(f"{app_id_val}:{sec_id_val}".encode()).hexdigest()
            val_resp = requests.post("https://api-t1.fyers.in/api/v3/validate-authcode", json={
                "grant_type": "authorization_code",
                "appIdHash": hash_v,
                "code": auth_code_extracted.strip()
            }).json()
            if val_resp.get("s") == "ok":
                set_db_val("f_token", val_resp["access_token"])
                st.query_params.clear()
                st.success("Auto-Connected Successfully!")
                st.rerun()
        except Exception:
            pass

with st.sidebar.expander("🚀 One-Click Auto Login", expanded=True):
    login_target_url = f"https://api.fyers.in/api/v3/generate-authcode?client_id={app_id_val}&redirect_uri=https://trade.fyers.in/api-login/redirect-uri/index.html&response_type=code&state=sample_state"
    st.markdown(f'<a href="{login_target_url}" target="_self"><button style="width:100%;background-color:#16a34a;color:white;padding:10px;border:none;border-radius:5px;cursor:pointer;font-weight:bold;">Click to Login Automatically</button></a>', unsafe_allow_html=True)

live_tok = get_db_val("f_token")
if live_tok:
    st.sidebar.success("● Live Token Connected")

default_capital = float(get_db_val("tot_cap") or 10000.0)
if app_id_val and live_tok:
    headers_dict = {"Authorization": f"{app_id_val}:{live_tok}"}
    try:
        funds_resp = requests.get("https://api-t1.fyers.in/api/v3/funds", headers=headers_dict)
        funds_data = funds_resp.json()
        if funds_data.get("s") == "ok":
            for item in funds_data.get("fund_limit", []):
                if item.get("title") == "Client Balance" or "Total Balance" in str(item.get("title")):
                    live_bal = float(item.get("equityAmount", 0.0))
                    if live_bal > 0:
                        default_capital = live_bal
    except Exception:
        pass

    try:
        trades_resp = requests.get("https://api-t1.fyers.in/api/v3/tradebook", headers=headers_dict)
        trades_data = trades_resp.json()
        if trades_data.get("s") == "ok":
            conn_db = sqlite3.connect("journal.db")
            cur_db = conn_db.cursor()
            for t_item in trades_data.get("tradeBook", []):
                sym_name = t_item.get("symbol", "NIFTY")
                t_side = "BUY" if t_item.get("side") == 1 else "SELL"
                t_qty = int(t_item.get("tradedQty", 1))
                t_prc = float(t_item.get("tradePrice", 0.0))
                t_time = t_item.get("tradeTime", datetime.now().strftime("%Y-%m-%d"))
                
                cur_db.execute("INSERT INTO trades (trade_date, symbol, trade_type, quantity, entry_price, exit_price, pnl, execution_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                               (str(t_time)[:10], sym_name, t_side, t_qty, t_prc, t_prc, 0.0, "FYERS_API"))
            conn_db.commit()
            conn_db.close()
    except Exception:
        pass

st.sidebar.markdown("---")
st.sidebar.markdown("🛡️ Capital & Risk Management", unsafe_allow_html=True)
total_capital = st.sidebar.number_input("Total Capital (₹)", min_value=1000.0, value=default_capital, step=1000.0)
set_db_val("tot_cap", str(total_capital))

st.title("⚡ Spiritual Trader Pro | Terminal & Dashboard")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "📝 Trade Journal", "📈 Analytics", "🧘 Mindset & Journal", "⚙️ Settings"])

with tab1:
    st.subheader("Live Market & Performance Dashboard")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Capital", f"₹{total_capital:,.2f}")
    c2.metric("Max Daily Trades", FIXED_MAX_TRADES)
    c3.metric("Risk Limit", f"₹{FIXED_MAX_LOSS}")

with tab2:
    st.subheader("Advanced Trade Journal & Execution")
    with st.form("main_trade_form"):
        col1, col2 = st.columns(2)
        with col1:
            sym = st.text_input("Trading Symbol", value="NIFTY")
            t_type = st.selectbox("Action", ["BUY", "SELL"])
            qty = st.number_input("Quantity", min_value=1, value=15)
        with col2:
            e_pr = st.number_input("Entry Price", min_value=0.0, value=100.0)
            ex_pr = st.number_input("Exit Price", min_value=0.0, value=110.0)
            sl_pr = st.number_input("Stop Loss", min_value=0.0, value=90.0)
        
        if st.form_submit_button("Record Trade"):
            conn = sqlite3.connect("journal.db")
            cur = conn.cursor()
            pnl_val = (ex_pr - e_pr) * qty if t_type == "BUY" else (e_pr - ex_pr) * qty
            cur.execute("INSERT INTO trades (trade_date, symbol, trade_type, quantity, entry_price, exit_price, stop_loss, pnl) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (datetime.now().strftime("%Y-%m-%d"), sym, t_type, qty, e_pr, ex_pr, sl_pr, pnl_val))
            conn.commit()
            conn.close()
            st.success("Trade recorded successfully!")

with tab3:
    st.subheader("Comprehensive Analytics & Reports")
    conn = sqlite3.connect("journal.db")
    df_trades = pd.read_sql("SELECT * FROM trades", conn)
    conn.close()
    if not df_trades.empty:
        st.dataframe(df_trades, use_container_width=True)
        tot_pnl = df_trades["pnl"].sum()
        st.metric("Net P&L", f"₹{tot_pnl:,.2f}")
    else:
        st.info("No trades found in database.")

with tab4:
    st.subheader("Daily Mindset & Psychology Journal")
    dt_str = datetime.now().strftime("%Y-%m-%d")
    journal_text = st.text_area("Write your trading reflections, emotions, and lessons:")
    if st.button("Save Journal Entry"):
        conn = sqlite3.connect("journal.db")
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO daily_journal (trade_date, notes) VALUES (?, ?)", (dt_str, journal_text))
        conn.commit()
        conn.close()
        st.success("Journal notes saved!")

with tab5:
    st.subheader("System Configurations & Database Controls")
    st.write("Manage your local SQLite database and application settings here.")

