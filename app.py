
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
    .block-container {{ padding: 0.4rem 0.6rem !important; max-width: 100% !important; }}
    .stApp {{ background-color: {bg_color}; color: {text_color}; font-family: sans-serif; }}
    section[data-testid="stSidebar"] {{ background-color: {sidebar_bg} !important; border-right: 1px solid {border_col}; min-width: 220px !important; max-width: 220px !important; }}
    div[data-testid="stMetric"] {{ background: {metric_bg}; border: 1px solid {border_col}; padding: 6px !important; border-radius: 6px; }}
    .stTabs [data-baseweb="tab"] {{ height: 32px; border-radius: 6px; background-color: {tab_bg}; color: {text_color}; }}
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

if "profile_pic_b64" not in st.session_state:
    st.session_state["profile_pic_b64"] = get_db_val("profile_pic")

p_pic = st.session_state["profile_pic_b64"]

col_p1, col_p2 = st.sidebar.columns([1, 3])
with col_p1:
    if p_pic:
        st.markdown(f'<img src="data:image/png;base64,{p_pic}" style="width:32px;height:32px;border-radius:50%;border:1px solid #38bdf8;object-fit:cover;">', unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size:20px;text-align:center;">👤</div>', unsafe_allow_html=True)
with col_p2:
    st.markdown("<div style='font-weight:bold;font-size:11px;padding-top:6px;'>Mittalkumar M.</div>", unsafe_allow_html=True)

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

# Fetch Live Capital from Fyers Funds API automatically if connected
default_capital = float(get_db_val("tot_cap") or 10000.0)
if app_id_val and live_tok:
    try:
        funds_resp = requests.get("https://api-t1.fyers.in/api/v3/funds", headers={"Authorization": f"{app_id_val}:{live_tok}"})
        funds_data = funds_resp.json()
        if funds_data.get("s") == "ok":
            for item in funds_data.get("fund_limit", []):
                if item.get("title") == "Client Balance" or "Total Balance" in str(item.get("title")):
                    live_bal = float(item.get("equityAmount", 0.0))
                    if live_bal > 0:
                        default_capital = live_bal
    except Exception:
        pass

st.sidebar.markdown("---")
st.sidebar.markdown("<b>🛡️ Capital & Risk Management</b>", unsafe_allow_html=True)
total_capital = st.sidebar.number_input("Total Capital (₹)", min_value=1000.0, value=default_capital, step=1000.0)
risk_pct = st.sidebar.slider("Max Risk / Trade (%)", 0.5, 5.0, float(get_db_val("risk_pct") or 2.0), 0.5)
max_allowed_trades = st.sidebar.number_input("Max Trades / Day", min_value=1, max_value=20, value=int(get_db_val("max_trades") or 3))

max_risk_amt = (total_capital * risk_pct) / 100.0
st.sidebar.info(f"💡 Per Trade Max Risk: ₹{max_risk_amt:,.0f}")

set_db_val("tot_cap", str(total_capital))
set_db_val("risk_pct", str(risk_pct))
set_db_val("max_trades", str(max_allowed_trades))

if st.sidebar.button("🔄 Sync Trades & Capital", use_container_width=True):
    if app_id_val and live_tok:
        try:
            r = requests.get("https://api-t1.fyers.in/api/v3/positions", headers={"Authorization": f"{app_id_val}:{live_tok}"})
            pos_data = r.json()
            if pos_data.get("s") == "ok":
                net_positions = pos_data.get("netPositions", [])
                conn = sqlite3.connect("journal.db")
                cur = conn.cursor()
                ins_sql = "INSERT INTO trades (trade_date, session, timeframe, symbol, trade_type, quantity, entry_price, exit_price, stop_loss, target_price, risk_reward, pnl, setup_type, entry_emotion, exit_reason, rule_followed, trade_grade, setup_notes, execution_type, chart_img) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                c_cnt = 0
                today_str = datetime.today().strftime("%Y-%m-%d")
                
                for pos in net_positions:
                    sym = pos.get("symbol", "")
                    qty = abs(pos.get("netQty", 0)) or abs(pos.get("qty", 0))
                    buy_avg = pos.get("buyAvg", 0.0)
                    sell_avg = pos.get("sellAvg", 0.0)
                    pnl_val = pos.get("pl", 0.0)
                    side_str = "BUY" if pos.get("side", 1) == 1 else "SELL"
                    
                    cur.execute("SELECT id FROM trades WHERE symbol = ? AND trade_date = ?", (sym, today_str))
                    if not cur.fetchone() and (qty > 0 or pnl_val != 0):
                        entry_p = buy_avg if buy_avg > 0 else sell_avg
                        exit_p = sell_avg if sell_avg > 0 else buy_avg
                        rule_status = "Yes (100%)"
                        violations = []
                        if pnl_val < 0 and abs(pnl_val) > max_risk_amt:
                            violations.append(f"Risk Limit Crossed")
                            rule_status = "No (Risk Violated)"

                        v = (today_str, "Live Market", "5m", sym, side_str, int(qty), float(entry_p), float(exit_p), 0.0, 0.0, 1.5, float(pnl_val), "Smart Money", "Disciplined", "API Synced", rule_status, "A+", f"FYERS_AUTO_{sym}", "FYERS_AUTO", None)
                        cur.execute(ins_sql, v)
                        c_cnt += 1
                conn.commit()
                conn.close()
                st.sidebar.success(f"✅ {c_cnt} ટ્રેડ્સ સિંક થયા!")
                st.rerun()
            else:
                st.sidebar.error("Fyers API Error")
        except Exception as e:
            st.sidebar.error(str(e))

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ Clear Records", use_container_width=True):
    conn = sqlite3.connect("journal.db")
    c = conn.cursor()
    c.execute("DELETE FROM trades")
    conn.commit()
    conn.close()
    st.sidebar.success("Cleared!")
    st.rerun()

st.markdown("<div style='font-size:16px;font-weight:bold;color:#2563eb;margin-bottom:6px;'>⚡ SPIRITUAL TRADER PRO TERMINAL</div>", unsafe_allow_html=True)

t1, t2, t3, t4, t5 = st.tabs([
    "📊 Journal & Analytics",
    "📈 Performance Insights",
    "🏦 Institutional Flow",
    "🔥 Option Chain & VIX",
    "🤖 AI & Rule Assistant"
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
    m1.metric("Total Trades", str(total_t))
    m2.metric("Net P&L (₹)", f"₹{net_pnl:,.2f}")
    m3.metric("Win Rate", f"{w_rate:.1f}%")
    m4.metric("Avg R:R", f"1:{avg_r:.1f}")
    m5.metric("Wins / Losses", f"{w_trades}W / {l_trades}L")

    if not df.empty:
        df["cum_pnl"] = df["pnl"].cumsum()
        df["trade_no"] = range(1, len(df) + 1)
        fig_eq = px.area(df, x="trade_no", y="cum_pnl", title="Equity Growth Curve (₹)")
        fig_eq.update_layout(template=plotly_template, height=220, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_eq, use_container_width=True)
        st.markdown("<b>📋 Synced Trades Log & Automated Audit Report</b>", unsafe_allow_html=True)
        st.dataframe(df[["id", "trade_date", "symbol", "trade_type", "quantity", "pnl", "rule_followed", "setup_notes"]], use_container_width=True)
        st.download_button("📥 Export Journal CSV", data=df.to_csv(index=False).encode('utf-8'), file_name="trades.csv", mime="text/csv")
    else:
        st.info("જર્નલ ખાલી છે. Fyers માંથી 'Sync Trades & Capital' બટન દબાવીને ટ્રેડ્સ ખેંચો.")

with t2:
    st.markdown("<b>🔍 Performance & Behavioral Insights</b>", unsafe_allow_html=True)
    conn = sqlite3.connect("journal.db")
    df_p = pd.read_sql_query("SELECT * FROM trades", conn)
    conn.close()
    if not df_p.empty:
        col_a, col_b = st.columns(2)
        with col_a:
            fig_pie = px.pie(df_p, names="rule_followed", title="Discipline & Rule Following Rate")
            fig_pie.update_layout(template=plotly_template, height=260, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_b:
            fig_bar = px.bar(df_p, x="symbol", y="pnl", color="trade_type", title="P&L by Symbol/Instrument")
            fig_bar.update_layout(template=plotly_template, height=260, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("એનાલિટિક્સ જોવા માટે પહેલાં ટ્રેડ્સ સિંક કરો.")

with t3:
    st.markdown("<b>🏦 Participant-wise Open Interest & Summary Matrix</b>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background-color:#1e293b; padding: 14px; border-radius: 8px; border-left: 5px solid #2563eb; margin-bottom: 15px;">
        <h4 style="color:#38bdf8; margin:0 0 6px 0;">⚡ Smart Money Trend & Summary Matrix:</h4>
        <p style="font-size:14px; color:#cbd5e1; margin:0 0 6px 0;">
            • <b>FII Long Ftrs:</b> 17,230 (9.00%) | <b>Short Ftrs:</b> 174,180 (91.00%) | Total: 191,410<br>
            • <b>Client (Retail):</b> Net Bearish / Trapped in Puts & Short Calls<br>
            • <b>FII & Pro:</b> Net Bullish in Index Calls & Index Futures
        </p>
        <hr style="border:0; border-top:1px solid #334155; margin:8px 0;">
        <p style="font-size:15px; font-weight:bold; color:#10b981; margin:0;">
            🟢 OVERALL MARKET BIAS: STRONG BULLISH (BUY ON DIPS)
        </p>
    </div>
    """, unsafe_allow_html=True)

    excel_sheet_data = [
        {"Participant Group": "Clients (Retail)", "Instrument": "Stock Futures", "Today": "-2,556", "1 Day Ago": "31,693", "2 Days Ago": "112,827", "Net Change": "-2,556", "Summary / Action": "sold net", "Bias": "🔴 bearish"},
        {"Participant Group": "Clients (Retail)", "Instrument": "Index Futures", "Today": "46", "1 Day Ago": "-156,950", "2 Days Ago": "-158,184", "Net Change": "46", "Summary / Action": "sold net", "Bias": "🔴 bearish"},
        {"Participant Group": "Clients (Retail)", "Instrument": "Index Calls", "Today": "1,234", "1 Day Ago": "12,430", "2 Days Ago": "11,062", "Net Change": "1,234", "Summary / Action": "sold net", "Bias": "🔴 bearish"},
        {"Participant Group": "Clients (Retail)", "Instrument": "Index Puts", "Today": "1,368", "1 Day Ago": "-1,042", "2 Days Ago": "-425", "Net Change": "1,368", "Summary / Action": "bought net", "Bias": "🔴 bearish"},
        
        {"Participant Group": "FII", "Instrument": "Stock Futures", "Today": "44,831", "1 Day Ago": "143,821", "2 Days Ago": "-46,475", "Net Change": "31,092", "Summary / Action": "bought net", "Bias": "🟢 bullish"},
        {"Participant Group": "FII", "Instrument": "Index Futures", "Today": "1,234", "1 Day Ago": "70", "2 Days Ago": "70", "Net Change": "1,234", "Summary / Action": "bought net", "Bias": "🟢 bullish"},
        {"Participant Group": "FII", "Instrument": "Index Calls", "Today": "31,092", "1 Day Ago": "45,156", "2 Days Ago": "-37,490", "Net Change": "159,906", "Summary / Action": "bought net", "Bias": "🟢 bullish"},
        {"Participant Group": "FII", "Instrument": "Index Puts", "Today": "-32,608", "1 Day Ago": "135,315", "2 Days Ago": "124,094", "Net Change": "-32,608", "Summary / Action": "bought net", "Bias": "🔴 bearish"},

        {"Participant Group": "Pros", "Instrument": "Stock Futures", "Today": "2,019", "1 Day Ago": "168,384", "2 Days Ago": "24,774", "Net Change": "2,019", "Summary / Action": "bought net", "Bias": "🟢 bullish"},
        {"Participant Group": "Pros", "Instrument": "Index Futures", "Today": "1,368", "1 Day Ago": "228,577", "2 Days Ago": "226,335", "Net Change": "1,368", "Summary / Action": "bought net", "Bias": "🟢 bullish"},
        {"Participant Group": "Pros", "Instrument": "Index Calls", "Today": "159,906", "1 Day Ago": "64,753", "2 Days Ago": "27,207", "Net Change": "159,906", "Summary / Action": "bought net", "Bias": "🟢 bullish"},
        {"Participant Group": "Pros", "Instrument": "Index Puts", "Today": "2,242", "1 Day Ago": "57,325", "2 Days Ago": "65,365", "Net Change": "2,242", "Summary / Action": "bought net", "Bias": "🔴 bearish"},

        {"Participant Group": "DIIs", "Instrument": "Stock Futures", "Today": "-25,949", "1 Day Ago": "3,965,038", "2 Days Ago": "2,189,552", "Net Change": "-25,949", "Summary / Action": "sold net", "Bias": "🔴 bearish"},
        {"Participant Group": "DIIs", "Instrument": "Index Futures", "Today": "-46", "1 Day Ago": "1,306,016", "2 Days Ago": "2,179,216", "Net Change": "-46", "Summary / Action": "sold net", "Bias": "🔴 bearish"}
    ]
    
    st.dataframe(pd.DataFrame(excel_sheet_data), use_container_width=True)

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
    fig_inst = px.bar(pd.DataFrame(inst_records), x="Date", y="Net Sentiment", color="Client Type", barmode="group", title="3-Day Participant Net Sentiment Flow Analysis")
    fig_inst.update_layout(template=plotly_template, height=260, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig_inst, use_container_width=True)

with t4:
    st.info("NIFTY Spot: 24,850 | INDIA VIX: 13.85 | Bias: Bullish Support at 24,800")
    s_list = [24850 + (i * 100) for i in range(-4, 5)]
    oc_data = [{"Strike": s, "Call OI": max(1500, int((500 - (s - 24850)) * 200)), "Put OI": max(1500, int((500 + (s - 24850)) * 250))} for s in s_list]
    df_oc = pd.DataFrame(oc_data)
    fig_o = go.Figure()
    fig_o.add_trace(go.Bar(x=df_oc["Strike"], y=df_oc["Call OI"], name="Call OI", marker_color="#f43f5e"))
    fig_o.add_trace(go.Bar(x=df_oc["Strike"], y=df_oc["Put OI"], name="Put OI", marker_color="#10b981"))
    fig_o.update_layout(barmode="group", height=240, template=plotly_template)
    st.plotly_chart(fig_o, use_container_width=True)


with t5:
    st.markdown("<b>🛡️ AI & Custom Trading Rules Editor & Automated Auditor</b>", unsafe_allow_html=True)
    st.write("સાઇડબારમાં તમે તમારી કેપિટલ, રિસ્ક ટકાવારી અને ડેઇલી ટ્રેડ લિમિટ સેટ કરી શકો છો.")
    
    saved_rules = get_db_val("custom_trading_rules")
    if saved_rules:
        default_rules_text = saved_rules
    else:
        default_rules_text = "1. Never take a revenge trade after a loss.\n2. Always respect predefined Stop Loss.\n3. Wait patiently for liquidity sweeps/Order blocks.\n4. Stop trading for the day after hitting Daily Max Loss."
    
    edited_rules = st.text_area("Edit Your Rules (Line by Line):", value=default_rules_text, height=180)
    
    if st.button("Save & Update Rules"):
        set_db_val("custom_trading_rules", edited_rules)
        st.success("તમારા નિયમો સફળતાપૂર્વક અપડેટ અને સેવ થઈ ગયા છે!")

