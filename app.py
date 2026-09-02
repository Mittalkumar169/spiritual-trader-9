
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
# 🚀 SPIRITUAL TRADER PRO - ULTIMATE UNIFIED TERMINAL & AUTO-JOURNAL
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
# 🎨 OBSIDIAN SLATE & NEON CSS
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #111827 !important; border-right: 1px solid #1f2937; }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8));
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 14px;
        border-radius: 12px;
        box-shadow: 0 4px 15px -2px rgba(0, 0, 0, 0.5);
    }
    div[data-testid="stMetricLabel"] p { font-size: 12px !important; font-weight: 600; text-transform: uppercase; color: #94a3b8 !important; }
    div[data-testid="stMetricValue"] div { font-size: 22px !important; font-weight: 700; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 42px; border-radius: 8px; color: #94a3b8; background-color: #161f30;
        border: 1px solid #1f2937; font-weight: 600; padding: 0 16px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
        color: #ffffff !important; border: 1px solid #60a5fa !important;
    }
    input, select, textarea { background-color: #1e293b !important; color: #f8fafc !important; border: 1px solid #334155 !important; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 🗄️ SQLITE DATABASE ENGINE (AUTO-SYNCING)
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
# 🏦 1. INSTITUTIONAL PARTICIPANT DATA (FII / PRO / CLIENT - LAST 3 DAYS)
# ------------------------------------------------------------------------------
@st.cache_data(ttl=1800)
def fetch_participant_data(date_obj):
    d_str = date_obj.strftime("%d%m%Y")
    url = f"https://archives.nseindia.com/content/nsccl/fao_participant_oi_{d_str}.csv"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code == 200 and "Client Type" in resp.text:
            df_raw = pd.read_csv(io.StringIO(resp.text), skiprows=1)
            df_raw.columns = [c.strip() for c in df_raw.columns]
            participants = ["Client", "DII", "FII", "Pro"]
            filtered = df_raw[df_raw["Client Type"].isin(participants)].copy()
            cols = [
                "Future Index Long", "Future Index Short",
                "Option Index Call Long", "Option Index Put Long",
                "Option Index Call Short", "Option Index Put Short"
            ]
            for c in cols:
                if c in filtered.columns:
                    filtered[c] = pd.to_numeric(filtered[c], errors='coerce').fillna(0)
            
            filtered["Net Future"] = filtered["Future Index Long"] - filtered["Future Index Short"]
            filtered["Net Calls"] = filtered["Option Index Call Long"] - filtered["Option Index Call Short"]
            filtered["Net Puts"] = filtered["Option Index Put Long"] - filtered["Option Index Put Short"]
            filtered["Net Sentiment Score"] = filtered["Net Future"] + filtered["Net Calls"] - filtered["Net Puts"]
            filtered["Date"] = date_obj.strftime("%d-%m-%Y")
            return filtered[["Date", "Client Type", "Net Future", "Net Calls", "Net Puts", "Net Sentiment Score"]]
    except Exception:
        return None
    return None

def get_last_3_days_participant_data():
    data_frames = []
    curr = datetime.today()
    attempts = 0
    while len(data_frames) < 3 and attempts < 10:
        if curr.weekday() < 5:
            df_day = fetch_participant_data(curr)
            if df_day is not None and not df_day.empty:
                data_frames.append(df_day)
        curr -= timedelta(days=1)
        attempts += 1
    
    if data_frames:
        return pd.concat(data_frames, ignore_index=True), False
    
    fallback_records = []
    dates = [(datetime.today() - timedelta(days=i)).strftime("%d-%m-%Y") for i in [2, 1, 0]]
    participants = ["Client", "DII", "FII", "Pro"]
    base_scores = {"Client": [-45000, -58000, -72000], "DII": [18000, 22000, 26000],
                   "FII": [64000, 78000, 91000], "Pro": [25000, 31000, 42000]}
    for idx, d in enumerate(dates):
        for p in participants:
            score = base_scores[p][idx]
            fallback_records.append({
                "Date": d, "Client Type": p, "Net Future": score // 2,
                "Net Calls": score // 2, "Net Puts": -score // 4, "Net Sentiment Score": score
            })
    return pd.DataFrame(fallback_records), True

# ------------------------------------------------------------------------------
# 📈 2. LIVE INDIA VIX & OPTION CHAIN WITH VIX RECOMMENDATION
# ------------------------------------------------------------------------------
@st.cache_data(ttl=120)
def fetch_live_vix():
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=5)
        api_url = "https://www.nseindia.com/api/allIndices"
        resp = session.get(api_url, headers=headers, timeout=5)
        if resp.status_code == 200:
            for item in resp.json().get("data", []):
                if item.get("index") == "INDIA VIX":
                    return float(item.get("last")), float(item.get("percentChange", 0.0))
    except Exception:
        pass
    return 13.45, 1.2

@st.cache_data(ttl=120)
def fetch_option_chain(symbol="NIFTY"):
    session = requests.Session()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=5)
        api_url = f"https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
        resp = session.get(api_url, headers=headers, timeout=5)
        if resp.status_code == 200:
            return resp.json(), False
    except Exception:
        pass
    
    simulated_spot = 24850.0 if symbol == "NIFTY" else 52300.0
    simulated_data = {"records": {"underlyingValue": simulated_spot, "expiryDates": ["10-Sep-2026", "17-Sep-2026"], "data": []}}
    for s in [simulated_spot + (i * 100) for i in range(-8, 9)]:
        simulated_data["records"]["data"].append({
            "strikePrice": s, "expiryDate": "10-Sep-2026",
            "CE": {"openInterest": max(1000, int((s - simulated_spot + 600) * 120)), "changeinOpenInterest": int((s - simulated_spot) * 8), "lastPrice": max(10.0, 300 - abs(s - simulated_spot))},
            "PE": {"openInterest": max(1000, int((simulated_spot - s + 600) * 150)), "changeinOpenInterest": int((simulated_spot - s + 100) * 12), "lastPrice": max(10.0, 300 - abs(s - simulated_spot))}
        })
    return simulated_data, True

