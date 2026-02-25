import pandas as pd
import requests
import time

# 1. Get the list of top 10 chains by TVL
chains_url = "https://api.llama.fi/v2/chains"
all_chains = requests.get(chains_url).json()
top_10_chains = sorted(all_chains, key=lambda x: x.get('tvl', 0), reverse=True)[:10]
chain_slugs = [c['name'].lower().replace(" ", "-") for c in top_10_chains]

# 2. Fetch Global Total Fees History (Market-wide)
print("Fetching global market fee history...")
total_fees_url = "https://api.llama.fi/overview/fees?excludeTotalDataChart=false"
global_res = requests.get(total_fees_url).json()
global_chart = global_res.get('totalDataChart', [])

# Initialize Master DF with Global Total
master_df = pd.DataFrame(global_chart, columns=['timestamp', 'Market_Total_Fees'])
master_df['date'] = pd.to_datetime(master_df['timestamp'], unit='s')
master_df.set_index('date', inplace=True)
master_df.drop(columns=['timestamp'], inplace=True)

# 3. Loop through Top 10 Chains and join them to the Master DF
print(f"Fetching history for: {', '.join(chain_slugs)}")
for slug in chain_slugs:
    try:
        fee_url = f"https://api.llama.fi/overview/fees/{slug}?excludeTotalDataChart=false"
        res = requests.get(fee_url).json()
        chart_data = res.get('totalDataChart', [])
        
        if chart_data:
            temp_df = pd.DataFrame(chart_data, columns=['timestamp', slug])
            temp_df['date'] = pd.to_datetime(temp_df['timestamp'], unit='s')
            temp_df.set_index('date', inplace=True)
            master_df = master_df.join(temp_df[[slug]], how='left')
        
        time.sleep(0.2)
    except Exception as e:
        print(f"Skipping {slug}: {e}")

# 4. Data Cleaning & Calculations
master_df = master_df.fillna(0)

# Calculate "Other" = Total - Sum(Top 10)
# We sum across the columns we just added (the chain slugs)
master_df['Other_Chains'] = master_df['Market_Total_Fees'] - master_df[chain_slugs].sum(axis=1)

# Ensure 'Other' isn't negative due to rounding or API data lags
master_df['Other_Chains'] = master_df['Other_Chains'].clip(lower=0)

# Reorder columns to put Total and Other at the end
final_cols = chain_slugs + ['Other_Chains', 'Market_Total_Fees']
master_df = master_df[final_cols]
