import time
import random
from rich.live import Live
from rich.table import Table

# 1. Stock Symbol Mapping
# In a real app, this could be loaded from a file.
# Format: { 'COMMON_NAME': {'nse': 'NSE_SYMBOL', 'bse': 'BSE_CODE'} }
STOCK_MAP = {
    'RELIANCE': {'nse': 'RELIANCE', 'bse': '500325'},
    'TCS': {'nse': 'TCS', 'bse': '532540'},
    'INFOSYS': {'nse': 'INFY', 'bse': '500209'},
    'HDFCBANK': {'nse': 'HDFCBANK', 'bse': '500180'},
    'ICICIBANK': {'nse': 'ICICIBANK', 'bse': '532174'},
}

# 2. Simulated Real-Time API
# --- THIS IS THE PART YOU WOULD REPLACE WITH A REAL API CALL ---
def get_simulated_prices(nse_symbol, bse_code):
    """
    Simulates fetching prices from an API.
    Returns a dictionary with NSE and BSE prices.
    """
    # Base price to make simulation look realistic
    base_prices = {'RELIANCE': 2900, 'TCS': 3850, 'INFY': 1650, 'HDFCBANK': 1500, 'ICICIBANK': 1100}
    base_price = base_prices.get(nse_symbol, 1000)

    # Introduce small, random fluctuations
    nse_price = base_price + random.uniform(-0.5, 0.5)
    bse_price = base_price + random.uniform(-0.5, 0.5)

    return {'nse': nse_price, 'bse': bse_price}
# ----------------------------------------------------------------

def generate_table() -> Table:
    """Generate a Rich Table with the latest stock price comparison."""
    table = Table(title="NSE vs. BSE Real-Time Price Comparator")
    table.add_column("Stock", style="cyan", no_wrap=True)
    table.add_column("NSE Price", style="green")
    table.add_column("BSE Price", style="green")
    table.add_column("Difference (₹)", justify="right", style="magenta")
    table.add_column("Difference (%)", justify="right", style="yellow")

    # 3. Processing Engine
    for name, symbols in STOCK_MAP.items():
        # Fetch prices (using our simulator)
        prices = get_simulated_prices(symbols['nse'], symbols['bse'])
        nse_price = prices['nse']
        bse_price = prices['bse']

        # Calculate differences
        if nse_price > 0: # Avoid division by zero
            difference = nse_price - bse_price
            percentage_diff = (difference / nse_price) * 100
        else:
            difference = 0
            percentage_diff = 0

        # Determine color based on which price is higher
        if difference > 0:
            diff_str = f"[bold red]+{difference:.2f}[/bold red]"
            pct_str = f"[bold red]+{percentage_diff:.3f}%[/bold red]"
        elif difference < 0:
            diff_str = f"[bold green]{difference:.2f}[/bold green]"
            pct_str = f"[bold green]{percentage_diff:.3f}%[/bold green]"
        else:
            diff_str = f"{difference:.2f}"
            pct_str = f"{percentage_diff:.3f}%"


        table.add_row(
            name,
            f"₹{nse_price:.2f}",
            f"₹{bse_price:.2f}",
            diff_str,
            pct_str
        )
    return table

# 4. Display the live-updating table
with Live(generate_table(), screen=True, refresh_per_second=2) as live:
    while True:
        time.sleep(0.5)
        live.update(generate_table())