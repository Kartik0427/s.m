# File: merge_stocks.py

import pandas as pd
import re

print("Starting the merge process...")

# --- Functions to clean company names ---
def clean_company_name(name):
  """
  Cleans and standardizes company names for matching.
  - Converts to uppercase
  - Removes Ltd, Limited, etc.
  - Replaces '&' with 'AND'
  - Removes special characters
  - Strips extra whitespace
  """
  try:
    # Convert to string and handle potential float values
    name = str(name).strip().upper()
    # Remove common corporate suffixes using a more robust regex
    name = re.sub(r'\s+(LTD|LIMITED|PVT|PRIVATE|CORP|CORPORATION|INC|INCORPORATED)(\.)?$', '', name)
    # Replace ampersand
    name = name.replace('&', 'AND')
    # Remove all non-alphanumeric characters except spaces
    name = re.sub(r'[^A-Z0-9\s]', '', name)
    # Collapse multiple spaces into one
    name = re.sub(r'\s+', ' ', name).strip()
    return name
  except AttributeError:
    return '' # Return empty string for non-string inputs like NaN

# --- Main script ---
try:
    # --- Load the datasets ---
    # Load the BSE Bhavcopy file
    bse_df = pd.read_csv('BSE.csv')
    print("BSE file loaded successfully.")

    # Load the NSE stock list file
    nse_df = pd.read_csv('NSE.csv')
    print("NSE file loaded successfully.")

    # --- Select and clean relevant columns ---
    # For BSE, select the scrip code and company name
    bse_stocks = bse_df[['bseScripCode', 'companyName']].copy()
    bse_stocks.rename(columns={'companyName': 'bse_companyName'}, inplace=True)
    bse_stocks['clean_name'] = bse_stocks['bse_companyName'].apply(clean_company_name)
    print(f"Processed {len(bse_stocks)} rows from BSE file.")

    # For NSE, select the symbol and company name
    nse_stocks = nse_df[['nseSymbol', 'companyName']].copy()
    nse_stocks.rename(columns={'companyName': 'nse_companyName'}, inplace=True)
    nse_stocks['clean_name'] = nse_stocks['nse_companyName'].apply(clean_company_name)
    print(f"Processed {len(nse_stocks)} rows from NSE file.")

    # --- Merge the dataframes ---
    # Merge based on the cleaned company name
    # Using a left merge to keep all NSE stocks and find matching BSE codes
    merged_df = pd.merge(nse_stocks, bse_stocks, on='clean_name', how='left')
    print(f"Merge complete. Found {len(merged_df[merged_df['bseScripCode'].notna()])} matching records.")

    # --- Finalize the output DataFrame ---
    # Select and rename the final columns
    final_df = merged_df[['nse_companyName', 'nseSymbol', 'bseScripCode']]
    final_df.rename(columns={'nse_companyName': 'companyName'}, inplace=True)

    # Fill missing BSE codes with 'Not Available'
    final_df['bseScripCode'] = final_df['bseScripCode'].fillna('Not Available')


    # --- Save to CSV ---
    output_filename = 'nse_bse_merged.csv'
    final_df.to_csv(output_filename, index=False)

    print(f"\nSuccessfully created the complete merged file: '{output_filename}'")
    print(f"Total rows in the final file: {len(final_df)}")

except FileNotFoundError as e:
    print(f"\nError: {e}")
    print("Please make sure both 'BSE.csv' and 'NSE.csv' are in the same folder as this script.")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")