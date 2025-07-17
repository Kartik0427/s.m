import pandas as pd
import requests

def generate_final_file():
    """
    Downloads the instrument list and filters it using the correct values
    to create the final 'instrument_list.csv'.
    """
    print("Downloading the latest instrument list...")
    instrument_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    
    try:
        response = requests.get(instrument_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not isinstance(data, list) or not data:
            print("❌ ERROR: Downloaded data is not a valid list or is empty.")
            return

        print(f"✅ Successfully downloaded {len(data)} total instruments. Processing...")
        
        df = pd.DataFrame(data)
        
        # --- CORRECTED FILTERING LOGIC ---
        # We will only filter by exchange, as 'instrumenttype' was the issue.
        # This is more robust and ensures all NSE/BSE stocks are included.
        df_filtered = df[df['exch_seg'].isin(['NSE', 'BSE'])].copy()

        # Clean the symbol column (e.g., 'TCS-EQ' becomes 'TCS')
        df_filtered['symbol'] = df_filtered['symbol'].str.split('-').str[0]
        
        # Select and rename final columns
        df_final = df_filtered[['token', 'symbol', 'name', 'exch_seg', 'lotsize']].copy()
        df_final.rename(columns={'symbol': 'api_symbol'}, inplace=True)
        
        # Save the final, correct CSV file
        df_final.to_csv("instrument_list.csv", index=False)

        print(f"\n✅ Successfully created 'instrument_list.csv' with {len(df_final)} entries.")

    except requests.exceptions.RequestException as e:
        print(f"❌ NETWORK ERROR: Could not download the file. {e}")
    except Exception as e:
        print(f"❌ AN UNEXPECTED ERROR OCCURRED: {e}")

if __name__ == "__main__":
    generate_final_file()