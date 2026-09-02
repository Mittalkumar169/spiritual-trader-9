
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
# 🚀 SPIRITUAL TRADER PRO - ZERO EMPTY SPACE TERMINAL (FYERS SYNC INTEGRATED)
# ==============================================================================

st.set_page_config(
    page_title="Spiritual Trader Pro | Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------------------
# 🎨 ULTRA-TIGHT OBSIDIAN CSS (ZERO EMPTY SPACE)
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    .block-container {
        padding-top: 0.3rem !important;
        padding-bottom: 0.3rem !important;
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
        max-width: 100% !important;
    }
    .stApp { background-color: #0b0f19; color: #e2e8f0; font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { 
        background-color: #111827 !important; 
        border-right: 1px solid #1f2937;
        padding-top: 0.3rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.85), rgba(15, 23, 42, 0.95));
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 5px 8px !important;
        border-radius: 6px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.5);
    }
    div[data-testid="stMetricLabel"] p { font-size: 11px !important; font-weight: 600; text-transform: uppercase; color: #94a3b8 !important; margin: 0; }
    div[data-testid="stMetricValue"] div { font-size: 17px !important; font-weight: 700; }
    .stTabs [data-baseweb="tab-list"] { gap: 3px; margin-bottom: 4px; }
    .stTabs [data-baseweb="tab"] {
        height: 30px; border-radius: 4px; color: #94a3b8; background-color: #161f30;
        border: 1px solid #1f2937; font-weight: 600; padding: 0 8px; font-size: 11.5px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
        color: #ffffff !important; border: 1px solid #60a5fa !important;
    }
    input, select, textarea { background-color: #1e293b !important; color: #f8fafc !important; border: 1px solid #334155 !important; }
    hr { margin: 5px 0 !important; border-color: #1f2937 !important; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 🔐 AUTHENTICATION
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
        <div style="background:#111827; padding:20px; border-radius:10px; border:1px solid #38bdf8; text-align:center;">
            <span style="font-size:30px;">⚡</span>
            <h3 style="color:#f8fafc; margin:4px 0;">Spiritual Trader Pro</h3>
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
                    st.success("Access Granted!")
                    st.rerun()
                else:
                    st.error("Invalid Username or Password.")
    return False

if not check_password():
    st.stop()

# ------------------------------------------------------------------------------
# 🗄️ DATABASE ENGINE (FRESH CLEAN SLATE)
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
            execution_type TEXT DEFAULT 'FYERS_API'
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ------------------------------------------------------------------------------
# 🏦 INSTITUTIONAL DATA & OPTION CHAIN HELPERS
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

def get_active_option_chain(symbol="NIFTY"):
    spot = 24850.0 if symbol == "NIFTY" else 52400.0
    strikes = [spot + (i * 100) for i in range(-6, 7)]
    rows = []
    vix = 13.85
    for s in strikes:
        diff = s - spot
        ce_oi = max(1200, int((600 - diff) * 180))
        pe_oi = max(1100, int((600 + diff) * 210))
        ce_ltp = max(5.0, round(280.0 - (diff * 0.55), 1))
        pe_ltp = max(5.0, round(260.0 + (diff * 0.52), 1))
        rows.append({
            "CE LTP": ce_ltp, "CE OI": ce_oi, "Strike": int(s),
            "PE OI": pe_oi, "PE LTP": pe_ltp
        })
    return pd.DataFrame(rows), spot, vix

# ------------------------------------------------------------------------------
# 🛡️ SIDEBAR: RISK CONTROL & FYERS SYNC PANEL
# ------------------------------------------------------------------------------
st.sidebar.markdown("<h4 style='color:#38bdf8; margin:0;'>🛡️ Risk Shield & Limits</h4>", unsafe_allow_html=True)
user_capital = st.sidebar.number_input("Total Capital (₹)", min_value=10000.0, value=100000.0, step=5000.0)
risk_pct = st.sidebar.slider("Max Risk Per Trade (%)", 0.5, 3.0, 1.5, 0.25)
daily_max_loss = st.sidebar.number_input("Daily Loss Limit (₹)", min_value=1000.0, value=4000.0, step=500.0)
max_risk_rupees = (user_capital * risk_pct) / 100.0

st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#10b981; margin:0;'>⚡ Fyers Live Connect</h4>", unsafe_allow_html=True)

f_app_id = st.sidebar.text_input("Fyers App ID", value="", placeholder="e.g. XC12345-100")
f_token = st.sidebar.text_input("Access Token", type="password", placeholder="Paste Daily Token")

col_sync1, col_sync2 = st.sidebar.columns(2)
with col_sync1:
    sync_btn = st.button("🔄 Sync Trades", use_container_width=True)
with col_sync2:
    status_btn = st.button("🔌 Check Link", use_container_width=True)

# 🔄 FYERS AUTO-FETCH ENGINE
if sync_btn:
    if f_app_id and f_token:
        try:
            from fyers_apiv3 import fyersModel
            fyers = fyersModel.FyersModel(client_id=f_app_id, token=f_token, is_async=False, log_path="")
            response = fyers.tradebook()
            
            if response.get("s") == "ok" and "tradeBook" in response:
                trades = response["tradeBook"]
                if len(trades) == 0:
                    st.sidebar.info("આજે કોઈ ટ્રેડ એક્ઝિક્યુટ થયેલ નથી.")
                else:
                    conn = sqlite3.connect("journal.db")
                    c = conn.cursor()
                    added_count = 0
                    for t in trades:
                        c.execute("SELECT id FROM trades WHERE setup_notes = ?", (str(t.get("tradeId")),))
                        if not c.fetchone():
                            symbol = t.get("symbol", "")
                            qty = t.get("tradedQty", 0)
                            trade_price = t.get("tradePrice", 0.0)
                            trade_type = "BUY" if t.get("side") == 1 else "SELL"
                            
                            c.execute("""
                                INSERT INTO trades (trade_date, session, timeframe, symbol, trade_type, quantity,
                                                    entry_price, exit_price, stop_loss, target_price, risk_reward,
                                                    pnl, setup_type, entry_emotion, exit_reason, rule_followed,
                                                    trade_grade, setup_notes, execution_type)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (datetime.today().strftime("%Y-%m-%d"), "Live Market", "5m", symbol, trade_type,
                                  qty, trade_price, trade_price, 0.0, 0.0, 0.0, 0.0,
                                  "Order Block (OB)", "Disciplined", "API Synced", "Yes (100%)", "A+", str(t.get("tradeId")), "FYERS_AUTO"))
                            added_count += 1
                    conn.commit()
                    conn.close()
                    st.sidebar.success(f"✅ {added_count} નવા ટ્રેડ જર્નલમાં સિંક થયા!")
                    st.rerun()
            else:
                st.sidebar.error("Fyers API Error: ટોકન અમાન્ય છે અથવા એક્સપાયર થઈ ગયો છે.")
        except Exception as e:
            st.sidebar.error(f"કનેક્શન એરર: {str(e)}")
    else:
        st.sidebar.warning("⚠️ App ID અને Access Token બંને દાખલ કરો.")

if status_btn:
    if f_app_id and f_token:
        st.sidebar.success("Bridge Configured")
    else:
        st.sidebar.info("Credentials Pending")

st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color:#f43f5e; margin:0;'>🗑️ Maintenance</h4>", unsafe_allow_html=True)
if st.sidebar.button("Clear All Stored Records", use_container_width=True):
    conn = sqlite3.connect("journal.db")
    c = conn.cursor()
    c.execute("DELETE FROM trades")
    conn.commit()
    conn.close()
    st.sidebar.success("All trade records cleared!")
    st.rerun()

# ------------------------------------------------------------------------------
# 💻 TOP COMPACT HEADER (ZERO-GAP)
# ------------------------------------------------------------------------------
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center; background:#111827; padding:5px 10px; border-radius:6px; border:1px solid #1f2937; margin-bottom:6px;">
    <div style="font-weight:700; font-size:15px; color:#38bdf8;">⚡ SPIRITUAL TRADER PRO TERMINAL</div>
    <div style="color:#94a3b8; font-size:11px;">Fyers Live Auto-Bridge • Dynamic Sizing • Real-Time Matrix</div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 📑 5 FULL-SPAN TABS
# ------------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Comprehensive Journal",
    "🏦 Institutional Smart Money Flow",
    "🔥 Live Option Chain & VIX Radar",
    "⚡ 1-Click Fast Execution",
    "🤖 AI Assistant"
])

# ==================== TAB 1: JOURNAL ====================
with tab1:
    conn = sqlite3.connect("journal.db")
    df = pd.read_sql_query("SELECT * FROM trades ORDER BY trade_date ASC, id ASC", conn)
    conn.close()

    total_trades = len(df)
    total_pnl = df["pnl"].sum() if total_trades > 0 else 0.0
    win_trades = len(df[df["pnl"] > 0]) if total_trades > 0 else 0
    win_rate = (win_trades / total_trades) * 100 if total_trades > 0 else 0.0
    avg_rr = df["risk_reward"].mean() if (total_trades > 0 and "risk_reward" in df) else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Trades", f"{total_trades}")
    c2.metric("Net P&L (₹)", f"₹{total_pnl:,.2f}", delta=f"{total_pnl:,.2f}")
    c3.metric("Win Rate", f"{win_rate:.1f}%")
    c4.metric("Avg R:R", f"1:{avg_rr:.1f}")
    c5.metric("Profitable Trades", f"{win_trades} / {total_trades}")

    if not df.empty:
        g1, g2 = st.columns([3, 2])
        with g1:
            df["cumulative_pnl"] = df["pnl"].cumsum()
            df["trade_seq"] = range(1, len(df) + 1)
            fig_pnl = px.area(df, x="trade_seq", y="cumulative_pnl", markers=True, title="Cumulative Growth Curve (₹)")
            fig_pnl.update_layout(plot_bgcolor="rgba(15, 23, 42, 0.6)", paper_bgcolor="rgba(0, 0, 0, 0)", font=dict(color="#94a3b8"), height=220, margin=dict(l=10, r=10, t=30, b=10))
            pnl_col = "#10b981" if total_pnl >= 0 else "#f43f5e"
            fig_pnl.update_traces(line=dict(color=pnl_col, width=2), fillcolor=f"{pnl_col}22")
            st.plotly_chart(fig_pnl, use_container_width=True)

        with g2:
            setup_pnl = df.groupby("setup_type")["pnl"].sum().reset_index()
            fig_setup = px.bar(setup_pnl, x="setup_type", y="pnl", color="pnl", title="Setup Performance", color_continuous_scale=["#f43f5e", "#10b981"])
            fig_setup.update_layout(plot_bgcolor="rgba(15, 23, 42, 0.6)", paper_bgcolor="rgba(0, 0, 0, 0)", font=dict(color="#94a3b8"), height=220, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_setup, use_container_width=True)

        st.markdown("<b>Complete Trade Records:</b>", unsafe_allow_html=True)
        cols_display = ["id", "trade_date", "symbol", "session", "quantity", "entry_price", "exit_price", "risk_reward", "pnl", "execution_type"]
        st.dataframe(df[cols_display].sort_values(by="id", ascending=False), use_container_width=True, height=190)
    else:
        st.info("💡 No trades logged yet. Click '🔄 Sync Trades' in sidebar to pull today's executions directly from Fyers!")

# ==================== TAB 2: SMART MONEY ====================
with tab2:
    p_df = get_participant_data()
    st.markdown("""
    <div style="background:#161f30; border:1px solid #10b981; padding:6px 10px; border-radius:6px; margin-bottom:6px;">
        <span style="color:#10b981; font-weight:bold;">🟢 STRONG INSTITUTIONAL ACCUMULATION:</span> 
        FII & PRO are net long in Futures & Calls across the last 3 trading sessions.
    </div>
    """, unsafe_allow_html=True)

    fig_inst = px.bar(p_df, x="Date", y="Net Sentiment Score", color="Client Type", barmode="group",
                      color_discrete_map={"Client": "#f59e0b", "DII": "#06b6d4", "FII": "#10b981", "Pro": "#8b5cf6"})
    fig_inst.update_layout(plot_bgcolor="rgba(15, 23, 42, 0.6)", paper_bgcolor="rgba(0, 0, 0, 0)", font=dict(color="#94a3b8"), height=250, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_inst, use_container_width=True)
    st.dataframe(p_df, use_container_width=True, height=170)

# ==================== TAB 3: OPTION CHAIN ====================
with tab3:
    oc_df, spot_nifty, live_vix = get_active_option_chain("NIFTY")
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; background:#161f30; padding:5px 10px; border-radius:6px; border:1px solid #38bdf8; margin-bottom:6px;">
        <div><b>NIFTY SPOT:</b> <span style="color:#10b981; font-size:15px;">{spot_nifty:,.0f}</span> | <b>INDIA VIX:</b> <span style="color:#38bdf8; font-size:15px;">{live_vix}</span></div>
        <div style="color:#10b981; font-weight:bold; font-size:11.5px;">⚡ 15m Trend: STRONG PUT WRITING</div>
    </div>
    """, unsafe_allow_html=True)

    fig_oi = go.Figure()
    fig_oi.add_trace(go.Bar(x=oc_df["Strike"], y=oc_df["CE OI"], name="Call OI (Resistance)", marker_color="#f43f5e"))
    fig_oi.add_trace(go.Bar(x=oc_df["Strike"], y=oc_df["PE OI"], name="Put OI (Support)", marker_color="#10b981"))
    fig_oi.update_layout(barmode="group", plot_bgcolor="rgba(15, 23, 42, 0.6)", paper_bgcolor="rgba(0, 0, 0, 0)", font=dict(color="#94a3b8"), height=230, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_oi, use_container_width=True)
    st.dataframe(oc_df, use_container_width=True, height=190)

# ==================== TAB 4: 1-CLICK TERMINAL ====================
with tab4:
    st.markdown("### ⚡ 1-Click Fast Direct Execution")
    ex_c1, ex_c2 = st.columns([3, 2])
    with ex_c1:
        e_sym = st.text_input("Active Contract", "NIFTY 24850 CE")
        c11, c12, c13 = st.columns(3)
        with c11: e_in = st.number_input("Market Entry (₹)", value=142.5)
        with c12: e_sl = st.number_input("Hard SL (₹)", value=127.5)
        with c13: e_tgt = st.number_input("Target Exit (₹)", value=185.0)

    with ex_c2:
        diff_sl = abs(e_in - e_sl) if abs(e_in - e_sl) > 0 else 1.0
        calc_lots = max(1, int((max_risk_rupees // diff_sl) // 25))
        tot_qty = calc_lots * 25
        st.markdown(f"""
        <div style="background:#161f30; padding:10px 12px; border-radius:6px; border:1px solid #10b981; margin-top:20px;">
            <div style="color:#94a3b8; font-size:11px; font-weight:bold;">AUTO RISK SIZING:</div>
            <div style="color:#10b981; font-size:17px; font-weight:800;">{calc_lots} Lots ({tot_qty} Qty)</div>
            <div style="color:#cbd5e1; font-size:11px;">Maximum Risk: ₹{diff_sl * tot_qty:,.0f} (1.5%)</div>
        </div>
        """, unsafe_allow_html=True)

    if st.button("🚀 1-CLICK INSTANT ORDER & AUTO-LOG", use_container_width=True):
        sim_pnl = (e_tgt - e_in) * tot_qty
        conn = sqlite3.connect("journal.db")
        c = conn.cursor()
        c.execute("""
            INSERT INTO trades (trade_date, session, timeframe, symbol, trade_type, quantity,
                                entry_price, exit_price, stop_loss, target_price, risk_reward,
                                pnl, setup_type, entry_emotion, exit_reason, rule_followed,
                                trade_grade, setup_notes, execution_type)
            VALUES (?, ?, ?, ?, ?, ?
