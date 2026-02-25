# -*- coding: utf-8 -*-
"""
Created on Wed Feb 11 17:39:44 2026

@author: ROB8341
"""


import requests
import pandas as pd
import matplotlib.pyplot as plt
import time

# 1. Identify Top 20 Chains by Current TVL
print("Fetching top 20 chains list...")
chains_url = "https://api.llama.fi/v2/chains"
all_chains = requests.get(chains_url).json()

# Sort by current TVL and extract names/slugs
top_20 = sorted(all_chains, key=lambda x: x.get('tvl', 0), reverse=True)[:20]
chain_map = {c['name'].lower().replace(" ", "-"): c['name'] for c in top_20}
chain_slugs = list(chain_map.keys())

# 2. Fetch Historical TVL for each chain
master_df = pd.DataFrame()

print(f"Downloading history for {len(chain_slugs)} chains...")
for slug in chain_slugs:
    try:
        url = f"https://api.llama.fi/v2/historicalChainTvl/{slug}"
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'], unit='s')
            df.set_index('date', inplace=True)
            df.columns = [chain_map[slug]] # Use clean display name
            
            # Merge into master DataFrame
            master_df = master_df.join(df, how='outer') if not master_df.empty else df
        time.sleep(0.1) # Respect API limits
    except Exception as e:
        print(f"Skipping {slug} due to error: {e}")

# 3. Data Cleanup
master_df = master_df.fillna(0).sort_index()
# Slice to last 12 months for a cleaner visual
plot_df = master_df.tail(365) 

# 4. Create the Stacked Area Chart
plt.figure(figsize=(15, 8))
plt.stackplot(plot_df.index, plot_df.T, labels=plot_df.columns, alpha=0.8)

# Formatting
plt.title('Top 20 Blockchain Chains: TVL Market Share (Last 12 Months)', fontsize=16, fontweight='bold')
plt.ylabel('Total Value Locked (USD)', fontsize=12)
plt.xlabel('Date', fontsize=12)
plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), title="Chains", fontsize=9)
plt.grid(axis='y', alpha=0.3, linestyle='--')

# Format Y-axis to Billions/Millions
def format_currency(x, pos):
    if x >= 1e9: return f'${x*1e-9:.1f}B'
    return f'${x*1e-6:.0f}M'

plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(format_currency))

plt.tight_layout()
plt.savefig('top_20_chains_tvl_stacked.png')
master_df.to_csv('top_20_chains_tvl_data.csv')

print("Success! Chart saved as 'top_20_chains_tvl_stacked.png' and data saved to CSV.")