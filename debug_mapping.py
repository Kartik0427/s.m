import pandas as pd

def debug_the_mapping():
    """
    This script loads both mapping files and shows exactly why
    the symbols might not be matching.
    """
    try:
        # Load both files, ensuring data types are treated as strings
        instrument_df = pd.read_csv("instrument_list.csv", dtype=str)
        map_df = pd.read_csv("bse_nse_mapping.csv", dtype=str)
        print("✅ --- Files Loaded Successfully ---")
    except FileNotFoundError as e:
        print(f"❌ ERROR: Could not find a file. {e}")
        return

    # --- Let's test with just one stock: TCS ---
    stock_to_test = 'TCS'
    print(f"\n--- 🐞 DEBUGGING FOR: {stock_to_test} ---")

    # 1. Get symbols from your mapping file
    stock_info = map_df[map_df['nseSymbol'] == stock_to_test]
    if stock_info.empty:
        print(f"❌ ERROR: Could not find '{stock_to_test}' in your bse_nse_mapping.csv file.")
        return

    nse_symbol_from_map = stock_info.iloc[0]['nseSymbol']
    bse_code_from_map = stock_info.iloc[0]['bseScripCode']

    print("\n[Your Mapping File Says]:")
    print(f"  - NSE Symbol to find: '{nse_symbol_from_map}'")
    print(f"  - BSE Code to find:   '{bse_code_from_map}'")

    # 2. Search in the master instrument list
    print("\n[Searching in `instrument_list.csv`]:")
    
    # --- NSE Search ---
    # Strip any hidden whitespace from the column for a clean match
    nse_match = instrument_df[
        (instrument_df['api_symbol'].str.strip() == nse_symbol_from_map.strip()) &
        (instrument_df['exch_seg'] == 'NSE')
    ]
    
    print(f"\n1. Attempting to find exact match for NSE symbol '{nse_symbol_from_map}'...")
    if not nse_match.empty:
        print("✅ --- NSE MATCH FOUND ---")
        print(nse_match)
    else:
        print("❌ --- NO EXACT NSE MATCH FOUND ---")
        # If no exact match, show what IS in the master list for that symbol
        potential_nse_matches = instrument_df[instrument_df['api_symbol'].str.contains(nse_symbol_from_map, na=False)]
        if not potential_nse_matches.empty:
            print("\nHere are some potential entries for TCS in the instrument list:")
            print(potential_nse_matches[['token', 'api_symbol', 'name', 'exch_seg']])
        else:
            print("Could not find any entries containing 'TCS'.")


    # --- BSE Search ---
    bse_match = instrument_df[
        (instrument_df['api_symbol'].str.strip() == bse_code_from_map.strip()) &
        (instrument_df['exch_seg'] == 'BSE')
    ]
    
    print(f"\n2. Attempting to find exact match for BSE code '{bse_code_from_map}'...")
    if not bse_match.empty:
        print("✅ --- BSE MATCH FOUND ---")
        print(bse_match)
    else:
        print("❌ --- NO EXACT BSE MATCH FOUND ---")


if __name__ == "__main__":
    debug_the_mapping()