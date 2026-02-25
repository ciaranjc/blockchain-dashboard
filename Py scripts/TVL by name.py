import requests
import pandas as pd
import time
from datetime import datetime

# --- CONFIGURATION ---
LIMIT = 20  # Number of top protocols to fetch
FILENAME = "defillama_wide_format.csv"

print(f"--- Fetching Top {LIMIT} Protocols ---")

# 1. Fetch protocol list and sort by TVL (Handling NoneType)
list_url = "https://api.llama.fi/protocols"
response = requests.get(list_url, timeout=30)
protocols = response.json()

top_protocols = sorted(
    protocols, 
    key=lambda x: x.get('tvl') if x.get('tvl') is not None else 0, 
    reverse=True
)[:LIMIT]

all_data = []

# 2. Fetch historical data for each protocol
for i, proto in enumerate(top_protocols):
    name = proto.get('name')
    slug = proto.get('slug')
    
    try:
        res = requests.get(f"https://api.llama.fi/protocol/{slug}", timeout=20)
        if res.status_code == 200:
            hist_tvl = res.json().get('tvl', [])
            for entry in hist_tvl:
                all_data.append({
                    'date': datetime.fromtimestamp(entry['date']).strftime('%Y-%m-%d'),
                    'protocol': name,
                    'tvl': entry.get('totalLiquidityUSD', 0)
                })
            print(f"[{i+1}/{LIMIT}] Processed: {name}")
        time.sleep(0.2)
    except Exception as e:
        print(f"Error fetching {name}: {e}")

# 3. Create initial "Long" DataFrame
df_long = pd.DataFrame(all_data)

# 4. Pivot to "Wide" Format: Rows = Dates, Columns = Protocols
# We use pivot_table with 'first' to handle any potential duplicate date entries
df_wide = df_long.pivot_table(index='date', columns='protocol', values='tvl', aggfunc='first')

# 5. Final Cleaning
df_wide.index = pd.to_datetime(df_wide.index)
df_wide = df_wide.sort_index()
df_wide = df_wide.fillna(0)  # Fill missing dates with 0 TVL

# Save and Display
df_wide.to_csv(FILENAME)
print("\n--- DONE ---")
print(f"Wide DataFrame created: {df_wide.shape[0]} rows x {df_wide.shape[1]} columns")
print(f"Saved to: {FILENAME}")

# Look at the last few rows in the console
print(df_wide.tail())