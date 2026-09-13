
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
from fyers_apiv3 import fyersModel

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
st.sidebar.markdown("⚡ Fyers Auto Live Connect", unsafe_allow_html=True)
app_id_val = st.sidebar.text_input("App ID", value=get_db_val("f_app_id") or "8THHZH0S7K-200")
sec_id_val = st.sidebar.text_input("Secret ID", value=get_db_val("f_sec_id") or "RVdcb1TLXE7r9ftE", type="password")
fyers_pin = st.sidebar.text_input("PIN / DOB (DDMMYYYY)", value=get_db_val("f_pin") or "", type="password")
fyers_totp_key = st.sidebar.text_input("TOTP Secret Key", value=get_db_val("f_totp_key") or "SLYEDG46FG4QNWGC5K3DHXEDE3PYVODJ", type="password")

with st.sidebar.expander("🔑 Auto Generate Token", expanded=True):
    if st.button("Generate Token Automatically", use_container_width=True):
        if app_id_val and sec_id_val and fyers_pin and fyers_totp_key:
            try:
                totp_gen = pyotp.TOTP(fyers_totp_key.strip().replace(" ", ""))
                current_totp = totp_gen.now()
                set_db_val("f_app_id", app_id_val)
                set_db_val("f_sec_id", sec_id_val)
                set_db_val("f_pin", fyers_pin)
                set_db_val("f_totp_key", fyers_totp_key)
                st.success(f"TOTP Configured! Current OTP: {current_totp}")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Please fill all credentials!")

live_tok = get_db_val("f_token")
if live_tok:
    st.sidebar.success("● Live Token Connected")

st.sidebar.markdown("---")
st.sidebar.markdown("🛡️ Capital & Risk Management", unsafe_allow_html=True)
total_capital = st.sidebar.number_input("Total Capital (₹)", min_value=1000.0, value=float(get_db_val("tot_cap") or 10000.0), step=1000.0)
set_db_val("tot_cap", str(total_capital))

st.title("⚡ Spiritual Trader Pro | Terminal & Dashboard")

# Complete feature tabs restored
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

