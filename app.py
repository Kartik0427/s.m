import streamlit as st
import pandas as pd
from SmartApi import SmartConnect
import time
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="NSE vs. BSE Price Dashboard",
    page_icon="📊",
    layout="wide",
)

# --- Helper Functions ---
@st.cache_data(ttl=3600)
def load_instrument_list():
    """Loads the instrument list from the pre-generated CSV file."""
    try:
        return pd.read_csv("instrument_list.csv", dtype={'api_symbol': str})
    except FileNotFoundError:
        st.error("Error: `instrument_list.csv` not found. Please run `generate_instrument_list.py` script.", icon="🔥")
        return None

def get_token(instrument_df, symbol, exchange):
    """Finds the token for a given symbol and exchange."""
    if instrument_df is None: return None
    res = instrument_df[
        (instrument_df['api_symbol'] == str(symbol)) & 
        (instrument_df['exch_seg'] == exchange)
    ]
    return res.iloc[0]['token'] if not res.empty else None

# --- Main Application Logic ---
st.title("📊 NSE vs. BSE Real-Time Price Dashboard")

# --- User Authentication ---
st.sidebar.header("Angel One Login")
if 'api_key' not in st.session_state: st.session_state.api_key = ''
if 'client_id' not in st.session_state: st.session_state.client_id = ''
if 'password' not in st.session_state: st.session_state.password = ''

st.session_state.api_key = st.sidebar.text_input("API Key", st.session_state.api_key)
st.session_state.client_id = st.sidebar.text_input("Client ID / Username", st.session_state.client_id)
st.session_state.password = st.sidebar.text_input("Password / PIN", st.session_state.password, type="password")
totp = st.sidebar.text_input("TOTP (from Authenticator App)")

if 'smart_api_obj' not in st.session_state:
    st.session_state.smart_api_obj = None

if st.sidebar.button("Login"):
    if st.session_state.api_key and st.session_state.client_id and st.session_state.password and totp:
        with st.spinner("Logging in..."):
            try:
                obj = SmartConnect(api_key=st.session_state.api_key)
                data = obj.generateSession(st.session_state.client_id, st.session_state.password, totp)
                
                if data.get('status') == True:
                    st.session_state.smart_api_obj = obj
                    st.sidebar.success("Login Successful!", icon="✅")
                    st.rerun() 
                else:
                    st.sidebar.error(f"Login Failed: {data.get('message', 'Unknown error')}", icon="❌")
            except Exception as e:
                st.sidebar.error(f"An error occurred: {e}", icon="🔥")
    else:
        st.sidebar.warning("Please fill in all login details.", icon="⚠️")

# --- Main Dashboard ---
if st.session_state.smart_api_obj is None:
    st.info("Please log in using the sidebar to view the dashboard.")
else:
    instrument_df = load_instrument_list()
    stock_df = pd.read_csv("bse_nse_mapping.csv")

    st.sidebar.header("Dashboard Controls")
    refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 5, 60, 10)
    num_stocks = st.sidebar.slider("Number of Stocks to Display", 1, len(stock_df), 10)

    placeholder = st.empty()

    while True:
        subset_df = stock_df.head(num_stocks)
        results = []

        for _, row in subset_df.iterrows():
            nse_symbol = row['nseSymbol']
            bse_code = str(row['bseScripCode'])
            
            # --- Get Tokens ---
            nse_token = get_token(instrument_df, nse_symbol, 'NSE')
            # --- THIS IS THE FIX ---
            # Use the NSE symbol to find the BSE token
            bse_token = get_token(instrument_df, nse_symbol, 'BSE')

            nse_price, bse_price = None, None
            
            # Fetch NSE Price
            if nse_token:
                try:
                    ltp_data = st.session_state.smart_api_obj.ltpData("NSE", nse_symbol, str(nse_token))
                    if ltp_data.get('status'):
                        nse_price = ltp_data.get('data', {}).get('ltp')
                except Exception: pass

            # Fetch BSE Price
            if bse_token:
                try:
                    # The trading symbol for BSE is its Scrip Code
                    ltp_data = st.session_state.smart_api_obj.ltpData("BSE", bse_code, str(bse_token))
                    if ltp_data.get('status'):
                        bse_price = ltp_data.get('data', {}).get('ltp')
                except Exception: pass

            difference, percentage_diff = None, None
            if nse_price is not None and bse_price is not None:
                difference = nse_price - bse_price
                percentage_diff = (difference / nse_price) * 100 if nse_price != 0 else 0

            results.append({
                "Company Name": row['companyName'], "NSE Price (₹)": nse_price, "BSE Price (₹)": bse_price,
                "Difference (₹)": difference, "Difference (%)": percentage_diff,
            })

        results_df = pd.DataFrame(results)

        with placeholder.container():
            st.header("Live Price Comparison Table")
            st.dataframe(
                results_df.style.format({
                    "NSE Price (₹)": "₹{:,.2f}", "BSE Price (₹)": "₹{:,.2f}",
                    "Difference (₹)": "{:+.2f}", "Difference (%)": "{:+.2f}%",
                }, na_rep="N/A"),
                use_container_width=True, hide_index=True
            )
            st.caption(f"Last updated: {datetime.now().strftime('%I:%M:%S %p')}")

        time.sleep(refresh_rate)