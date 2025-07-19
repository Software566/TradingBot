import streamlit as st
from SmartApi.smartConnect import SmartConnect
import pyotp
import pandas as pd
from ta.trend import SMAIndicator
import datetime

# ========== Streamlit UI ==========
st.set_page_config(page_title="AngelOne Algo Bot", layout="wide")
st.title("📈 AngelOne Algo Trading Bot")

# ========== 1. Login ==========
st.sidebar.subheader("🔐 API Login Details")
api_key = st.sidebar.text_input("API Key", value="ou9Ytz6G")
client_code = st.sidebar.text_input("Client Code", value="A437010")
mpin = st.sidebar.text_input("MPIN", value="2580", type="password")
totp_key = st.sidebar.text_input("TOTP Key", value="DKIKHBKHV2NLRHXVJJCMHL4AUA")

login_button = st.sidebar.button("Login")

obj = None
userProfile = None

if login_button:
    try:
        obj = SmartConnect(api_key=api_key)
        token = pyotp.TOTP(totp_key).now()
        data = obj.generateSession(client_code, mpin, token)
        refreshToken = data['data']['refreshToken']
        userProfile = obj.getProfile(refreshToken)
        st.sidebar.success("Login successful")
        st.sidebar.write(userProfile)
        st.session_state['obj'] = obj
        st.session_state['refreshToken'] = refreshToken
    except Exception as e:
        st.sidebar.error(f"Login Failed: {e}")

# ========== 2. Fetch & Analyze ==========
symbol = "NIFTY 50"
exchange = "NSE"
token = "2885"

def fetch_data():
    to_date = datetime.datetime.now()
    from_date = to_date - datetime.timedelta(days=10)
    historicParam = {
        "exchange": exchange,
        "symboltoken": token,
        "interval": "FIVE_MINUTE",
        "fromdate": from_date.strftime('%Y-%m-%d %H:%M'),
        "todate": to_date.strftime('%Y-%m-%d %H:%M')
    }
    data = st.session_state['obj'].getCandleData(historicParam)
    df = pd.DataFrame(data['data'], columns=["timestamp", "open", "high", "low", "close", "volume"])
    df['close'] = df['close'].astype(float)
    return df

def generate_signal(df):
    df['SMA_20'] = SMAIndicator(df['close'], 5).sma_indicator()
    df['SMA_5'] = SMAIndicator(df['close'], 20).sma_indicator()
    if df['SMA_5'].iloc[-2] < df['SMA_20'].iloc[-2] and df['SMA_5'].iloc[-1] > df['SMA_20'].iloc[-1]:
        return "buy"
    elif df['SMA_5'].iloc[-2] > df['SMA_20'].iloc[-2] and df['SMA_5'].iloc[-1] < df['SMA_20'].iloc[-1]:
        return "sell"
    return "hold"

def place_order(signal):
    order_type = "BUY" if signal == "buy" else "SELL"
    if signal in ["buy", "sell"]:
        order = st.session_state['obj'].placeOrder({
            "variety": "NORMAL",
            "tradingsymbol": symbol,
            "symboltoken": token,
            "transactiontype": order_type,
            "exchange": exchange,
            "ordertype": " Indian MARKET",
            "producttype": "INTRADAY",
            "duration": "DAY",
            "quantity": 1
        })
        return order
    return "No order placed."

# ========== 3. Execute Bot ==========
if st.sidebar.button("Run Bot"):
    if 'obj' not in st.session_state:
        st.error("Please login first.")
    else:
        try:
            df = fetch_data()
            st.subheader("📊 Nifty-50 Data")
            st.dataframe(df.tail(10))

            signal = generate_signal(df)
            st.success(f"📌 Signal: {signal.upper()}")

            result = place_order(signal)
            st.info(f"📝 Order Result: {result}")
        except Exception as e:
            st.error(f"❌ Error: {e}")