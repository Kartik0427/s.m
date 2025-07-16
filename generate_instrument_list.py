import pandas as pd
import requests

def generate_file():
    """
    Downloads the complete instrument list from Angel One, processes it,
    and saves a filtered CSV for use in the main app.
    """
    print("Downloading the latest instrument list from Angel One...")
    try:
        url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        response = requests.get(url)
        response.raise_for_status()  # This will raise an error for bad responses (like 404, 500)
        
        # The JSON data is a list of dictionaries
        data = response.json()
        
        if not data:
            print("Error: Downloaded data is empty.")
            return

        # Explicitly create a pandas DataFrame from the data
        # At this point, 'df' is a DataFrame object
        df = pd.DataFrame(data)
        
        print("Processing data...")

        # Filter for relevant columns and equities on NSE & BSE
        df = df[df['exch_seg'].isin(['NSE', 'BSE'])]
        df = df[df['instrumenttype'] == 'EQUITY']
        
        # Ensure 'symbol' column doesn't have extra characters for matching
        # This operation is performed on a DataFrame Series
        df['symbol'] = df['symbol'].str.split('-').str[0]
        
        # Select and rename columns for clarity
        df = df[['token', 'symbol', 'name', 'exch_seg', 'lotsize']]
        
        # .rename() is a DataFrame method
        df.rename(columns={'symbol': 'api_symbol'}, inplace=True)

        # .to_csv() is a DataFrame method
        df.to_csv("instrument_list.csv", index=False)

        print("\n✅ Successfully created 'instrument_list.csv'")
        print(f"File contains {len(df)} entries.")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading file: {e}")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    generate_file()