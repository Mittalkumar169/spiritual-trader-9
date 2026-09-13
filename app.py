
import streamlit as st
import pandas as pd
import requests
import pyotp
from fyers_apiv3 import fyersModel

st.set_page_config(page_title="Auto Trading Journal", layout="wide")
st.title("📊 Smart Trading Journal & Performance Analytics")

# --- साइडबार: केवल 1 बार भरने के लिए क्रेडेंशियल्स ---
st.sidebar.header("🔐 FYERS ऑटोमेशन क्रेडेंशियल्स")
fy_id = st.sidebar.text_input("FYERS Client ID", value="XM22563")
fy_pin = st.sidebar.text_input("FYERS PIN (4-अंक)", type="password")
app_id = st.sidebar.text_input("App ID (जैसे XM22563-100)")
secret_key = st.sidebar.text_input("Secret Key", type="password")
totp_key = st.sidebar.text_input("TOTP Secret Key (32-अंक)", type="password")

st.sidebar.caption("🔒 यह क्रेडेंशियल्स सीधे FYERS सर्वर से जुड़ती हैं और कहीं स्टोर नहीं होतीं।")

# --- ऑटोमैटिक टोकन जनरेशन फंक्शन (बिना ऑथ कोड या रीडायरेक्ट के) ---
def get_automated_token(client_id, pin, app_id, secret, totp_secret):
    session = requests.Session()
    
    # 1. TOTP की मदद से ऑटोमैटिक OTP भेजना
    send_otp_url = "https://api-t1.fyers.in/api/v3/generate-authcode"
    otp = pyotp.TOTP(totp_secret).now()
    payload = {
        "fy_id": client_id,
        "password": pin,
        "app_id": "2",
        "otp": otp
    }
    
    res = session.post(send_otp_url, json=payload).json()
    if res.get("s") != "ok":
        raise Exception(f"लॉगिन OTP विफल: {res.get('message', 'अमान्य क्रेडेंशियल्स')}")
    
    request_key = res.get("request_key")
    
    # 2. पिन वेरिफाई करके ऑटोमैटिक auth_code प्राप्त करना
    verify_pin_url = "https://api-t1.fyers.in/api/v3/validate-pin"
    pin_payload = {
        "request_key": request_key,
        "identity_type": "pin",
        "identifier": pin
    }
    
    pin_res = session.post(verify_pin_url, json=pin_payload).json()
    if pin_res.get("s") != "ok":
        raise Exception(f"पिन सत्यापन विफल: {pin_res.get('message', 'गलत पिन')}")
        
    auth_code = pin_res.get("data", {}).get("auth_code")
    
    # 3. बिना किसी रीडायरेक्ट के फाइनल एक्सेस टोकन प्राप्त करना
    app_session = fyersModel.SessionModel(
        client_id=app_id,
        secret_key=secret,
        grant_type="authorization_code",
        response_type="code"
    )
    app_session.set_token(auth_code)
    token_response = app_session.generate_token()
    return token_response["access_token"]

# --- मुख्य स्क्रीन: ऑटो-सिंक बटन ---
if st.button("⚡ एक क्लिक में आज के ट्रेड्स फेच और एनालाइज़ करें"):
    if not (fy_id and fy_pin and app_id and secret_key and totp_key):
        st.warning("⚠️ कृपया साइडबार में अपने सभी 5 क्रेडेंशियल्स भरें।")
    else:
        with st.spinner("FYERS सर्वर से सीधे कनेक्ट होकर ट्रेड्स लाए जा रहे हैं..."):
            try:
                # ऑटो टोकन निकालें
                access_token = get_automated_token(fy_id, fy_pin, app_id, secret_key, totp_key)
                fyers = fyersModel.FyersModel(client_id=app_id, token=access_token, log_path="")
                
                # ट्रेड्स फेच करें
                trades_data = fyers.tradebook()
                
                if trades_data.get("tradeBook"):
                    df = pd.DataFrame(trades_data["tradeBook"])
                    
                    # सिंबल, साइड, क्वांटिटी और भाव अलग करें
                    df['side_name'] = df['side'].apply(lambda x: "BUY" if x == 1 else "SELL")
                    display_cols = ['symbol', 'side_name', 'tradedQty', 'tradePrice', 'orderDateTime']
                    df_display = df[display_cols].copy()
                    
                    total_trades = len(df_display)
                    
                    # एनालिटिक्स कार्ड्स
                    col1, col2, col3 = st.columns(3)
                    col1.metric("कुल ट्रेड्स", total_trades)
                    col2.metric("दैनिक लिमिट", "3 ट्रेड्स", 
                                delta=f"{3 - total_trades} बाकी" if total_trades <= 3 else "⚠️ ओवरट्रेडिंग (नियम टूटा)",
                                delta_color="normal" if total_trades <= 3 else "inverse")
                    col3.metric("सिस्टम स्टेटस", "✅ लाइव कनेक्टेड")

                    st.markdown("### 📋 आज के निष्पादित (Executed) ट्रेड्स")
                    st.dataframe(df_display, use_container_width=True)
                    
                else:
                    st.info("ℹ️ आज आपके डीमैट खाते में कोई नया ट्रेड नहीं हुआ है।")
                    
            except Exception as e:
                st.error(f"❌ त्रुटि: {str(e)}")
