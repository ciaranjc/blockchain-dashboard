import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import time

# --- CONFIGURATION ---
STABLECOIN_ID = "1"  # 1 = USDT
START_DATE = '2025-01-01'

# 1. Fetch Stablecoin History (DeFiLlama)
print(f"--- Fetching Stablecoin Data ---")
url = f"https://stablecoins.llama.fi/stablecoin/{STABLECOIN_ID}"
res = requests.get(url).json()
COIN_NAME = res.get('name', "Tether")

chain_data = res.get('chainBalances', {})
all_dfs = []

for chain, data in chain_data.items():
    hist = data.get('tokens', [])
    if not hist: continue
    t_df = pd.DataFrame(hist)
    t_df['date'] = pd.to_datetime(t_df['date'], unit='s').dt.date
    t_df[chain] = t_df['circulating'].apply(lambda x: x.get('peggedUSD', 0) if isinstance(x, dict) else 0)
    all_dfs.append(t_df[['date', chain]].set_index('date'))

df_stables = pd.concat(all_dfs, axis=1).fillna(0)
df_stables.index = pd.to_datetime(df_stables.index)
df_stables = df_stables[df_stables.index >= START_DATE].sort_index()

# 2. Fetch BTC Price (Switching to CoinGecko for reliability)
print("--- Fetching BTC Price (CoinGecko) ---")
# Get 365 days of data to ensure the 2025 window is fully covered
btc_url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=365&interval=daily"
try:
    btc_res = requests.get(btc_url).json()
    prices = btc_res.get('prices', [])
    df_btc = pd.DataFrame(prices, columns=['timestamp', 'price'])
    df_btc['date'] = pd.to_datetime(df_btc['timestamp'], unit='ms').dt.date
    df_btc = df_btc[['date', 'price']].set_index('date')
    df_btc.index = pd.to_datetime(df_btc.index)
except Exception as e:
    print(f"CoinGecko Error: {e}. Falling back to a 0-line.")
    df_btc = pd.DataFrame({'price': 0}, index=df_stables.index)

# 3. Clean up the Stablecoin Chains (Top 10 + Others)
top_10 = df_stables.iloc[-1].sort_values(ascending=False).head(10).index.tolist()
df_final_stables = df_stables[top_10].copy()
df_final_stables['Others'] = df_stables.drop(columns=top_10).sum(axis=1)

# 4. Merge and Plot
df_plot = df_final_stables.join(df_btc, how='left').ffill()

if df_plot.empty or df_plot.sum().sum() == 0:
    print("Error: The final dataframe is empty. Check API reachability.")
else:
    fig, ax1 = plt.subplots(figsize=(14, 7))
    
    # Area Plot for Stablecoins
    ax1.stackplot(df_plot.index, df_plot.drop(columns='price').T, 
                  labels=df_plot.drop(columns='price').columns, alpha=0.85)
    ax1.set_ylabel('Supply (USD)', fontsize=12, fontweight='bold')
    
    # Line Plot for BTC
    ax2 = ax1.twinx()
    ax2.plot(df_plot.index, df_plot['price'], color='black', linewidth=3, label='BTC Price')
    ax2.set_ylabel('BTC Price (USD)', fontsize=12, color='black', fontweight='bold')
    
    # Formatting
    plt.title(f'{COIN_NAME} Distribution vs BTC Price (2025)', fontsize=16, fontweight='bold')
    ax1.legend(loc='upper left', bbox_to_anchor=(1.1, 1))
    plt.grid(axis='y', alpha=0.2)
    plt.tight_layout()
    plt.show()