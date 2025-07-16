import streamlit as st
import pandas as pd
import yfinance as yf
import time
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="NSE vs BSE Arbitrage Dashboard",
    page_icon="🚨",
    layout="wide",
)

# --- Data Loading (Functions remain the same) ---
@st.cache_data(ttl=600)
def get_stock_list():
    try:
        df = pd.read_csv("bse_nse_mapping.csv")
        return df
    except FileNotFoundError:
        st.error("Error: `bse_nse_mapping.csv` not found. Please ensure the file is in the same directory.")
        return None

@st.cache_data(ttl=60)
def get_live_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        price = stock.info.get('regularMarketPrice')
        if price:
            return price
        return stock.history(period='1d')['Close'].iloc[-1]
    except Exception as e:
        return None

# --- NEW: Function to highlight rows that cross the threshold ---
def highlight_alerts(row, threshold):
    """Highlights a row in the DataFrame if its percentage difference crosses the threshold."""
    # Ensure the column exists and is not None before comparing
    if 'Difference (%)' in row and row['Difference (%)'] is not None and abs(row['Difference (%)']) > threshold:
        return ['background-color: #8B0000; color: white'] * len(row)
    else:
        return [''] * len(row)

# --- Main Application Logic ---
st.title("🚨 NSE vs. BSE Price Arbitrage Dashboard")
st.caption(f"Data is subject to delay from Yahoo Finance. Last refreshed: {datetime.now().strftime('%I:%M:%S %p')}")

stock_df = get_stock_list()

if stock_df is not None:
    # --- UI Controls ---
    st.sidebar.header("Dashboard Controls")
    
    alert_threshold = st.sidebar.number_input(
        "Alert Threshold (%)", 
        min_value=0.0, 
        max_value=10.0, 
        value=0.5,
        step=0.1,
        help="Set the percentage difference you want to be alerted for."
    )
    
    refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 5, 60, 10)
    num_stocks = st.sidebar.slider("Number of Stocks to Display", 5, len(stock_df), 10)

    placeholder = st.empty()

    while True:
        subset_df = stock_df.head(num_stocks)
        results = []
        alerts_list = []

        progress_bar = st.progress(0, text="Initializing...")
        
        # --- FIX: Using enumerate for a reliable loop counter ---
        for i, (index, row) in enumerate(subset_df.iterrows()):
            progress_text = f"Fetching data for {row['companyName']}..."
            # Use the reliable counter 'i' instead of 'index'
            progress_value = (i + 1) / num_stocks
            progress_bar.progress(progress_value, text=progress_text)
            
            nse_ticker = row['nseSymbol'] + ".NS"
            bse_ticker = str(row['bseScripCode']) + ".BO"
            
            nse_price = get_live_price(nse_ticker)
            bse_price = get_live_price(bse_ticker)

            if nse_price is not None and bse_price is not None:
                difference = nse_price - bse_price
                percentage_diff = (difference / nse_price) * 100 if nse_price != 0 else 0
                
                if abs(percentage_diff) > alert_threshold:
                    alerts_list.append({
                        "Company": row['companyName'],
                        "NSE Price": f"₹{nse_price:.2f}",
                        "BSE Price": f"₹{bse_price:.2f}",
                        "Gap": f"{percentage_diff:.2f}%"
                    })
            else:
                difference = None
                percentage_diff = None
            
            results.append({
                "Company Name": row['companyName'],
                "NSE Price (₹)": nse_price,
                "BSE Price (₹)": bse_price,
                "Difference (₹)": difference,
                "Difference (%)": percentage_diff,
            })
        
        progress_bar.empty()
        results_df = pd.DataFrame(results)

        with placeholder.container():
            st.subheader(f"Alerts Triggered (Gap > {alert_threshold}%)")
            if not alerts_list:
                st.info("No stocks have crossed the alert threshold in this batch.")
            else:
                for alert in alerts_list:
                    st.error(
                        f"**{alert['Company']}**: Gap of **{alert['Gap']}** (NSE: {alert['NSE Price']}, BSE: {alert['BSE Price']})", 
                        icon="🔥"
                    )
            
            st.header("Live Price Comparison Table")
            
            if not results_df.empty:
                # Filter out rows with None values before styling
                results_df.dropna(subset=['Difference (%)'], inplace=True)
                styled_df = results_df.style.apply(
                    highlight_alerts, threshold=alert_threshold, axis=1
                ).format({
                    "NSE Price (₹)": "₹{:.2f}",
                    "BSE Price (₹)": "₹{:.2f}",
                    "Difference (₹)": "{:+.2f}",
                    "Difference (%)": "{:+.2f}%",
                })
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
            else:
                st.warning("Could not fetch data for the selected stocks.")

        time.sleep(refresh_rate)