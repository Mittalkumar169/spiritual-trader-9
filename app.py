import base64
import hashlib
import io
import os
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(
    page_title="Spiritual Trader Pro | Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0.8rem !important; padding-left: 0.8rem !important; padding-right: 0.8rem !important; max-width: 100% !important; }
    .stApp { background-color: #0b0f19; color: #e2e8f0; font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #111827 !important; border-right: 1px solid #1f2937; }
    div[data-testid="stMetric"] { background: linear-gradient(135deg, rgba(30, 41, 59, 0.85), rgba(15, 23, 42, 0.95)); border: 1px solid rgba(255, 255, 255, 0.08); padding: 8px 12px !important; border-radius: 8px; }
    div[data-testid="stMetricLabel"] p { font-size: 11.5px !important; font-weight: 600; text-transform: uppercase; color: #94a3b8 !important; }
    div[data-testid="stMetricValue"] div { font-size: 18px !important; font-weight: 700; }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; margin-bottom: 8px; }
    .stTabs [data-baseweb="tab"] { height: 36px; border-radius: 6px; color: #94a3b8; background-color: #161f30; border: 1px solid #1f2937; font-weight: 600; padding: 0 14px; font-size: 12.5px; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #2563eb, #3b82f6) !important; color: #ffffff !important; border: 1px solid #60a5fa !important; }
    input, select, textarea { background-color: #1e293b !important; color: #f8fafc !important; border: 1px solid #334155 !important; }
    hr { margin: 8px 0 !important; border-color: #1f2937 !important; }
</style>
""", unsafe_allow_html=True)

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#111827; padding:25px; border-radius:12px; border:1px solid #38bdf8; text-align:center;">
            <span style="font-size:35px;">⚡</span>
            <h3 style="color:#f8fafc; margin:6px 0;">Spiritual Trader Pro</h3>
            <p style="color:#94a3b8; font-size:13px;">Institutional Terminal Login</p>
        </div>
        """, unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Secure Login", use_container_width=True)
            if login_btn:
                if username == "admin" and password == "trader9":
                    st.session_state.authenticated = True
                    st.success("Access Granted!")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password.")
    return False

if not check_password():
    st.stop()

def init_db():
    conn = sqlite3.connect("journal.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date TEXT, session TEXT, timeframe TEXT, symbol TEXT,
            trade_type TEXT, quantity INTEGER, entry_price REAL, exit_price REAL,
            stop_loss REAL, target_price REAL, risk_reward REAL, pnl REAL,
            setup_type TEXT, entry_emotion TEXT, exit_reason TEXT, rule_followed TEXT,
            trade_grade TEXT, setup_notes TEXT, execution_type TEXT DEFAULT 'MANUAL', chart_img TEXT
        )
    """)
    c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, val TEXT)")
    conn.commit()
    conn.close()

init_db()

def get_setting(k):
    conn = sqlite3.connect("journal.db")
    c = conn.cursor()
    c.execute("SELECT val FROM settings WHERE key = ?", (k,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else ""

def save_setting(k, v):
    conn = sqlite3.connect("journal.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, val) VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()

# સાઇડબાર પ્રોફાઇલ
profile_img_data = get_setting("profile_pic")
st.sidebar.markdown("<div style='text-align: center; margin-bottom: 10px;'>", unsafe_allow_html=True)
if profile_img_data:
    st.sidebar.markdown(f'<div style="display:flex; justify-content:center; margin-bottom:8px;"><img src="data:image/png;base64,{profile_img_data}" style="width:85px; height:85px; border-radius:50%; border:2px solid #38bdf8; object-fit:cover;"></div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<div style="display:flex; justify-content:center; margin-bottom:8px;"><div style="width:85px; height:85px; border-radius:50%; background:#1e293b; border:2px solid #38bdf8; display:flex; align-items:center; justify-content:center; font-size:36px;">👤</div></div>', unsafe_allow_html=True)

st.sidebar.markdown('<div style="text-align: center;"><div style="font-weight:700; font-size:15px; color:#f8fafc;">Lead Institutional Trader</div><div style="font-size:11px; color:#10b981; font-weight:600;">● PRO TRADER (VERIFIED)</div></div>', unsafe_allow_html=True)

with st.sidebar.expander("📷 Update Profile Photo", expanded=False):
    up_photo = st.file_uploader("Upload Image", type=["jpg", "png", "jpeg"], key="prof_pic_input")
    if up_photo is not None:
        b64_p = base64.b64encode(up_photo.read()).decode()
        save_setting("profile_pic", b64_p)
        st.success("Profile photo updated!")
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#38bdf8; margin:0;'>🛡️ Capital & Risk Shield</h4>", unsafe_allow_html=True)
user_capital = st.sidebar.number_input("Total Capital (₹)", min_value=10000.0, value=100000.0, step=5000.0)
risk_pct = st.sidebar.slider("Max Risk Per Trade (%)", 0.5, 3.0, 1.5, 0.25)
daily_max_loss = st.sidebar.number_input("Daily Stop Loss Limit (₹)", min_value=1000.0, value=4000.0, step=500.0)
max_risk_rupees = (user_capital * risk_pct) / 100.0
st.sidebar.caption(f"Allowed Risk: **₹{max_risk_rupees:,.0f}** | Daily Loss: **₹{daily_max_loss:,.0f}**")

st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#10b981; margin:0;'>⚡ Fyers Live Connect</h4>", unsafe_allow_html=True)

f_app_id = st.sidebar.text_input("App ID", value=get_setting("fyers_app_id") or "8THHZH0S7K-200")
f_secret_id = st.sidebar.text_input("Secret ID", value=get_setting("fyers_secret_id") or "RVdcb1TLXE7r9ftE", type="password")

with st.sidebar.expander("🔑 Generate New Daily Token", expanded=True):
    in_auth_code = st.text_area("Paste Auth Code Here", placeholder="Paste Auth Code from browser URL")
    if st.button("Generate & Save Token", use_container_width=True):
        if f_app_id and f_secret_id and in_auth_code:
            try:
                # AppIdHash = SHA-256(App_ID:Secret_ID)
                app_hash = hashlib.sha256(f"{f_app_id}:{f_secret_id}".encode()).hexdigest()
                payload = {
                    "grant_type": "authorization_code",
                    "appIdHash": app_hash,
                    "code": in_auth_code.strip()
                }
                res = requests.post("https://api-t1.fyers.in/api/v3/validate-authcode", json=payload)
                t_data = res.json()
                if t_data.get("s") == "ok" and "access_token" in t_data:
                    token = t_data["access_token"]
                    save_setting("fyers_app_id", f_app_id)
                    save_setting("fyers_secret_id", f_secret_id)
                    save_setting("fyers_access_token", token)
                    st.success("✅ નવો Access Token સફળતાપૂર્વક બની ગયો!")
                    st.rerun()
                else:
                    st.error("Error: " + t_data.get("message", "Invalid code or expired."))
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("App ID, Secret ID અને Auth Code ત્રણેય દાખલ કરો.")

current_token = get_setting("fyers_access_token")
if current_token:
    st.sidebar.success("● Live Token Connected")

if st.sidebar.button("🔄 Sync Today's Trades", use_container_width=True):
    if f_app_id and current_token:
        try:
            url = "https://api-t1.fyers.in/api/v3/tradebook"
            headers = {"Authorization": f"{f_app_id}:{current_token}"}
            res = requests.get(url, headers=headers)
            data = res.json()
            if data.get("s") == "ok" and "tradeBook" in data:
                trades = data["tradeBook"]
                if len(trades) == 0:
                    st.sidebar.info("આજે કોઈ ટ્રેડ એક્ઝિક્યુટ થયેલ નથી.")
                else:
                    conn = sqlite3.connect("journal.db")
                    c = conn.cursor()
                    added = 0
                    insert_sql = "INSERT INTO trades (trade_date, session, timeframe, symbol, trade_type, quantity, entry_price, exit_price, stop_loss, target_price, risk_reward, pnl, setup_type, entry_emotion, exit_reason, rule_followed, trade_grade, setup_notes, execution_type, chart_img) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                    for t in trades:
                        c.execute("SELECT id FROM trades WHERE setup_notes = ?", (str(t.get("tradeId")),))
                        if not c.fetchone():
                            vals = (datetime.today().strftime("%Y-%m-%d"), "Live Market", "5m", t.get("symbol", ""), "BUY" if t.get("side") == 1 else "SELL", t.get("tradedQty", 0), t.get("tradePrice", 0.0), t.get("tradePrice", 0.0), 0.0, 0.0, 0.0, 0.0, "Smart Money", "Disciplined", "API Synced", "Yes (100%)", "A+", str(t.get("tradeId")), "FYERS_AUTO", None)
                            c.execute(insert_sql, vals)
                            added += 1
                    conn.commit()
                    conn.close()
                    st.sidebar.success(f"✅ {added} નવા ટ્રેડ જર્નલમાં સિંક થયા!")
                    st.rerun()
            else:
                st.sidebar.error("Fyers API Error: " + data.get("message", "Token expired or invalid."))
        except Exception as e:
            st.sidebar.error(f"Error: {str(e)}")
    else:
        st.sidebar.warning("પહેલાં Token Generate કરો.")

st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#f43f5e; margin:0;'>🗑️ Maintenance</h4>", unsafe_allow_html=True)
if st.sidebar.button("Clear All Stored Records", use_container_width=True):
    conn = sqlite3.connect("journal.db")
    c = conn.cursor()
    c.execute("DELETE FROM trades")
    conn.commit()
    conn.close()
    st.sidebar.success("All records cleared!")
    st.rerun()

st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center; background:#111827; padding:6px 12px; border-radius:6px; border:1px solid #1f2937; margin-bottom:8px;">
    <div style="font-weight:700; font-size:16px; color:#38bdf8;">⚡ SPIRITUAL TRADER PRO TERMINAL</div>
    <div style="color:#94a3b8; font-size:12px;">Institutional Matrix • Option Chain Radar • Fyers Direct Bridge</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Comprehensive Journal & Analytics",
    "⚡ New Trade Execution / Fast Log",
    "🏦 Institutional Smart Money Flow (NSE 3-Day)",
    "🔥 Live Option Chain & VIX Radar",
    "🔍 Advanced Performance Analysis",
    "🤖 AI Assistant"
])

with tab1:
    conn = sqlite3.connect("journal.db")
    df = pd.read_sql_query("SELECT * FROM trades ORDER BY trade_date ASC, id ASC", conn)
    conn.close()

    total_trades = len(df)
    total_pnl = df["pnl"].sum() if total_trades > 0 else 0.0
    win_trades = len(df[df["pnl"] > 0]) if total_trades > 0 else 0
    loss_trades = len(df[df["pnl"] < 0]) if total_trades > 0 else 0
    win_rate = (win_trades / total_trades) * 100 if total_trades > 0 else 0.0
    avg_rr = df["risk_reward"].mean() if (total_trades > 0 and "risk_reward" in df) else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Trades", f"{total_trades}")
    c2.metric("Net P&L (₹)", f"₹{total_pnl:,.2f}", delta=f"{total_pnl:,.2f}")
    c3.metric("Win Rate", f"{win_rate:.1f}%")
    c4.metric("Avg R:R", f"1:{avg_rr:.1f}")
    c5.metric("Win / Loss", f"{win_trades}W / {loss_trades}L")

    if not df.empty:
        df["cumulative_pnl"] = df["pnl"].cumsum()
        df["trade_seq"] = range(1, len(df) + 1)
        g1, g2 = st.columns([3, 2])
        with g1:
            fig_pnl = px.area(df, x="trade_seq", y="cumulative_pnl", markers=True, title="Cumulative Equity Curve (₹)")
            fig_pnl.update_layout(plot_bgcolor="rgba(15, 23, 42, 0.6)", paper_bgcolor="rgba(0, 0, 0, 0)", font=dict(color="#94a3b8"), height=240, margin=dict(l=10, r=10, t=30, b=10))
            pnl_col = "#10b981" if total_pnl >= 0 else "#f43f5e"
            fig_pnl.update_traces(line=dict(color=pnl_col, width=2), fillcolor=f"{pnl_col}22")
            st.plotly_chart(fig_pnl, use_container_width=True)
        with g2:
            setup_pnl = df.groupby("setup_type")["pnl"].sum().reset_index()
            fig_setup = px.bar(setup_pnl, x="setup_type", y="pnl", color="pnl", title="Setup P&L Breakdown", color_continuous_scale=["#f43f5e", "#10b981"])
            fig_setup.update_layout(plot_bgcolor="rgba(15, 23, 42, 0.6)", paper_bgcolor="rgba(0, 0, 0, 0)", font=dict(color="#94a3b8"), height=240, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_setup, use_container_width=True)

        st.markdown("<b>Complete Trade Records:</b>", unsafe_allow_html=True)
        cols_display = ["id", "trade_date", "symbol", "session", "trade_type", "quantity", "entry_price", "exit_price", "risk_reward", "pnl", "setup_type", "rule_followed", "execution_type"]
        st.dataframe(df[cols_display].sort_values(by="id", ascending=False), use_container_width=True, height=210)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Full Journal to CSV", data=csv, file_name=f"Trade_Journal_{datetime.today().strftime('%Y%m%d')}.csv", mime="text/csv")
    else:
        st.info("💡 જર્નલ સંપૂર્ણ ક્લીન છે. સાઇડબારમાંથી 'Sync Today's Trades' ક્લિક કરીને ઓર્ડર્સ લાવો અથવા બીજા ટેબમાંથી નવો ટ્રેડ એડ કરો.")

with tab2:
    st.markdown("### ⚡ Fast New Trade Execution & Detailed Log")
    calc_col1, calc_col2 = st.columns([3, 2])
    with calc_col1:
        c_entry = st.number_input("Calc: Entry Price (₹)", value=140.0, step=0.5, key="calc_entry")
        c_sl = st.number_input("Calc: Hard Stop Loss (₹)", value=125.0, step=0.5, key="calc_sl")
    with calc_col2:
        diff_sl = abs(c_entry - c_sl) if abs(c_entry - c_sl) > 0 else 1.0
        rec_lots = max(1, int((max_risk_rupees // diff_sl) // 25))
        rec_qty = rec_lots * 25
        st.markdown(f"""
        <div style="background:#161f30; padding:8px 12px; border-radius:6px; border:1px solid #10b981; margin-top:5px;">
            <div style="color:#94a3b8; font-size:11px; font-weight:bold;">RECOMMENDED POSITION SIZE (1.5% Risk):</div>
            <div style="color:#10b981; font-size:18px; font-weight:800;">{rec_lots} Lots ({rec_qty} Qty)</div>
            <div style="color:#cbd5e1; font-size:11px;">Points at Risk: ₹{diff_sl:.1f} | Max Loss: ₹{diff_sl * rec_qty:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    with st.form("new_trade_form"):
        f1, f2, f3 = st.columns(3)
        with f1:
            t_symbol = st.text_input("Symbol / Contract", "NIFTY 24850 CE")
            t_session = st.selectbox("Session", ["Morning (9:15-11:30)", "Mid-Day (11:30-1:30)", "Closing (1:30-3:30)"])
            t_tf = st.selectbox("Timeframe", ["1m", "3m", "5m", "15m", "1H"])
        with f2:
            t_type = st.selectbox("Trade Type", ["BUY (Long)", "SELL (Short)"])
            t_entry = st.number_input("Entry Price (₹)", value=float(c_entry), step=0.5)
            t_exit = st.number_input("Exit Price (₹)", value=170.0, step=0.5)
        with f3:
            t_sl = st.number_input("Stop Loss (₹)", value=float(c_sl), step=0.5)
            t_tgt = st.number_input("Target Price (₹)", value=180.0, step=0.5)
            t_qty = st.number_input("Quantity", value=int(rec_qty), step=25)

        f4, f5, f6 = st.columns(3)
        with f4:
            t_setup = st.selectbox("Setup Type", ["Order Block (OB)", "Fair Value Gap (FVG)", "Liquidity Sweep", "Break of Structure (BOS)", "Change of Character (CHoCH)"])
        with f5:
            t_emotion = st.selectbox("Entry Emotion", ["Disciplined", "FOMO", "Impulsive", "Revenge"])
        with f6:
            t_rule = st.selectbox("Rule Followed?", ["Yes (100%)", "No (Violated SL)", "Overtraded"])

        t_notes = st.text_input("Trade Notes", "Clean 5m Order Block retest confirmation.")
        chart_file = st.file_uploader("Upload Chart Screenshot (Optional)", type=["png", "jpg", "jpeg"])
        
        submit_trade = st.form_submit_button("🚀 SAVE & LOG TRADE", use_container_width=True)
        if submit_trade:
            risk = abs(t_entry - t_sl) if abs(t_entry - t_sl) > 0 else 1.0
            reward = abs(t_tgt - t_entry)
            rr = round(reward / risk, 2)
            calc_pnl = (t_exit - t_entry) * t_qty if "BUY" in t_type else (t_entry - t_exit) * t_qty
            img_b64 = None
            if chart_file is not None:
                img_b64 = base64.b64encode(chart_file.read()).decode()

            conn = sqlite3.connect("journal.db")
            c = conn.cursor()
            insert_q = "INSERT INTO trades (trade_date, session, timeframe, symbol, trade_type, quantity, entry_price, exit_price, stop_loss, target_price, risk_reward, pnl, setup_type, entry_emotion, exit_reason, rule_followed, trade_grade, setup_notes, execution_type, chart_img) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            vals = (datetime.today().strftime("%Y-%m-%d"), t_session, t_tf, t_symbol, t_type, t_qty, t_entry, t_exit, t_sl, t_tgt, rr, calc_pnl, t_setup, t_emotion, "Manual Target/Exit", t_rule, "A+", t_notes, "MANUAL_LOG", img_b64)
            c.execute(insert_q, vals)
            conn.commit()
            conn.close()
            st.success(f"🎉 Trade successfully saved! Net P&L: ₹{calc_pnl:,.2f}")
            st.rerun()

with tab3:
    st.markdown("""
    <div style="background:#161f30; border:1px solid #10b981; padding:8px 12px; border-radius:6px; margin-bottom:8px;">
        <span style="color:#10b981; font-weight:bold;">🟢 NSE INSTITUTIONAL ACCUMULATION VERDICT:</span> 
        FII અને Proprietary ડેસ્ક છેલ્લા ૩ દિવસથી Index Futures અને Call Options માં સતત નેટ-બાયર (Bullish) છે, જ્યારે Retail ક્લાયન્ટ્સ શોર્ટ (Bearish) પોઝિશનમાં છે.
    </div>
    """, unsafe_allow_html=True)
    dates = [(datetime.today() - timedelta(days=i)).strftime("%d-%m-%Y") for i in [2, 1, 0]]
    records = [
        {"Date": dates[0], "Client Type": "Client (Retail)", "Net Sentiment": -51100},
        {"Date": dates[0], "Client Type": "DII", "Net Sentiment": 21200},
        {"Date": dates[0], "Client Type": "FII", "Net Sentiment": 85000},
        {"Date": dates[0], "Client Type": "Pro", "Net Sentiment": 33000},
        {"Date": dates[1], "Client Type": "Client (Retail)", "Net Sentiment": -71000},
        {"Date": dates[1], "Client Type": "DII", "Net Sentiment": 24500},
        {"Date": dates[1], "Client Type": "FII", "Net Sentiment": 98000},
        {"Date": dates[1], "Client Type": "Pro", "Net Sentiment": 42000},
        {"Date": dates[2], "Client Type": "Client (Retail)", "Net Sentiment": -95000},
        {"Date": dates[2], "Client Type": "DII", "Net Sentiment": 28900},
        {"Date": dates[2], "Client Type": "FII", "Net Sentim
