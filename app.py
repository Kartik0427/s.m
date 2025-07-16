import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="NSE vs BSE Arbitrage Dashboard",
    page_icon="✅",
    layout="wide",
)

# --- NEW: Alpha Vantage Data Fetching Function ---
@st.cache_data(ttl=60) # Cache for 1 minute
def get_live_price_av(symbol, api_key):
    """Fetches the latest price from Alpha Vantage."""
    if not api_key:
        return None
        
    base_url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": api_key,
    }
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        
        # Check if the 'Global Quote' key exists and is not empty
        if 'Global Quote' in data and data['Global Quote']:
            price_str = data.get('Global Quote', {}).get('05. price')
            return float(price_str) if price_str else None
        # Handle API limit message
        elif 'Note' in data:
            st.sidebar.warning("API call limit may have been reached.", icon="⚠️")
            return None
        else:
            return None
    except Exception:
        return None

# --- Data Loading (Unchanged) ---
@st.cache_data(ttl=600)
def get_stock_list():
    try:
        df = pd.read_csv("bse_nse_mapping.csv")
        return df
    except FileNotFoundError:
        st.error("Error: `bse_nse_mapping.csv` not found.")
        return None

def highlight_alerts(row, threshold):
    if isinstance(row['Difference (%)'], (int, float)) and abs(row['Difference (%)']) > threshold:
        return ['background-color: #8B0000; color: white'] * len(row)
    return [''] * len(row)

# --- Main Application Logic ---
st.title("✅ NSE vs. BSE Arbitrage Dashboard")
st.caption(f"Data from Alpha Vantage. Last refreshed: {datetime.now().strftime('%I:%M:%S %p')}")

stock_df = get_stock_list()

if stock_df is not None:
    # --- UI Controls ---
    st.sidebar.header("Dashboard Controls")
    
    # --- NEW: API Key Input ---
    api_key = st.sidebar.text_input("Enter Your Alpha Vantage API Key", type="password")

    alert_threshold = st.sidebar.number_input("Alert Threshold (%)", 0.0, 10.0, 0.2, 0.1)
    refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 15, 60, 20, help="Note: The free API has a limit of 25 requests per day.")
    num_stocks = st.sidebar.slider("Number of Stocks to Display", 1, 5, 5) # Reduced max to respect API limits

    placeholder = st.empty()

    while True:
        if not api_key:
            st.warning("Please enter your Alpha Vantage API key in the sidebar to fetch data.")
            break

        subset_df = stock_df.head(num_stocks)
        results = []
        
        progress_bar = st.progress(0, text="Initializing...")
        
        for i, (index, row) in enumerate(subset_df.iterrows()):
            progress_text = f"Fetching {row['nseSymbol']}..."
            progress_bar.progress((i + 1) / num_stocks, text=progress_text)
            
            # --- UPDATED: Use Alpha Vantage tickers ---
            # For Alpha Vantage, use .BSE instead of .BO
            nse_ticker = str(row['nseSymbol']) + ".NSE"
            bse_ticker = str(row['bseScripCode']) + ".BSE"
            
            nse_price = get_live_price_av(nse_ticker, api_key)
            # Add a small delay between API calls to be safe
            time.sleep(1) 
            bse_price = get_live_price_av(bse_ticker, api_key)
            
            difference, percentage_diff = None, None
            if nse_price is not None and bse_price is not None:
                difference = nse_price - bse_price
                percentage_diff = (difference / nse_price) * 100 if nse_price != 0 else 0
            
            results.append({
                "Company Name": row['companyName'],
                "NSE Price (₹)": nse_price,
                "BSE Price (₹)": bse_price,
                "Difference (₹)": difference,
                "Difference (%)": percentage_diff,
            })
            time.sleep(1)

        progress_bar.empty()
        results_df = pd.DataFrame(results)

        with placeholder.container():
            st.header("Live Price Comparison Table")
            if not results_df.empty:
                styled_df = results_df.style.apply(highlight_alerts, threshold=alert_threshold, axis=1).format({
                    "NSE Price (₹)": lambda x: f"₹{x:.2f}" if pd.notna(x) else "N/A",
                    "BSE Price (₹)": lambda x: f"₹{x:.2f}" if pd.notna(x) else "N/A",
                    "Difference (₹)": lambda x: f"{x:+.2f}" if pd.notna(x) else "N/A",
                    "Difference (%)": lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A",
                })
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
            else:
                st.warning("Could not fetch data. Check your API key or wait if you have hit the daily limit.")

        time.sleep(refresh_rate)