def analyze_15m_oi_trend(oc_df, spot_price):
    oc_df["atm_diff"] = (oc_df["Strike"] - spot_price).abs()
    near_atm = oc_df.sort_values("atm_diff").head(5)
    call_chg_oi = near_atm["CE_Change_OI"].sum()
    put_chg_oi = near_atm["PE_Change_OI"].sum()

    if put_chg_oi > call_chg_oi * 1.3:
        return "UPTREND (તેજી)", "#10b981", "🟢 **STRONG UPTREND:** 15 મિનિટમાં Put Writers (Bulls) સક્રિય છે. Support પાસે Buy Setup શોધો.", int(call_chg_oi), int(put_chg_oi)
    elif call_chg_oi > put_chg_oi * 1.3:
        return "DOWNTREND (મંદી)", "#f43f5e", "🔴 **STRONG DOWNTREND:** 15 મિનિટમાં Call Writers (Bears) ભારે દબાણ કરી રહ્યા છે. Resistance પાસે Sell Setup શોધો.", int(call_chg_oi), int(put_chg_oi)
    else:
        return "SIDEWAYS (રેન્જબાઉન્ડ)", "#f59e0b", "🟡 **SIDEWAYS / CHOP:** બંને બાજુ સરખો OI ઉમેરાઈ રહ્યો છે. બ્રેકઆઉટની રાહ જુઓ.", int(call_chg_oi), int(put_chg_oi)

def evaluate_premium_by_vix(strike, spot_price, vix_value):
    diff = strike - spot_price
    if abs(diff) <= 50:
        return "⭐ BEST BUY (ATM)", "⭐ BEST BUY (ATM)"
    elif -150 <= diff < -50:
        return "🟢 BEST (High Delta ITM)", ("🔴 AVOID (Theta Decay OTM)" if vix_value < 13.0 else "🟡 MODERATE (Scalp only)")
    elif 50 < diff <= 150:
        return ("🔴 AVOID (Theta Decay OTM)" if vix_value < 13.0 else "🟡 MODERATE (Scalp only)"), "🟢 BEST (High Delta ITM)"
    elif diff < -150:
        return "🟢 SAFE (Deep ITM)", "❌ DANGEROUS (Far OTM Trap)"
    else:
        return "❌ DANGEROUS (Far OTM Trap)", "🟢 SAFE (Deep ITM)"

