import streamlit as st
import pandas as pd
from SmartApi import SmartConnect
import time
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Angel One - Debug Dashboard",
    page_icon="🐞",
    layout="wide",
)

# --- Helper Functions ---
@st.cache_data(ttl=3600)
def load_instrument_list():
    try:
        return pd.read_csv("instrument_list.csv")
    except FileNotFoundError:
        st.error("Error: `instrument_list.csv` not found. Please run `generate_instrument_list.py` first.", icon="🔥")
        return None

def get_token(instrument_df, symbol, exchange):
    if instrument_df is None: return None
    res = instrument_df[(instrument_df['api_symbol'] == symbol) & (instrument_df['exch_seg'] == exchange)]
    return res.iloc[0]['token'] if not res.empty else None

# --- Main Application Logic ---
st.title("🐞 Angel One - Debug Dashboard")

# --- User Authentication ---
st.sidebar.header("Angel One Login")
# Use st.session_state to preserve input values after reruns
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
    # Load mapping files
    instrument_df = load_instrument_list()
    stock_df = pd.read_csv("bse_nse_mapping.csv")

    st.sidebar.header("Dashboard Controls")
    num_stocks = st.sidebar.slider("Number of Stocks to Display", 1, len(stock_df), 3)

    st.header("Live Price Comparison Table")
    placeholder = st.empty()
    
    st.header("🐞 Debugging Log")
    log_placeholder = st.container()

    while True:
        subset_df = stock_df.head(num_stocks)
        results = []

        with log_placeholder:
            st.write("---")
            st.write(f"**Cycle Start: {datetime.now().strftime('%I:%M:%S %p')}**")

            for _, row in subset_df.iterrows():
                nse_symbol = row['nseSymbol']
                bse_code = str(row['bseScripCode'])
                
                nse_token = get_token(instrument_df, nse_symbol, 'NSE')
                bse_token = get_token(instrument_df, bse_code, 'BSE')
                
                st.write(f"Processing {row['companyName']}: NSE Symbol='{nse_symbol}', BSE Code='{bse_code}'")
                st.write(f"Found Tokens -> NSE: `{nse_token}`, BSE: `{bse_token}`")

                nse_price, bse_price = None, None
                
                # Fetch NSE Price
                if nse_token:
                    try:
                        ltp_data = st.session_state.smart_api_obj.ltpData("NSE", nse_symbol, str(nse_token))
                        if ltp_data.get('status') == True:
                            nse_price = ltp_data.get('data', {}).get('ltp')
                        else:
                            st.error(f"NSE API Error for {nse_symbol}:")
                            st.json(ltp_data) # Print the full error response
                    except Exception as e:
                        st.error(f"NSE Exception for {nse_symbol}: {e}")

                # Fetch BSE Price
                if bse_token:
                    try:
                        ltp_data = st.session_state.smart_api_obj.ltpData("BSE", bse_code, str(bse_token))
                        if ltp_data.get('status') == True:
                            bse_price = ltp_data.get('data', {}).get('ltp')
                        else:
                            st.error(f"BSE API Error for {bse_code}:")
                            st.json(ltp_data)
                    except Exception as e:
                        st.error(f"BSE Exception for {bse_code}: {e}")

                results.append({
                    "Company Name": row['companyName'], "NSE Price (₹)": nse_price, "BSE Price (₹)": bse_price,
                })

        # --- Display Results ---
        results_df = pd.DataFrame(results)
        placeholder.dataframe(results_df, use_container_width=True, hide_index=True)
        time.sleep(15) # Use a longer refresh for debugging