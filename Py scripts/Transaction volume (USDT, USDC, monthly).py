import requests
import pandas as pd
import matplotlib.pyplot as plt
import time

def get_stablecoin_volume_data():
    print("--- Fetching Stablecoin Monthly Data (Last 24 Months) ---")
    
    # Get USDT and USDC data
    coins = {
        'tether': 'USDT',
        'usd-coin': 'USDC'
    }
    
    stable_volumes = {}
    
    for coin_id, coin_name in coins.items():
        print(f"Syncing Volume: {coin_name}")
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=365&interval=daily"
            res = requests.get(url).json()
            
            if 'error' in res:
                print(f"  API Error: {res['error']}")
                continue
            
            if 'total_volumes' in res and res['total_volumes']:
                vols = res['total_volumes']
                print(f"  Got {len(vols)} volume data points")
                
                temp_df = pd.DataFrame(vols, columns=['timestamp', coin_name])
                temp_df['date'] = pd.to_datetime(temp_df['timestamp'], unit='ms')
                
                # Group by month and sum volumes
                temp_df['month'] = temp_df['date'].dt.to_period('M')
                monthly_data = temp_df.groupby('month')[coin_name].sum()
                stable_volumes[coin_name] = monthly_data
                print(f"  Grouped into {len(monthly_data)} months")
            else:
                print(f"  No volume data found")
            
            time.sleep(2.5)
        except Exception as e:
            print(f"  Error: {e}")
    
    if not stable_volumes:
        print("No data collected!")
        return None
    
    df = pd.DataFrame(stable_volumes).fillna(0)
    
    # Convert PeriodIndex to timestamp for plotting
    if hasattr(df.index, 'to_timestamp'):
        df.index = df.index.to_timestamp()
    
    # Add Total column
    df['Total'] = df['USDT'] + df['USDC']
    
    print(f"\nDate range: {df.index.min()} to {df.index.max()}")
    print(f"Shape: {df.shape}")
    
    return df

# Run and Plot
df_stables = get_stablecoin_volume_data()
if df_stables is not None:
    plt.figure(figsize=(14, 8))
    plot_cols = ['USDT', 'USDC']
    
    plt.stackplot(df_stables.index, 
                  [df_stables[c] for c in plot_cols], 
                  labels=plot_cols, 
                  alpha=0.8)
    
    plt.title('Monthly Stablecoin Volume: USDT vs USDC (Last 24 Months)', fontsize=14, fontweight='bold')
    plt.ylabel('Monthly Volume (USD)')
    plt.xlabel('Date')
    plt.legend(loc='upper left', fontsize='medium')
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    print("\nMonthly Stablecoin Volume Breakdown:")
    print(df_stables)