import streamlit as st
import pandas as pd
from SmartApi import SmartConnect
import time
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="NSE vs. BSE Price Dashboard",
    page_icon="⚡",
    layout="wide",
)

# --- Helper Functions ---
@st.cache_data(ttl=3600)
def load_instrument_list():
    try:
        return pd.read_csv("instrument_list.csv", dtype={'api_symbol': str})
    except FileNotFoundError:
        st.error("Error: `instrument_list.csv` not found. Please run `generate_instrument_list.py` script.", icon="🔥")
        return None

def get_token(instrument_df, symbol, exchange):
    if instrument_df is None: return None
    res = instrument_df[
        (instrument_df['api_symbol'] == str(symbol)) & 
        (instrument_df['exch_seg'] == exchange)
    ]
    return res.iloc[0]['token'] if not res.empty else None

# --- Main Application Logic ---
st.title("⚡ NSE vs. BSE Real-Time Price Dashboard")

# --- User Authentication ---
st.sidebar.header("Angel One Login")
# ... (The login section remains the same as the last working version)
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

    # --- NEW: Custom Filter and Sort Controls ---
    st.sidebar.subheader("Filters & Sorting")
    
    min_diff_filter = st.sidebar.number_input(
        "Minimum Absolute Difference (%)", 
        min_value=0.00, 
        max_value=5.0, 
        value=0.05, 
        step=0.01,
        help="Only show stocks where the percentage price gap is greater than this value."
    )

    sort_by = st.sidebar.selectbox(
        "Sort Table By",
        ["Default", "Biggest Difference (%)", "Biggest Difference (₹)"],
        help="Sort the table to see the largest opportunities at the top."
    )
    
    placeholder = st.empty()

    while True:
        subset_df = stock_df.head(num_stocks)
        results = []

        for _, row in subset_df.iterrows():
            # Data fetching logic remains the same...
            nse_symbol = row['nseSymbol']
            bse_code = str(row['bseScripCode'])
            nse_token = get_token(instrument_df, nse_symbol, 'NSE')
            bse_token = get_token(instrument_df, nse_symbol, 'BSE')
            nse_price, bse_price = None, None
            
            if nse_token:
                try:
                    ltp_data = st.session_state.smart_api_obj.ltpData("NSE", nse_symbol, str(nse_token))
                    if ltp_data.get('status'): nse_price = ltp_data.get('data', {}).get('ltp')
                except Exception: pass
            if bse_token:
                try:
                    ltp_data = st.session_state.smart_api_obj.ltpData("BSE", bse_code, str(bse_token))
                    if ltp_data.get('status'): bse_price = ltp_data.get('data', {}).get('ltp')
                except Exception: pass

            difference, percentage_diff = None, None
            if nse_price is not None and bse_price is not None:
                difference = nse_price - bse_price
                percentage_diff = (difference / nse_price) * 100 if nse_price != 0 else 0

            results.append({
                "Company Name": row['companyName'], "NSE Price (₹)": nse_price, "BSE Price (₹)": bse_price,
                "Difference (₹)": difference, "Difference (%)": percentage_diff,
            })

        results_df = pd.DataFrame(results).dropna()

        # --- NEW: Apply Filtering and Sorting ---
        if not results_df.empty:
            # Add an absolute percentage column for filtering and sorting
            results_df['abs_diff_pct'] = results_df['Difference (%)'].abs()
            results_df['abs_diff_rs'] = results_df['Difference (₹)'].abs()

            # Apply the minimum difference filter
            results_df = results_df[results_df['abs_diff_pct'] >= min_diff_filter]

            # Apply sorting based on user selection
            if sort_by == "Biggest Difference (%)":
                results_df = results_df.sort_values(by="abs_diff_pct", ascending=False)
            elif sort_by == "Biggest Difference (₹)":
                results_df = results_df.sort_values(by="abs_diff_rs", ascending=False)
            
            # Drop the helper columns before displaying
            results_df = results_df.drop(columns=['abs_diff_pct', 'abs_diff_rs'])

        with placeholder.container():
            st.header("Live Price Comparison Table")
            
            # --- NEW: Apply Heatmap Styling ---
            st.dataframe(
                results_df.style.background_gradient(
                    cmap='RdYlGn', subset=['Difference (₹)', 'Difference (%)']
                ).format({
                    "NSE Price (₹)": "₹{:,.2f}",
                    "BSE Price (₹)": "₹{:,.2f}",
                    "Difference (₹)": "{:+.2f}",
                    "Difference (%)": "{:+.2f}%",
                }),
                use_container_width=True, 
                hide_index=True
            )
            st.caption(f"Last updated: {datetime.now().strftime('%I:%M:%S %p')}")

        time.sleep(refresh_rate)