# ------------------------------------------------------------------------------
# 💻 UI HEADER
# ------------------------------------------------------------------------------
st.markdown("""
<div style="display: flex; align-items: center; gap: 14px; margin-bottom: 18px;">
    <div style="background: linear-gradient(135deg, #10b981, #06b6d4); padding: 10px; border-radius: 12px;">
        <span style="font-size: 24px;">⚡</span>
    </div>
    <div>
        <h2 style="margin: 0; font-size: 22px; color: #f8fafc;">SPIRITUAL TRADER TERMINAL</h2>
        <p style="margin: 0; color: #94a3b8; font-size: 13px;">Auto-Journaling • Risk Shield • 15m Trend • India VIX Edge • AI Chat</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 🛡️ SIDEBAR: CAPITAL SETTINGS, RISK SHIELD & LOGGING
# ------------------------------------------------------------------------------
st.sidebar.markdown("<h3 style='color:#38bdf8;'>🛡️ કેપિટલ & રિસ્ક શીલ્ડ</h3>", unsafe_allow_html=True)
user_capital = st.sidebar.number_input("તમારી કુલ મૂડી (Capital ₹)", min_value=10000.0, value=100000.0, step=5000.0)
risk_per_trade_pct = st.sidebar.slider("પ્રતિ ટ્રેડ રિસ્ક (%)", min_value=0.5, max_value=3.0, value=1.5, step=0.25)
daily_max_loss = st.sidebar.number_input("ડેઇલી મેક્સ લોસ લિમિટ (₹)", min_value=1000.0, value=4000.0, step=500.0)

max_risk_rupees = (user_capital * risk_per_trade_pct) / 100.0

conn = sqlite3.connect("journal.db")
today_str = datetime.today().strftime("%Y-%m-%d")
c_cur = conn.cursor()
c_cur.execute("SELECT SUM(pnl) FROM trades WHERE trade_date = ?", (today_str,))
res_pnl = c_cur.fetchone()[0]
today_pnl = res_pnl if res_pnl is not None else 0.0
conn.close()

is_daily_loss_hit = today_pnl <= -abs(daily_max_loss)
if is_daily_loss_hit:
    st.sidebar.error(f"🛑 **આજનો મેક્સ લોસ પૂરો થઈ ગયો છે!**\n\nઆજનો P&L: ₹{today_pnl:,.2f} / લિમિટ: -₹{daily_max_loss:,.2f}\n\nઓવરટ્રેડિંગ રોકવા નવો ટ્રેડ લેવો બ્લોક કર્યો છે.")

st.sidebar.markdown("---")
st.sidebar.markdown("<h3 style='color:#38bdf8;'>➕ ટ્રેડ એન્ટ્રી & ઓર્ડર પેનલ</h3>", unsafe_allow_html=True)

with st.sidebar.form("trade_form", clear_on_submit=True):
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        trade_date = st.date_input("તારીખ", datetime.today())
        timeframe = st.selectbox("Timeframe", ["1m", "3m", "5m", "15m", "1H"])
    with col_f2:
        session = st.selectbox("Session", ["Morning (9:15-11:30)", "Mid-Day (11:30-1:30)", "Afternoon (1:30-3:30)"])
        symbol = st.text_input("Symbol", placeholder="NIFTY 24850 CE").upper().strip()

    trade_type = st.selectbox("Position Type", ["BUY (Long)", "SELL (Short)"])

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        entry_price = st.number_input("Entry Price (₹)", min_value=0.0, format="%.2f")
        stop_loss = st.number_input("Stop Loss (₹)", min_value=0.0, format="%.2f")
    with col_p2:
        exit_price = st.number_input("Exit Price (₹)", min_value=0.0, format="%.2f")
        target_price = st.number_input("Target Price (₹)", min_value=0.0, format="%.2f")

    sl_points = abs(entry_price - stop_loss) if (entry_price > 0 and stop_loss > 0) else 1.0
    rec_qty = int(max_risk_rupees // sl_points) if sl_points > 0 else 0
    rec_lots = max(1, rec_qty // 25)
    rec_qty_rounded = rec_lots * 25

    st.markdown(f"""
    <div style="background:#161f30; padding:10px; border-radius:8px; border:1px solid #334155; margin-bottom:10px;">
        <div style="color:#94a3b8; font-size:11px; font-weight:bold;">🛡️ ઓટો-કેલ્ક્યુલેટેડ ક્વાન્ટિટી (Risk: ₹{max_risk_rupees:,.0f})</div>
        <div style="color:#10b981; font-size:15px; font-weight:bold;">👉 {rec_lots} Lots ({rec_qty_rounded} Qty)</div>
        <div style="color:#cbd5e1; font-size:11px;">SL Points: {sl_points:.2f} | જો SL હિટ થશે: -₹{sl_points * rec_qty_rounded:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

    quantity = st.number_input("Lots / Quantity", min_value=1, value=int(rec_qty_rounded if rec_qty_rounded > 0 else 25), step=25)

    setup_type = st.selectbox("Setup / Logic", [
        "Order Block (OB)", "Fair Value Gap (FVG)", "Liquidity Sweep",
        "Support / Resistance Rejection", "Trendline Breakout / Retest", "Other"
    ])

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        entry_emotion = st.selectbox("Entry Emotion", ["Calm & Disciplined", "FOMO", "Revenge Trading", "Boredom Entry"])
        rule_followed = st.selectbox("Rules Followed?", ["Yes (100%)", "Partial", "No (Violated)"])
    with col_s2:
        exit_reason = st.selectbox("Exit Reason", ["Target Hit", "SL Hit", "Trailing SL", "Early / Panic Exit"])
        trade_grade = st.selectbox("Trade Grade", ["A+", "A", "B", "C (Bad Execution)"])

    setup_notes = st.text_area("વિગતવાર નોંધ (Mistakes / Lessons Learned)")
    uploaded_image = st.file_uploader("ચાર્ટ સ્ક્રીનશોટ", type=["png", "jpg", "jpeg"])

    submitted = st.form_submit_button("💾 ટ્રેડ રેકોર્ડ કરો", disabled=is_daily_loss_hit)

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
        st.sidebar.success("✅ ટ્રેડ સફળતાપૂર્વક લોગ થયો!")
        st.rerun()

# ------------------------------------------------------------------------------
# 📑 NAVIGATION TABS
# ------------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Comprehensive Journal",
    "🏦 Institutional Smart Money Flow",
    "🔥 Live Option Chain & VIX Radar",
    "⚡ 1-Click Broker Auto-Execution",
    "🤖 In-App AI Assistant (Chat)"
])

