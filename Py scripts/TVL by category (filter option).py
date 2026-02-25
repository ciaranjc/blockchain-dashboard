# -*- coding: utf-8 -*-
"""
Created on Thu Feb 12 16:24:28 2026

@author: ROB8341
"""

import requests
import pandas as pd
import time
from datetime import datetime
import matplotlib.pyplot as plt
# --- CONFIGURATION ---
# We filter for these specific categories
TARGET_CATEGORIES = ['RWA', 'RWA Lending', 'OTC Marketplace'] 
FILENAME = "rwa_historical_timeseries.csv"

print(f"--- Searching for all protocols in categories: {TARGET_CATEGORIES} ---")

# 1. Fetch all protocols and filter by category
list_url = "https://api.llama.fi/protocols"
response = requests.get(list_url, timeout=30)
protocols = response.json()

# Filter protocols that match our target categories
rwa_protocols = [
    p for p in protocols 
    if p.get('category') in TARGET_CATEGORIES
]

print(f"Found {len(rwa_protocols)} RWA-related protocols. Starting history fetch...")

all_data = []

# 2. Fetch history for each RWA protocol
for i, proto in enumerate(rwa_protocols):
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
            print(f"[{i+1}/{len(rwa_protocols)}] Processed: {name}")
        
        # API Politeness
        time.sleep(0.15)
            
    except Exception as e:
        print(f"Error fetching {name}: {e}")

# 3. Create DataFrame
df_long = pd.DataFrame(all_data)

if not df_long.empty:
    # 4. Pivot to Wide Format (Dates as Rows, Protocols as Columns)
    df_rwa_wide = df_long.pivot_table(index='date', columns='protocol', values='tvl', aggfunc='first')
    
    # 5. Final Cleaning
    df_rwa_wide.index = pd.to_datetime(df_rwa_wide.index)
    df_rwa_wide = df_rwa_wide.sort_index()
    df_rwa_wide = df_rwa_wide.fillna(0) # Fill days where a protocol didn't exist with 0
    
    # Save and verify
    df_rwa_wide.to_csv(FILENAME)
    print("\n--- DONE ---")
    print(f"Variable 'df_rwa_wide' created with {df_rwa_wide.shape[1]} protocols.")
    print(f"File saved: {FILENAME}")
    
    # Display the most recent TVL values for the top columns
    print(df_rwa_wide.tail())
else:
    print("No data found for the specified categories.")
    
    
    
# 1. Identify the current top 20 protocols based on the last row
current_tvl = df_rwa_wide.iloc[-1]
top_20_names = current_tvl.sort_values(ascending=False).head(20).index.tolist()

# 2. Create the new DataFrame
# Keep only the top 20 columns
df_top_20 = df_rwa_wide[top_20_names].copy()

# 3. Calculate 'Others' (Everything not in the top 20)
# This ensures our 'Total' is truly the sum of the entire RWA market
other_cols = [c for c in df_rwa_wide.columns if c not in top_20_names]
df_top_20['Others'] = df_rwa_wide[other_cols].sum(axis=1)

# 4. Calculate 'Total'
# Summing across all columns (Top 20 + Others)
df_top_20['Total_Market'] = df_top_20.sum(axis=1)

# 5. Plotting a Stacked Area Chart
# We exclude 'Total_Market' from the plot itself so we can see the breakdown
plot_data = df_top_20.drop(columns=['Total_Market'])

plt.figure(figsize=(14, 8))
plt.stackplot(plot_data.index, plot_data.T, labels=plot_data.columns, alpha=0.8)

plt.title('Top 20 RWA Protocols by TVL (Stacked)', fontsize=16)
plt.xlabel('Date', fontsize=12)
plt.ylabel('TVL (USD)', fontsize=12)
plt.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=9)
plt.grid(axis='y', alpha=0.3)
plt.tight_layout()

# Display the plot
plt.show()

# Print the most recent totals for verification
print("Current Total RWA Market TVL:", f"${df_top_20['Total_Market'].iloc[-1]:,.2f}")

# 2. Create the working DataFrame with Top 20
df_rwa_final = df_rwa_wide[top_20_names].copy()

# 3. Calculate 'Others' (Sum of everything not in top 20)
other_cols = [c for c in df_rwa_wide.columns if c not in top_20_names]
df_rwa_final['Others'] = df_rwa_wide[other_cols].sum(axis=1)

# 4. Calculate 'Total' (This is your denominator for the 100% version)
df_rwa_final['Total'] = df_rwa_final.sum(axis=1)
df_percentage = df_rwa_final.drop(columns=['Total']).div(df_rwa_final['Total'], axis=0) * 100
# 5. Plotting the 100% Stacked Area Chart
plt.figure(figsize=(14, 8))
plt.stackplot(df_percentage.index, df_percentage.T, labels=df_percentage.columns, alpha=0.85)

# Formatting
plt.title('RWA Market Share % (Top 20 Protocols)', fontsize=16)
plt.xlabel('Date', fontsize=12)
plt.ylabel('Market Share (%)', fontsize=12)
plt.ylim(0, 100) # Force the Y-axis to 100%
plt.legend(loc='upper left', bbox_to_anchor=(1, 1), fontsize=9)
plt.grid(axis='y', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.show()

# Verification: Print the current market share of the top leader
leader_name = top_20_names[0]
current_share = df_percentage[leader_name].iloc[-1]
print(f"Current Market Leader: {leader_name} ({current_share:.2f}% share)")