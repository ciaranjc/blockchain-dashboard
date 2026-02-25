import requests
import pandas as pd

DUNE_API_KEY = "RFMOcmSflJvpo2iYn40WMETlR9cN58pm"
QUERY_ID = 6706569  # <-- replace with your actual query ID from step 3

resp = requests.get(
    f"https://api.dune.com/api/v1/query/{QUERY_ID}/results",
    headers={"X-Dune-Api-Key": DUNE_API_KEY},
    params={"limit": 10000}
)
resp.raise_for_status()

rows = resp.json()["result"]["rows"]
df = pd.DataFrame(rows)
df["day"] = pd.to_datetime(df["day"]).dt.date
df = df.pivot_table(
    index="day", columns="stablecoin",
    values="active_senders", aggfunc="sum"
).fillna(0).astype(int)
df.index = pd.DatetimeIndex(df.index)
df = df.sort_index()

print(df)