# ==============================================================================
# 📊 TAB 1: COMPREHENSIVE JOURNAL & TIMING ANALYSIS
# ==============================================================================
with tab1:
    conn = sqlite3.connect("journal.db")
    df = pd.read_sql_query("SELECT * FROM trades ORDER BY trade_date ASC, id ASC", conn)
    conn.close()

    if not df.empty:
        df["trade_date"] = pd.to_datetime(df["trade_date"])

        st.sidebar.markdown("---")
        st.sidebar.markdown("<h3 style='color:#a78bfa;'>🔍 એડવાન્સ્ડ ફિલ્ટર્સ</h3>", unsafe_allow_html=True)
        f_setup = st.sidebar.multiselect("Setup ફિલ્ટર:", options=df["setup_type"].unique(), default=df["setup_type"].unique())
        f_grade = st.sidebar.multiselect("Grade ફિલ્ટર:", options=df["trade_grade"].unique(), default=df["trade_grade"].unique())

        filtered_df = df[(df["setup_type"].isin(f_setup)) & (df["trade_grade"].isin(f_grade))]

        total_trades = len(filtered_df)
        total_pnl = filtered_df["pnl"].sum()
        win_trades = len(filtered_df[filtered_df["pnl"] > 0])
        win_rate = (win_trades / total_trades) * 100 if total_trades > 0 else 0
        avg_rr = filtered_df["risk_reward"].mean() if "risk_reward" in filtered_df else 0.0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("કુલ ટ્રેડ્સ", f"{total_trades}")
        c2.metric("કુલ P&L (₹)", f"₹{total_pnl:,.2f}", delta=f"{total_pnl:,.2f}")
        c3.metric("Win Rate", f"{win_rate:.1f}%")
        c4.metric("સરેરાશ R:R", f"1:{avg_rr:.1f}")
        c5.metric("Profit Trades", f"{win_trades} / {total_trades}")

        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("⏱️ Session Timing Edge (કયા સમયે ટ્રેડ કરવો સૌથી ફાયદાકારક છે?)")
        sessions = ["Morning (9:15-11:30)", "Mid-Day (11:30-1:30)", "Afternoon (1:30-3:30)"]
        session_stats = []
        for s in sessions:
            prefix = s.split(" ")[0]
            s_df = filtered_df[filtered_df["session"].st
