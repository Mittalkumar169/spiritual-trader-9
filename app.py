
import io
import os
import sqlite3
from datetime import datetime, timedelta
from PIL import Image
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ==============================================================================
# 🚀 SPIRITUAL TRADER PRO - COMPACT TERMINAL
# ==============================================================================

st.set_page_config(
    page_title="Spiritual Trader Pro | Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

IMAGE_DIR = "screenshots"
os.makedirs(IMAGE_DIR, exist_ok=True)

# ------------------------------------------------------------------------------
# 🎨 OBSIDIAN SLATE & ULTRA-COMPACT CSS (ZERO EMPTY SPACE)
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 0.8rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    .stApp { background-color: #0b0f19; color: #e2e8f0; font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { 
        background-color: #111827 !important; 
        border-right: 1px solid #1f2937;
        padding-top: 0.8rem !important;
    }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 8px 12px !important;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    }
    div[data-testid="stMetricLabel"] p { font-size: 11px !important; font-weight: 600; text-transform: uppercase; color: #94a3b8 !important; margin: 0; }
    div[data-testid="stMetricValue"] div { font-size: 19px !important; font-weight: 700; }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; margin-bottom: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 36px; border-radius: 6px; color: #94a3b8; background-color: #161f30;
        border: 1px solid #1f2937; font-weight: 600; padding: 0 12px; font-size: 12.5px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
        color: #ffffff !important; border: 1px solid #60a5fa !important;
    }
    input, select, textarea { background-color: #1e293b !important; color: #f8fafc !important; border: 1px solid #334155 !important; }
    hr { margin: 8px 0 !important; border-color: #1f2937 !important; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 🔐 AUTHENTICATION & LOGIN SHIELD
# ------------------------------------------------------------------------------
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#111827; padding:24px; border-radius:12px; border:1px solid #38bdf8; text-align:center;">
            <span style="font-size:32px;">⚡</span>
            <h3 style="color:#f8fafc; margin:6px 0;">Spiritual Trader Pro</h3>
            <p style="color:#94a3b8; font-size:12px;">Institutional Terminal Login</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Secure Login", use_container_width=True)

            if login_btn:
                if username == "admin" and password == "trader9":
                    st.session_state.authenticated = True
                    st.success("Access Granted! Loading terminal...")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password.")
        st.caption("Default Access: User: `admin` | Pass: `trader9`")
    return False

if not check_password():
    st.stop()

# ------------------------------------------------------------------------------
# 🗄️ SQLITE DATABASE ENGINE (PRE-POPULATED IF EMPTY)
# ------------------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect("journal.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date TEXT,
            session TEXT,
            timeframe TEXT,
            symbol TEXT,
            trade_type TEXT,
            quantity INTEGER,
            entry_price REAL,
            exit_price REAL,
            stop_loss REAL,
            target_price REAL,
            risk_reward REAL,
            pnl REAL,
            setup_type TEXT,
            entry_emotion TEXT,
            exit_reason TEXT,
            rule_followed TEXT,
            trade_grade TEXT,
            setup_notes TEXT,
            image_name TEXT,
            execution_type TEXT DEFAULT 'MANUAL'
        )
    """)
    conn.commit()

    c.execute("SELECT COUNT(*) FROM trades")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO trades (trade_date, session, timeframe, symbol, trade_type, quantity, entry_price, exit_price, stop_loss, target_price, risk_reward, pnl, setup_type, entry_emotion, exit_reason, rule_followed, trade_grade, setup_notes, image_name, execution_type)
            VALUES 
            (date('now', '-1 day'), 'Morning (9:15-11:30)', '5m', 'NIFTY 24800 CE', 'BUY (Long)', 50, 120.0, 165.0, 105.0, 160.0, 3.0, 2250.0, 'Order Block (OB)', 'Calm & Disciplined', 'Target Hit', 'Yes (100%)', 'A+', 'Clean 15m OB tap and bullish engulfing', '', 'MANUAL'),
            (date('now'), 'Mid-Day (11:30-1:30)', '5m', 'BANKNIFTY 52000 PE', 'BUY (Long)', 30, 240.0, 210.0, 210.0, 300.0, 2.0, -900.0, 'Fair Value Gap (FVG)', 'FOMO', 'SL Hit', 'Partial', 'B', 'Choppy range entry near noon', '', 'MANUAL')
        """)
        conn.commit()
    conn.close()

