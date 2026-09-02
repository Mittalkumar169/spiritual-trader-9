
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
    .block-container {{ padding: 0.5rem 0.8rem !important; max-width: 100% !important; }}
    .stApp {{ background-color: {bg_color}; color: {text_color}; font-family: sans-serif; }}
    section[data-testid="stSidebar"] {{ background-color: {sidebar_bg} !important; border-right: 1px solid {border_col}; }}
    div[data-testid="stMetric"] {{ background: {metric_bg}; border: 1px solid {border_col}; padding: 8px !important; border-radius: 8px; }}
    .stTabs [data-baseweb="tab"] {{ height: 35px; border-radius: 6px; background-color: {tab_bg}; color: {text_color}; }}
    .stTabs [aria-selected="true"] {{ background: #2563eb !important; color: #ffffff !important; }}
</style>
""", unsafe_allow_html=True)

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.markdown("<br><h3 style='text-align:center;'>⚡ Spiritual Trader Pro</h3>", unsafe_allow_html=True)
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

def init_db():
    conn = sqlite3.connect("journal.db")
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS trades (id INTEGER PRIMARY KEY AUTOINCREMENT, trade_date TEXT, session TEXT, timeframe TEXT, symbol TEXT, trade_type TEXT, quantity INTEGER, entry_price REAL, exit_price REAL, stop_loss REAL, target_price REAL, risk_reward REAL, pnl REAL, setup_type TEXT, entry_emotion TEXT, exit_reason TEXT, rule_followed TEXT, trade_grade TEXT, setup_notes TEXT, execution_type TEXT DEFAULT 'MANUAL', chart_img TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, val TEXT)")
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

p_pic = get_db_val("profile_pic")
if p_pic:
    st.sidebar.markdown(f'<div style="text-align:center;"><img src="data:image/png;base64,{p_pic}" style="width:80px;height:80px;border-radius:50%;border:2px solid #38bdf8;"></div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<div style="text-align:center;font-size:40px;">👤</div>', unsafe_allow_html=True)

st.sidebar.markdown("<div style='text-align:center;font-weight:bold;'>Lead Institutional Trader</div>", unsafe_allow_html=True)

with st.sidebar.expander("📷 Update Profile Photo", expanded=False):
    with st.form("photo_form"):
        up_img = st.file_uploader("Choose Photo", type=["jpg", "png", "jpeg"])
        submitted = st.form_submit_button("Upload Photo", use_container_width=True)
        if submitted and up_img:
            set_db_val("profile_pic", base64.b64encode(up_img.read()).decode())
            st.success("Photo Updated Successfully!")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("<b>🛡️ Capital & Risk</b>", unsafe_allow_html=True)
u_capital = st.sidebar.number_input("Capital (₹)", min_value=10000.0, value=100000.0, step=5000.0)
r_pct = st.sidebar.slider("Risk (%)", 0.5, 3.0, 1.5, 0.25)
d_loss = st.sidebar.number_input("Daily Stop Loss (₹)", min_value=1000.0, value=4000.0, step=500.0)
max_r_amt = (u_capital * r_pct) / 100.0

st.sidebar.markdown("---")
st.sidebar.markdown("<b>⚡ Fyers Live Connect</b>", unsafe_allow_html=True)
app_id_val = st.sidebar.text_input("App ID", value=get_db_val("f_app_id") or "8THHZH0S7K-200")
sec_id_val = st.sidebar.text_input("Secret ID", value=get_db_val("f_sec_id") or "RVdcb1TLXE7r9ftE", type="password")

with st.sidebar.expander("🔑 Generate Daily Token", expanded=True):
    code_in = st.text_area("Auth Code Here", placeholder="Paste code")
    if st.button("Generate Token", use_container_width=True):
        if app_id_val and sec_id_val and code_in:
            try:
                hash_v = hashlib.sha256(f"{app_id_val}:{sec_id_val}".encode()).hexdigest()
                resp = requests.post("https://api-t1.fyers.in/api/v3/validate-authcode", json={"grant_type": "authorization_code", "appIdHash": hash_v, "code": code_in.strip()})
                res_d = resp.json()
                if res_d.get("s") == "ok" and "access_token" in res_d:
                    set_db_val("f_app_id", app_id_val)
                    set_db_val("f_sec_id", sec_id_val)
                    set_db_val("f_token", res_d["access_token"])
                    st.success("Token Generated!")
                    st.rerun()
                else:
                    st.error("Error: " + res_d.get("message", "Invalid code"))
            except Exception as e:
                st.error(f"Error: {e}")

live_tok = get_db_val("f_token")
if live_tok:
    st.sidebar.success("● Live Token Connected")

if st.sidebar.button("🔄 Sync Today's Trades", use_container_width=True):
    if app_id_val and live_tok:
        try:
            r = requests.get("https://api-t1.fyers.in/api/v3/positions", headers={"Authorization": f"{app_id_val}:{live_tok}"})
            pos_data = r.json()
            if pos_data.get("s") == "ok":
                net_positions = pos_data.get("netPositions", [])
                if len(net_positions) == 0:
                    st.sidebar.info("આજે કોઈ પોઝિશન મળી નથી.")
                else:
                    conn = sqlite3.connect("journal.db")
                    cur = conn.cursor()
                    ins_sql = "INSERT INTO trades (trade_date, session, timeframe, symbol, trade_type, quantity, entry_price, exit_price, stop_loss, target_price, risk_reward, pnl, setup_type, entry_emotion, exit_reason, rule_followed, trade_grade, setup_notes, execution_type, chart_img) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                    c_cnt = 0
                    for pos in net_positions:
                        sym = pos.get("symbol", "")
                        qty = abs(pos.get("netQty", 0)) or abs(pos.get("qty", 0))
                        buy_avg = pos.get("buyAvg", 0.0)
                        sell_avg = pos.get("sellAvg", 0.0)
                        pnl_val = pos.get("pl", 0.0)
                        side_str = "BUY" if pos.get("side", 1) == 1 else "SELL"
                        
                        cur.execute("SELECT id FROM trades WHERE symbol = ? AND trade_date = ?", (sym, datetime.today().strftime("%Y-%m-%d")))
                        if not cur.fetchone() and (qty > 0 or pnl_val != 0):
                            entry_p = buy_avg if buy_avg > 0 else sell_avg
                            exit_p = sell_avg if sell_avg > 0 else buy_avg
                            v = (datetime.today().strftime("%Y-%m-%d"), "Live Market", "5m", sym, side_str, int(qty), float(entry_p), float(exit_p), 0.0, 0.0, 0.0, float(pnl_val), "Smart Money", "Disciplined", "API Synced", "Yes (100%)", "A+", f"FYERS_AUTO_{sym}", "FYERS_AUTO", None)
                            cur.execute(ins_sql, v)
                            c_cnt += 1
                    conn.commit()
                    conn.close()
                    st.sidebar.success(f"✅ {c_cnt} ટ્રેડ્સ ઓટોમેટિક સિંક થયા!")
                    st.rerun()
            else:
                st.sidebar.error("Fyers API Error")
        except Exception as e:
            st.sidebar.error(str(e))

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Database Records", use_container_width=True):
    conn = sqlite3.connect("journal.db")
    c = conn.cursor()
    c.execute("DELETE FROM trades")
    conn.commit()
    conn.close()
    st.sidebar.success("Records Cleared!")
    st.rerun()

st.markdown("<div style='font-size:18px;font-weight:bold;color:#2563eb;margin-bottom:8px;'>⚡ SPIRITUAL TRADER PRO TERMINAL</div>", unsafe_allow_html=True)

t1, t2, t3, t4, t5, t6 = st.tabs([
    "📊 Journal & Analytics",
    "⚡ Trade Execution / Fast Log",
    "🏦 Institutional Flow",
    "🔥 Option Chain & VIX",
    "🔍 Performance Analysis",
    "🤖 AI Assistant"
])

with t1:
    conn = sqlite3.connect("journal.db")
    df = pd.read_sql_query("SELECT * FROM trades ORDER BY id ASC", conn)
    conn.close()

    total_t = len(df)
    net_pnl = df["pnl"].sum() if total_t > 0 else 0.0
    w_trades = len(df[df["pnl"] > 0]) if total_t > 0 else 0
    l_trades = len(df[df["pnl"] < 0]) if total_t > 0 else 0
    w_rate = (w_trades / total_t * 100) if total_t > 0 else 0.0
    avg_r = df["risk_reward"].mean() if total_t > 0 else 0.0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Trades", str(total_t))
    m2.metric("P&L (₹)", f"₹{net_pnl:,.2f}")
    m3.metric("Win Rate", f"{w_rate:.1f}%")
    m4.metric("Avg R:R", f"1:{avg_r:.1f}")
    m5.metric("W / L", f"{w_trades}W / {l_trades}L")

    if not df.empty:
        df["cum_pnl"] = df["pnl"].cumsum()
        df["trade_no"] = range(1, len(df) + 1)
        fig_eq = px.area(df, x="trade_no", y="cum_pnl", title="Equity Curve (₹)")
        fig_eq.update_layout(template=plotly_template)
        st.plotly_chart(fig_eq, use_container_width=True)
        st.dataframe(df[["id", "trade_date", "symbol", "session", "trade_type", "quantity", "entry_price", "exit_price", "pnl", "setup_type", "rule_followed"]], use_container_width=True)
        st.download_button("📥 Export CSV", data=df.to_csv(index=False).encode('utf-8'), file_name="trades.csv", mime="text/csv")
    else:
        st.info("જર્નલ ખાલી છે. Fyers માંથી સિંક કરો.")

with t2:
    st.markdown("<b>Fast Trade Log</b>", unsafe_allow_html=True)
    c_e = st.number_input("Calc: Entry (₹)", value=140.0, step=0.5)
    c_s = st.number_input("Calc: Hard SL (₹)", value=125.0, step=0.5)
    diff = abs(c_e - c_s) if abs(c_e - c_s) > 0 else 1.0
    s_lots = max(1, int((max_r_amt // diff) // 25))
    s_qty = s_lots * 25
    st.info(f"Recommended: {s_lots} Lots ({s_qty} Qty) | Max Loss: ₹{diff * s_qty:,.0f}")

    with st.form("tr_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            sym = st.text_input("Symbol", "NIFTY 24850 CE")
            ses = st.selectbox("Session", ["Morning", "Mid-Day", "Closing"])
            tf = st.selectbox("Timeframe", ["1m", "3m", "5m", "15m", "1H"])
        with col2:
            tt = st.selectbox("Type", ["BUY", "SELL"])
            en = st.number_input("Entry (₹)", value=float(c_e), step=0.5)
            ex = st.number_input("Exit (₹)", value=170.0, step=0.5)
        with col3:
            sl = st.number_input("SL (₹)", value=float(c_s), step=0.5)
            tg = st.number_input("Target (₹)", value=180.0, step=0.5)
            qt = st.number_input("Quantity", value=int(s_qty), step=25)

        col4, col5, col6 = st.columns(3)
        with col4:
            stp = st.selectbox("Setup", ["Order Block", "FVG", "Liquidity Sweep", "Break of Structure"])
        with col5:
            emo = st.selectbox("Emotion", ["Disciplined", "FOMO", "Revenge"])
        with col6:
            rul = st.selectbox("Rule Followed", ["Yes (100%)", "No (Violated SL)"])

        notes = st.text_input("Notes", "Clean structure setup")
        c_shot = st.file_uploader("Chart Screenshot (Optional)", type=["png", "jpg", "jpeg"])

        if st.form_submit_button("Save Trade", use_container_width=True):
            r_val = abs(en - sl) if abs(en - sl) > 0 else 1.0
            rr_val = round(abs(tg - en) / r_val, 2)
            c_pnl = (ex - en) * qt if tt == "BUY" else (en - ex) * qt
            i_b64 = base64.b64encode(c_shot.read()).decode() if c_shot else None
            conn = sqlite3.connect("journal.db")
            c = conn.cursor()
            q_ins = "INSERT INTO trades (trade_date, session, timeframe, symbol, trade_type, quantity, entry_price, exit_price, stop_loss, target_price, risk_reward, pnl, setup_type, entry_emotion, exit_reason, rule_followed, trade_grade, setup_notes, execution_type, chart_img) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
            c.execute(q_ins, (datetime.today().strftime("%Y-%m-%d"), ses, tf, sym, tt, qt, en, ex, sl, tg, rr_val, c_pnl, stp, emo, "Manual Exit", rul, "A+", notes, "MANUAL", i_b64))
            conn.commit()
            conn.close()
            st.success(f"Saved! P&L: ₹{c_pnl:,.2f}")
            st.rerun()

with t3:
    st.info("NSE Participant Positioning (FII vs DII vs Retail)")
    d_list = [(datetime.today() - timedelta(days=i)).strftime("%d-%m-%Y") for i in [2, 1, 0]]
    inst_records = [
        {"Date": d_list[0], "Client Type": "Retail", "Net Sentiment": -51100},
        {"Date": d_list[0], "Client Type": "DII", "Net Sentiment": 21200},
        {"Date": d_list[0], "Client Type": "FII", "Net Sentiment": 85000},
        {"Date": d_list[1], "Client Type": "Retail", "Net Sentiment": -71000},
        {"Date": d_list[1], "Client Type": "DII", "Net Sentiment": 24500},
        {"Date": d_list[1], "Client Type": "FII", "Net Sentiment": 98000},
        {"Date": d_list[2], "Client Type": "Retail", "Net Sentiment": -95000},
        {"Date": d_list[2], "Client Type": "DII", "Net Sentiment": 28900},
        {"Date": d_list[2], "Client Type": "FII", "Net Sentiment": 118000}
    ]
    fig_inst = px.bar(pd.DataFrame(inst_records), x="Date", y="Net Sentiment", color="Client Type", barmode="group")
    fig_inst.update_layout(template=plotly_template)
    st.plotly_chart(fig_inst, use_container_width=True)

with t4:
    st.info("NIFTY Spot: 24,850 | INDIA VIX: 13.85 | Bias: Bullish Support at 24,800")
    s_list = [24850 + (i * 100) for i in range(-4, 5)]
    oc_data = [{"Strike": s, "Call OI": max(1500, int((500 - (s - 24850)) * 200)), "Put OI": max(1500, int((500 + (s - 24850)) * 250))} for s in s_list]
    df_oc = pd.DataFrame(oc_data)
    fig_o = go.Figure()
    fig_o.add_trace(go.Bar(x=df_oc["Strike"], y=df_oc["Call OI"], name="Call OI", marker_color="#f43f5e"))
    fig_o.add_trace(go.Bar(x=df_oc["Strike"], y=df_oc["Put OI"], name="Put OI", marker_color="#10b981"))
    fig_o.update_layout(barmode="group", height=260, template=plotly_template)
    st.plotly_chart(fig_o, use_container_width=True)

with t5:
    conn = sqlite3.connect("journal.db")
    df_p = pd.read_sql_query("SELECT * FROM trades", conn)
    conn.close()
    if not df_p.empty:
        fig_pie = px.pie(df_p, names="rule_followed", title="Discipline Rate")
        fig_pie.update_layout(template=plotly_template)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("એનાલિટિક્સ માટે પહેલાં ટ્રેડ્સ લૉગ કરો.")

with t6:
    st.markdown("<b>Spiritual Trader AI Rules</b>", unsafe_allow_html=True)
    st.write("1. Protect capital first. Always respect predefined Stop Loss.")
    st.write("2. Wait patiently for liquidity sweeps before execution.")

