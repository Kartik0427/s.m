import pandas as pd
import requests

def generate_file():
    """
    Downloads the complete instrument list from Angel One, processes it,
    and saves a filtered CSV for use in the main app.
    """
    print("Downloading the latest instrument list...")
    instrument_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    
    try:
        response = requests.get(instrument_url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if not isinstance(data, list) or not data:
            print("❌ ERROR: Downloaded data is not a valid list or is empty. Please try again later.")
            return

        print(f"Successfully downloaded {len(data)} total instruments. Processing...")
        
        # Create the DataFrame
        df = pd.DataFrame(data)
        
        # --- Data Cleaning and Filtering ---
        # Ensure required columns exist
        required_cols = {'exch_seg', 'instrumenttype', 'symbol', 'token', 'name', 'lotsize'}
        if not required_cols.issubset(df.columns):
            print(f"❌ ERROR: Downloaded data is missing required columns.")
            return

        # 1. Filter for NSE and BSE equities only
        df = df[df['exch_seg'].isin(['NSE', 'BSE'])].copy()
        df = df[df['instrumenttype'] == 'EQUITY'].copy()

        # 2. Clean the symbol (e.g., 'TCS-EQ' becomes 'TCS')
        df['symbol'] = df['symbol'].str.split('-').str[0]
        
        # 3. Select and rename columns
        df_final = df[['token', 'symbol', 'name', 'exch_seg', 'lotsize']].copy()
        df_final.rename(columns={'symbol': 'api_symbol'}, inplace=True)
        
        # 4. Save to CSV
        df_final.to_csv("instrument_list.csv", index=False)

        print(f"\n✅ Successfully created 'instrument_list.csv' with {len(df_final)} entries.")

    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: Could not download the file. Check your internet connection. Details: {e}")
    except Exception as e:
        print(f"❌ AN UNEXPECTED ERROR OCCURRED: {e}")

if __name__ == "__main__":
    generate_file()