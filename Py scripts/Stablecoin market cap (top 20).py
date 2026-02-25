# -*- coding: utf-8 -*-
"""
Created on Wed Feb 11 15:20:24 2026

@author: ROB8341
"""

import pandas as pd
from defillama_sdk import DefiLlama

# Initialize client
client = DefiLlama()

def get_stablecoin_data(limit=20):
    """Fetches top stablecoin data and merges into a single DataFrame."""
    stablecoins = client.stablecoins.getStablecoins()
    pegged_assets = stablecoins.get('peggedAssets', [])
    
    # 1. Get the list of top coin IDs and their names
    top_assets = pegged_assets[:limit]
    
    main_df = None

    for asset in top_assets:
        coin_id = asset['id']
        coin_name = asset.get('name', f"coin_{coin_id}")
        
        # Fetch individual history
        data = client.stablecoins.getStablecoin(coin_id)
        tokens = data.get("tokens", [])
        
        if not tokens:
            continue
            
        # Create temp DataFrame for this coin
        temp_df = pd.DataFrame([
            {"date": pd.to_datetime(t["date"], unit='s'), coin_name: t["circulating"]["peggedUSD"]}
            for t in tokens
        ])
        
        # Merge logic
        if main_df is None:
            main_df = temp_df
        else:
            main_df = pd.merge(main_df, temp_df, on='date', how='outer')

    return main_df.sort_values('date').fillna(0)

# --- Execution ---
coin_df = get_stablecoin_data(limit=20)

# 2. Add Total Market Cap
total_list = client.stablecoins.getAllCharts()
total_map = {pd.to_datetime(item["date"], unit='s'): item["totalCirculating"]["peggedUSD"] for item in total_list}

coin_df['Total_Market'] = coin_df['date'].map(total_map).fillna(0)

# 3. Calculate 'Others'
# Difference between Total_Market and the sum of all individual coin columns
coin_cols = coin_df.columns.difference(['date', 'Total_Market'])
coin_df['Others'] = (coin_df['Total_Market'] - coin_df[coin_cols].sum(axis=1)).clip(lower=0)

# 4. Final Formatting
coin_df = coin_df.set_index('date')

'''
# 5. Export to Excel
output_path = r'C:\Users\ROB8341\OneDrive - Robeco Nederland B.V\Blockchain dashboard\Py\data.xlsx'
coin_df.to_excel(output_path)
'''