init_db()

def log_trade_to_db(trade_date, session_val, timeframe_val, symbol_val, trade_type_val,
                     quantity_val, entry_val, exit_val, sl_val, target_val, rr_val,
                     pnl_val, setup_val, emotion_val, exit_reason_val, rule_val,
                     grade_val, notes_val, img_name_val="", exec_type="MANUAL"):
    conn = sqlite3.connect("journal.db")
    c = conn.cursor()
    c.execute("""
        INSERT INTO trades (trade_date, session, timeframe, symbol, trade_type, quantity,
                            entry_price, exit_price, stop_loss, target_price, risk_reward,
                            pnl, setup_type, entry_emotion, exit_reason, rule_followed,
                            trade_grade, setup_notes, image_name, execution_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (str(trade_date), session_val, timeframe_val, symbol_val, trade_type_val,
          quantity_val, entry_val, exit_val, sl_val, target_val, rr_val,
          pnl_val, setup_val, emotion_val, exit_reason_val, rule_val,
          grade_val, notes_val, img_name_val, exec_type))
    conn.commit()
    conn.close()

# ------------------------------------------------------------------------------
# 🏦 1. INSTITUTIONAL DATA LOADER
# ------------------------------------------------------------------------------
def get_participant_data():
    today = datetime.today()
    dates = [(today - timedelta(days=i)).strftime("%d-%m-%Y") for i in [2, 1, 0]]
    records = [
        {"Date": dates[0], "Client Type": "Client", "Net Future": -24100, "Net Calls": -12000, "Net Puts": 15000, "Net Sentiment Score": -51100},
        {"Date": dates[0], "Client Type": "DII", "Net Future": 14200, "Net Calls": 5000, "Net Puts": -2000, "Net Sentiment Score": 21200},
        {"Date": dates[0], "Client Type": "FII", "Net Future": 42000, "Net Calls": 31000, "Net Puts": -12000, "Net Sentiment Score": 85000},
        {"Date": dates[0], "Client Type": "Pro", "Net Future": 12000, "Net Calls": 15000, "Net Puts": -6000, "Net Sentiment Score": 33000},
        {"Date": dates[1], "Client Type": "Client", "Net Future": -31000, "Net Calls": -18000, "Net Puts": 22000, "Net Sentiment Score": -71000},
        {"Date": dates[1], "Client Type": "DII", "Net Future": 16500, "Net Calls": 6200, "Net Puts": -1800, "Net Sentiment Score": 24500},
        {"Date": dates[1], "Client Type": "FII", "Net Future": 48000, "Net Calls": 36000, "Net Puts": -14000, "Net Sentiment Score": 98000},
        {"Date": dates[1], "Client Type": "Pro", "Net Future": 15500, "Net Calls": 18500, "Net Puts": -8000, "Net Sentiment Score": 42000},
        {"Date": dates[2], "Client Type": "Client", "Net Future": -42000, "Net Calls": -24000, "Net Puts": 29000, "Net Sentiment Score": -95000},
        {"Date": dates[2], "Client Type": "DII", "Net Future": 19000, "Net Calls": 7800, "Net Puts": -2100, "Net Sentiment Score": 28900},
        {"Date": dates[2], "Client Type": "FII", "Net Future": 56000, "Net Calls": 44000, "Net Puts": -18000, "Net Sentiment Score": 118000},
        {"Date": dates[2], "Client Type": "Pro", "Net Future": 18200, "Net Calls": 22400, "Net Puts": -9500, "Net Sentiment Score": 50100},
    ]
    return pd.DataFrame(records)

# ------------------------------------------------------------------------------
# 📈 2. OPTION CHAIN & VIX RADAR
# ------------------------------------------------------------------------------
def get_active_option_chain(symbol="NIFTY"):
    spot = 24850.0 if symbol == "NIFTY" else 52400.0
    strikes = [spot + (i * 100) for i in range(-7, 8)]
    rows = []
    vix = 13.85
    for s in strikes:
        diff = s - spot
        ce_oi = max(1200, int((600 - diff) * 180))
        pe_oi = max(1100, int((600 + diff) * 210))
        ce_chg = int(-diff * 5)
        pe_chg = int(diff * 6)
        ce_ltp = max(5.0, round(280.0 - (diff * 0.55), 1))
        pe_ltp = max(5.0, round(260.0 + (diff * 0.52), 1))
        
        ce_edge = "⭐ ATM BUY" if abs(diff) <= 50 else ("🟢 High Delta ITM" if diff < -50 else "🔴 Avoid OTM Decay")
        pe_edge = "⭐ ATM BUY" if abs(diff) <= 50 else ("🟢 High Delta ITM" if diff > 50 else "🔴 Avoid OTM Decay")
        
        rows.append({
            "CE Edge": ce_edge,
            "CE LTP": ce_ltp,
            "CE Chg OI": ce_chg,
            "CE OI": ce_oi,
            "Strike": int(s),
            "PE OI": pe_oi,
            "PE Chg OI": pe_chg,
            "PE LTP": pe_ltp,
            "PE Edge": pe_edge
        })
    return pd.DataFrame(rows), spot, vix

# ------------------------------------------------------------------------------
# 🛡️ SIDEBAR: RISK SHIELD & ORDER ENTRY
# ------------------------------------------------------------------------------
st.sidebar.markdown("<h3 style='color:#38bdf8; margin:0;'>🛡️ Risk Shield Panel</h3>", unsafe_allow_html=True)
user_capital = st.sidebar.number_input("Total Capital (₹)", min_value=10000.0, value=100000.0, step=5000.0)
risk_pct = st.sidebar.slider("Risk Per Trade (%)", 0.5, 3.0, 1.5, 0.25)
daily_max_loss = st.sidebar.number_input("Max Daily Loss Limit (₹)", min_value=1000.0, value=4000.0, step=500.0)

max_risk_rupees = (user_capital * risk_pct) / 100.0

conn = sqlite3.connect("journal.db")
today_str = datetime.today().strftime("%Y-%m-%d")
c_cur = conn.cursor()
c_cur.execute("SELECT SUM(pnl) FROM trades WHERE trade_date = ?", (today_str,))
res_pnl = c_cur.fetchone()[0]
today_pnl = res_pnl if res_pnl is not None else 0.0
conn.close()

is_daily_loss_hit = today_pnl <= -abs(daily_max_loss)
if is_daily_loss_hit:
    st.sidebar.error(f"🛑 **Daily Loss Limit Hit!**\nToday's P&L: ₹{today_pnl:,.2f} | Max: -₹{daily_max_loss:,.2f}\nTrading blocked to prevent overtrading.")

st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#38bdf8; margin:0;'>➕ New Trade Record</h4>", unsafe_allow_html=True)

with st.sidebar.form("trade_form", clear_on_submit=True):
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        trade_date = st.date_input("Date", datetime.today())
        timeframe = st.selectbox("Timeframe", ["1m", "3m", "5m", "15m", "1H"])
    with col_f2:
        session = st.selectbox("Session", ["Morning (9:15-11:30)", "Mid-Day (11:30-1:30)", "Afternoon (1:30-3:30)"])
        symbol = st.text_input("Symbol", value="NIFTY 24850 CE").upper().strip()

    trade_type = st.selectbox("Trade Type", ["BUY (Long)", "SELL (Short)"])

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        entry_price = st.number_input("Entry Price (₹)", min_value=0.0, value=140.0, format="%.2f")
        stop_loss = st.number_input("Stop Loss (₹)", min_value=0.0, value=125.0, format="%.2f")
    with col_p2:
        exit_price = st.number_input("Exit Price (₹)", min_value=0.0, value=175.0, format="%.2f")
        target_price = st.number_input("Target Price (₹)", min_value=0.0, value=180.0, format="%.2f")

    sl_pts = abs(entry_price - stop_loss) if (entry_price > 0 and stop_loss > 0) else 1.0
    rec_lots = max(1, int((max_risk_rupees // sl_pts) // 25))
    rec_qty = rec_lots * 25

    st.markdown(f"""
    <div style="background:#161f30; padding:8px 12px; border-radius:6px; border:1px solid #334155; margin-bottom:8px;">
        <div style="color:#94a3b8; font-size:10.5px; font-weight:bold;">🛡️ AUTO RISK SIZING (Cap: ₹{max_risk_rupees:,.0f})</div>
        <div style="color:#10b981; font-size:14px; font-weight:bold;">👉 {rec_lots} Lots ({rec_qty} Qty)</div>
        <div style="color:#cbd5e1; font-size:10px;">SL: {sl_pts:.1f} pts | Risk if SL hits: -₹{sl_pts * rec_qty:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

    quantity = st.number_input("Lots / Quantity", min_value=1, value=int(rec_qty), step=25)
    setup_type = st.selectbox("Setup Logic", [
        "Order Block (OB)", "Fair Value Gap (FVG)", "Liquidity Sweep",
        "Support / Resistance Rejection", "Trendline Breakout / Retest", "Other"
    ])

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        entry_emotion = st.selectbox("Entry Mindset", ["Calm & Disciplined", "FOMO", "Revenge Entry", "Boredom Entry"])
        rule_followed = st.selectbox("Rules Followed?", ["Yes (100%)", "Partial", "No (Violated)"])
    with col_s2:
        exit_reason = st.selectbox("Exit Reason", ["Target Hit", "SL Hit", "Trailing SL", "Early Panic Exit"])
        trade_grade = st.selectbox("Trade Grade", ["A+", "A", "B", "C (Poor Execution)"])

    setup_notes = st.text_area("Trading Notes & Lessons", height=60)
    uploaded_image = st.file_uploader("Chart Screenshot", type=["png", "jpg", "jpeg"])

    submitted = st.form_submit_button("💾 Save Trade Record", disabled=is_daily_loss_hit)

if submitted:
    if symbol and entry_price > 0 and exit_price > 0 and stop_loss > 0:
        is_buy = "BUY" in trade_type
        pnl = (exit_price - entry_price) * quantity if is_buy else (entry_price - exit_price) * quantity
        risk_unit = abs(entry_price - stop_loss) if abs(entry_price - stop_loss) > 0 else 1.0
        reward_unit = abs(target_price - entry_price) if target_price > 0 else abs(exit_price - entry_price)
        rr_ratio = round(reward_unit / risk_unit, 2)

        img_name = ""
        if uploaded_image:
            img_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_image.name}"
            with open(os.path.join(IMAGE_DIR, img_name), "wb") as f:
                f.write(uploaded_image.getbuffer())

        log_trade_to_db(trade_date, session, timeframe, symbol, trade_type, quantity,
                        entry_price, exit_price, stop_loss, target_price, rr_ratio,
                        pnl, setup_type, entry_emotion, exit_reason, rule_followed,
                        trade_grade, setup_notes, img_name, "MANUAL")
        st.sidebar.success("✅ Trade logged successfully!")
        st.rerun()

# ------------------------------------------------------------------------------
# 💻 TOP COMPACT HEADER
# ------------------------------------------------------------------------------
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center; background:#111827; padding:8px 14px; border-radius:8px; border:1px solid #1f2937; margin-bottom:10px;">
    <div style="font-weight:700; font-size:17px; color:#38bdf8;">⚡ SPIRITUAL TRADER TERMINAL PRO</div>
    <div style="color:#94a3b8; font-size:12px;">Live Institutional Flow • Auto Risk Shield • Real-Time Matrix</div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 📑 NAVIGATION TABS
# ------------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Comprehensive Journal",
    "🏦 Institutional Smart Money Flow",
    "🔥 Live Option Chain & VIX Radar",
    "⚡ 1-Click Broker Auto-Execution",
    "🤖 AI Assistant"
])

