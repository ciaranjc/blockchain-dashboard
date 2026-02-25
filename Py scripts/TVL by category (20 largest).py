# -*- coding: utf-8 -*-
"""
Created on Thu Feb 12 16:18:27 2026

@author: ROB8341
"""

import requests
import pandas as pd
import time
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm

# --- CONFIGURATION ---
LIMIT = 100  # We fetch more protocols to get a better representation of each category


print(f"--- Fetching Data for Top {LIMIT} Protocols to Group by Category ---")

# 1. Fetch protocol list
list_url = "https://api.llama.fi/protocols"
response = requests.get(list_url, timeout=30)
protocols = response.json()

# Sort by TVL and handle None values
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
    category = proto.get('category')  # Keep track of the category
    
    try:
        res = requests.get(f"https://api.llama.fi/protocol/{slug}", timeout=20)
        if res.status_code == 200:
            hist_tvl = res.json().get('tvl', [])
            for entry in hist_tvl:
                all_data.append({
                    'date': datetime.fromtimestamp(entry['date']).strftime('%Y-%m-%d'),
                    'category': category,
                    'tvl': entry.get('totalLiquidityUSD', 0)
                })
            print(f"[{i+1}/{LIMIT}] Processed: {name} ({category})")
        time.sleep(0.15) # Politeness delay
    except Exception as e:
        print(f"Error fetching {name}: {e}")

# 3. Create initial DataFrame
df_long = pd.DataFrame(all_data)

# 4. AGGREGATE BY CATEGORY AND DATE
# This sums up all protocol TVLs that belong to the same category on the same day
df_daily_categories = df_long.groupby(['date', 'category'])['tvl'].sum().reset_index()

# 5. Pivot to "Wide" Format: Rows = Dates, Columns = Categories
df_categories = df_daily_categories.pivot(index='date', columns='category', values='tvl')

# 6. Final Cleaning
df_categories.index = pd.to_datetime(df_categories.index)
df_categories = df_categories.sort_index()
df_categories = df_categories.fillna(0)  # Fill gaps with 0


# 1. Prepare and Sort Data
# We sort columns based on the most recent TVL so the biggest categories are at the bottom
sorted_cols = df_categories.iloc[-1].sort_values(ascending=False).index
df_plot = df_categories[sorted_cols].copy()


# 1. Get the number of categories
num_categories = len(df_plot.columns)

# 2. Generate a list of unique colors from a large colormap
# 'tab20' is good for 20 categories; 'gist_rainbow' works for any number
colors = [cm.gist_rainbow(i) for i in np.linspace(0, 1, num_categories)]

# 2. Calculate the 100% Stacked version
df_perc = df_plot.div(df_plot.sum(axis=1), axis=0) * 100

# ---------------------------------------------------------
# GRAPH 1: ABSOLUTE USD STACKED AREA
# ---------------------------------------------------------
# 3. Apply these colors to your plot
plt.figure(figsize=(15, 8))
plt.stackplot(df_plot.index, df_plot.T, labels=df_plot.columns, colors=colors, alpha=0.8)

plt.title('Unfiltered DeFi TVL by Category (Absolute USD)', fontsize=15, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Total Value Locked (USD)', fontsize=12)
plt.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=8, ncol=2)
plt.grid(axis='y', linestyle='--', alpha=0.3)
plt.tight_layout()
plt.show() # This opens the first window

# ---------------------------------------------------------
# GRAPH 2: 100% MARKET SHARE STACKED AREA
# ---------------------------------------------------------
plt.figure(figsize=(15, 8))
plt.stackplot(df_perc.index, df_perc.T, labels=df_plot.columns, colors=colors, alpha=0.8)

plt.title('Unfiltered DeFi Market Share by Category (100% Stacked)', fontsize=15, fontweight='bold')
plt.xlabel('Date', fontsize=12)
plt.ylabel('Market Share (%)', fontsize=12)
plt.ylim(0, 100)
plt.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=8, ncol=2)
plt.grid(axis='y', linestyle='--', alpha=0.3)
plt.tight_layout()
plt.show() # This opens the second window