# ==============================================================================
# 📊 TAB 1: COMPREHENSIVE JOURNAL
# ==============================================================================
with tab1:
    conn = sqlite3.connect("journal.db")
    df = pd.read_sql_query("SELECT * FROM trades ORDER BY trade_date ASC, id ASC", conn)
    conn.close()

    if not df.empty:
        df["trade_date"] = pd.to_datetime(df["trade_date"])

        total_trades = len(df)
        total_pnl = df["pnl"].sum()
        win_trades = len(df[df["pnl"] > 0])
        win_rate = (win_trades / total_trades) * 100 if total_trades > 0 else 0
        avg_rr = df["risk_reward"].mean() if "risk_reward" in df else 0.0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Trades", f"{total_trades}")
        c2.metric("Net P&L (₹)", f"₹{total_pnl:,.2f}", delta=f"{total_pnl:,.2f}")
        c3.metric("Win Rate", f"{win_rate:.1f}%")
        c4.metric("Avg R:R", f"1:{avg_rr:.1f}")
        c5.metric("Profitable Trades", f"{win_trades} / {total_trades}")

        # Session Analysis
        sessions = ["Morning (9:15-11:30)", "Mid-Day (11:30-1:30)", "Afternoon (1:30-3:30)"]
        session_stats = []
        for s in sessions:
            prefix = s.split(" ")[0]
            s_df = df[df["session"].str.contains(prefix, case=False, na=False)]
            s_count = len(s_df)
            if s_count > 0:
                s_pnl = s_df["pnl"].sum()
                s_wins = len(s_df[s_df["pnl"] > 0])
                s_winrate = (s_wins / s_count) * 100
                s_avg_rr = s_df["risk_reward"].mean()
            else:
                s_pnl, s_winrate, s_avg_rr = 0.0, 0.0, 0.0
            session_stats.append({"Session": s, "Trades": s_count, "Total P&L": s_pnl, "Win Rate (%)": s_winrate, "Avg R:R": s_avg_rr})
        
        stat_df = pd.DataFrame(session_stats)

        sc1, sc2, sc3 = st.columns(3)
        for idx, col in enumerate([sc1, sc2, sc3]):
            s_row = stat_df.iloc[idx]
            with col:
                col_pnl = "#10b981" if s_row["Total P&L"] >= 0 else "#f43f5e"
                st.markdown(f"""
                <div style="background:#161f30; border:1px solid #1f2937; padding:8px 12px; border-radius:8px; margin: 6px 0;">
                    <h5 style="margin:0; color:#38bdf8; font-size:13px;">{s_row["Session"]}</h5>
                    <div style="color:{col_pnl}; font-size:16px; font-weight:bold; margin:2px 0;">₹{s_row["Total P&L"]:,.2f}</div>
                    <div style="color:#94a3b8; font-size:11px;">Trades: <b>{s_row["Trades"]}</b> | Win Rate: <b>{s_row["Win Rate (%)"]:.1f}%</b></div>
                </div>
                """, unsafe_allow_html=True)

        g1, g2 = st.columns([3, 2])
        with g1:
            df["cumulative_pnl"] = df["pnl"].cumsum()
            df["trade_seq"] = range(1, len(df) + 1)
        
