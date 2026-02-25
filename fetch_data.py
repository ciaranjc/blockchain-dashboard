"""
fetch_data.py  –  Replaces Power Query / Excel data refresh.
Fetches all blockchain dashboard data directly from public APIs:
  - DefiLlama (stablecoins, TVL, fees, protocols)
  - Binance (token prices)
  - CoinGecko (stablecoin volumes)
  - Dune Analytics (ETH active addresses)
"""

import os
import math
import time
from datetime import datetime, timezone
from collections import defaultdict

import requests

# ── Config ────────────────────────────────────────────────────────────────────
DUNE_API_KEY   = os.environ.get("DUNE_API_KEY", "")
DUNE_QUERY_ID  = "6707340"

CHAINS = [
    "ethereum", "solana", "bsc", "bitcoin",
    "tron", "base", "plasma", "arbitrum", "hyperliquid-l1", "provenance",
]
BINANCE_MAP = {
    "ethereum": "ETH", "bitcoin": "BTC",  "solana":  "SOL",
    "bsc":      "BNB", "tron":    "TRX",  "base":    "ETH",
    "arbitrum": "ETH", "hyperliquid-l1": "HYPE",
}

sess = requests.Session()
sess.headers.update({"User-Agent": "blockchain-dashboard/1.0"})


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_json(url, params=None, headers=None, retries=3, timeout=30):
    for attempt in range(retries):
        try:
            r = sess.get(url, params=params, headers=headers, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            if attempt == retries - 1:
                print(f"  WARN: failed {url}: {exc}")
                return None
            time.sleep(2 ** attempt)


def ts_to_date(ts):
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")


def rolling7(vals):
    """7-day rolling average (assumes vals ordered oldest→newest)."""
    out = []
    for i in range(len(vals)):
        window = [v for v in vals[max(0, i - 6): i + 1] if v is not None and v != 0]
        out.append(sum(window) / len(window) if window else None)
    return out


def rolling_corr(x, y, window=90):
    """Rolling Pearson correlation of % changes (oldest→newest)."""
    n = len(x)

    def pct(vals):
        out = [None]
        for i in range(1, len(vals)):
            if vals[i] is not None and vals[i - 1]:
                out.append((vals[i] - vals[i - 1]) / vals[i - 1])
            else:
                out.append(None)
        return out

    xp, yp = pct(x), pct(y)
    result = [None] * n
    for i in range(window, n):
        pairs = [
            (a, b) for a, b in zip(xp[i - window: i], yp[i - window: i])
            if a is not None and b is not None
        ]
        if len(pairs) < 20:
            continue
        xs, ys = zip(*pairs)
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
        den = math.sqrt(
            sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys)
        )
        result[i] = num / den if den > 1e-10 else None
    return result


# ── Data fetchers ─────────────────────────────────────────────────────────────
def fetch_stablecoin_overview():
    """Returns (overview_top30, peg_mech_items)."""
    print("  Fetching stablecoin overview...")
    raw    = get_json("https://stablecoins.llama.fi/stablecoins") or {}
    assets = raw.get("peggedAssets", [])
    total_circ = sum(
        ((a.get("circulating") or {}).get("peggedUSD") or 0) for a in assets
    )

    overview = []
    for a in assets:
        circ       = (a.get("circulating")        or {}).get("peggedUSD") or 0
        prev_day   = (a.get("circulatingPrevDay")  or {}).get("peggedUSD") or 0
        prev_week  = (a.get("circulatingPrevWeek") or {}).get("peggedUSD") or 0
        prev_month = (a.get("circulatingPrevMonth")or {}).get("peggedUSD") or 0
        overview.append({
            "name":          a.get("name"),
            "symbol":        a.get("symbol"),
            "peg_mechanism": a.get("pegMechanism"),
            "market_share":  circ / total_circ if total_circ else 0,
            "circulating":   circ,
            "change_1d":     (circ / prev_day   - 1) if prev_day   else 0,
            "change_1w":     (circ / prev_week  - 1) if prev_week  else 0,
            "change_1m":     (circ / prev_month - 1) if prev_month else 0,
            "peg":           a.get("price"),
        })

    overview.sort(key=lambda x: -(x["circulating"] or 0))

    peg_mech = {}
    for s in overview:
        m = s["peg_mechanism"] or "Unknown"
        peg_mech[m] = peg_mech.get(m, 0) + (s["circulating"] or 0)

    return overview[:30], list(peg_mech.items())


def fetch_stablecoin_market_caps():
    """Returns (dates, usdt, usdc, others, total) newest-first, sampled every 3."""
    print("  Fetching stablecoin market caps...")
    total_raw = get_json("https://stablecoins.llama.fi/stablecoincharts/all") or []
    usdt_raw  = get_json("https://stablecoins.llama.fi/stablecoin/1") or {}
    usdc_raw  = get_json("https://stablecoins.llama.fi/stablecoin/2") or {}

    date_total = {
        ts_to_date(d["date"]): (
            (d.get("totalCirculatingUSD") or d.get("totalCirculating") or {}).get("peggedUSD") or 0
        )
        for d in total_raw
    }
    date_usdt = {
        ts_to_date(t["date"]): ((t.get("circulating") or {}).get("peggedUSD") or 0)
        for t in usdt_raw.get("tokens", [])
    }
    date_usdc = {
        ts_to_date(t["date"]): ((t.get("circulating") or {}).get("peggedUSD") or 0)
        for t in usdc_raw.get("tokens", [])
    }

    all_dates_desc = sorted(date_total.keys(), reverse=True)
    dates, usdt, usdc, others, total = [], [], [], [], []
    for i, d in enumerate(all_dates_desc):
        if i % 3 != 0:
            continue
        t = date_total.get(d) or 0
        u = date_usdt.get(d)  or 0
        c = date_usdc.get(d)  or 0
        dates.append(d);  usdt.append(u);   usdc.append(c)
        others.append(max(0, t - u - c));   total.append(t)

    return dates, usdt, usdc, others, total


def fetch_eth_active_addresses():
    """Returns (dates, usdt_counts, usdc_counts) newest-first monthly."""
    print("  Fetching ETH active addresses (Dune)...")
    if not DUNE_API_KEY:
        print("    DUNE_API_KEY not set - skipping active addresses")
        return [], [], []

    raw = get_json(
        f"https://api.dune.com/api/v1/query/{DUNE_QUERY_ID}/results",
        headers={"X-Dune-Api-Key": DUNE_API_KEY},
        params={"limit": 10000},
    ) or {}
    rows = (raw.get("result") or {}).get("rows", [])

    by_month = {}
    for row in rows:
        month  = str(row.get("month", "")).replace(" UTC", "").split(" ")[0][:10]
        stable = str(row.get("stablecoin", ""))
        count  = row.get("active_senders", 0)
        if month not in by_month:
            by_month[month] = {"USDT": None, "USDC": None}
        if "USDT" in stable.upper():
            by_month[month]["USDT"] = count
        elif "USDC" in stable.upper():
            by_month[month]["USDC"] = count

    sorted_months = sorted(by_month.keys(), reverse=True)
    return (
        sorted_months,
        [by_month[m].get("USDT") for m in sorted_months],
        [by_month[m].get("USDC") for m in sorted_months],
    )


def fetch_binance_prices(ticker):
    """Returns {date_str: close_price} for up to ~3000 days."""
    result   = {}
    end_time = None
    for _ in range(3):
        params = {"symbol": f"{ticker}USDT", "interval": "1d", "limit": 1000}
        if end_time:
            params["endTime"] = end_time
        klines = get_json("https://api.binance.com/api/v3/klines", params=params)
        if not klines:
            break
        for k in klines:
            d = datetime.fromtimestamp(k[0] / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            result[d] = float(k[4])
        end_time = klines[0][0] - 1
    return result


def fetch_fees_and_prices():
    """
    Returns dict with fee_dates, fee_eth/sol/bsc/btc/tron/base/total,
    fee_eth/sol_price, fee_eth/sol_native.  All lists newest-first, every 3.
    Also returns _btc_price_daily and _eth_price_daily lookup dicts.
    """
    print("  Fetching global fees...")
    global_raw = get_json(
        "https://api.llama.fi/overview/fees?excludeTotalDataChart=false"
    ) or {}
    global_chart = {
        ts_to_date(row[0]): row[1]
        for row in global_raw.get("totalDataChart", [])
    }

    chain_fees = {}
    for chain in CHAINS:
        print(f"  Fetching fees for {chain}...")
        raw = get_json(
            f"https://api.llama.fi/overview/fees/{chain}?excludeTotalDataChart=false",
            timeout=25,
        ) or {}
        chain_fees[chain] = {
            ts_to_date(row[0]): row[1]
            for row in raw.get("totalDataChart", [])
        }
        time.sleep(0.3)

    print("  Fetching prices from Binance...")
    prices = {}
    for ticker in set(BINANCE_MAP.values()):
        print(f"    {ticker}...")
        prices[ticker] = fetch_binance_prices(ticker)
        time.sleep(0.2)

    all_dates_asc = sorted(global_chart.keys())

    raw_eth   = [chain_fees["ethereum"].get(d) for d in all_dates_asc]
    raw_sol   = [chain_fees["solana"].get(d)   for d in all_dates_asc]
    raw_bsc   = [chain_fees["bsc"].get(d)      for d in all_dates_asc]
    raw_btc   = [chain_fees["bitcoin"].get(d)  for d in all_dates_asc]
    raw_tron  = [chain_fees["tron"].get(d)     for d in all_dates_asc]
    raw_base  = [chain_fees["base"].get(d)     for d in all_dates_asc]
    raw_total = [global_chart.get(d)           for d in all_dates_asc]

    ep_asc = [prices.get("ETH", {}).get(d) for d in all_dates_asc]
    sp_asc = [prices.get("SOL", {}).get(d) for d in all_dates_asc]
    bp_asc = [prices.get("BTC", {}).get(d) for d in all_dates_asc]

    avg_eth   = rolling7(raw_eth)
    avg_sol   = rolling7(raw_sol)
    avg_bsc   = rolling7(raw_bsc)
    avg_btc   = rolling7(raw_btc)
    avg_tron  = rolling7(raw_tron)
    avg_base  = rolling7(raw_base)
    avg_total = rolling7(raw_total)

    def safe_div(a, b):
        return a / b if a and b else None

    nat_eth = [safe_div(f, p) for f, p in zip(avg_eth, ep_asc)]
    nat_sol = [safe_div(f, p) for f, p in zip(avg_sol, sp_asc)]

    idxs = list(range(0, len(all_dates_asc), 3))
    def sr(lst): return [lst[i] for i in idxs][::-1]

    return {
        "fee_dates":       sr(all_dates_asc),
        "fee_eth":         sr(avg_eth),
        "fee_sol":         sr(avg_sol),
        "fee_bsc":         sr(avg_bsc),
        "fee_btc":         sr(avg_btc),
        "fee_tron":        sr(avg_tron),
        "fee_base":        sr(avg_base),
        "fee_total":       sr(avg_total),
        "fee_eth_price":   sr(ep_asc),
        "fee_sol_price":   sr(sp_asc),
        "fee_eth_native":  sr(nat_eth),
        "fee_sol_native":  sr(nat_sol),
        # Return full Binance price dicts directly — not indexed by fee dates,
        # so correlations work even when fee API calls fail (e.g. corporate firewall)
        "_btc_price_daily": prices.get("BTC", {}),
        "_eth_price_daily": prices.get("ETH", {}),
    }


def fetch_tvl_data():
    """Returns dicts for total TVL and per-chain TVL (newest-first)."""
    print("  Fetching TVL by chain...")
    chains_raw = get_json("https://api.llama.fi/v2/chains") or []
    top_chains = sorted(chains_raw, key=lambda x: -(x.get("tvl") or 0))[:10]
    slugs = [c["name"].lower().replace(" ", "-") for c in top_chains]

    chain_hist = {}
    for slug in slugs:
        raw = get_json(f"https://api.llama.fi/v2/historicalChainTvl/{slug}") or []
        chain_hist[slug] = {ts_to_date(r["date"]): r.get("tvl", 0) for r in raw}
        time.sleep(0.25)

    print("  Fetching total TVL...")
    total_raw  = get_json("https://api.llama.fi/v2/historicalChainTvl") or []
    date_total = {ts_to_date(r["date"]): r.get("tvl", 0) for r in total_raw}

    all_dates_asc = sorted(date_total.keys())

    def col(slug):
        return [chain_hist.get(slug, {}).get(d) for d in all_dates_asc]

    eth_a   = col("ethereum");  sol_a  = col("solana")
    bsc_a   = col("bsc");       btc_a  = col("bitcoin")
    tron_a  = col("tron");      base_a = col("base")
    arb_a   = col("arbitrum")
    total_a = [date_total.get(d) for d in all_dates_asc]
    other_a = [
        max(0, (total_a[i] or 0) - sum(
            (v or 0) for v in [eth_a[i], sol_a[i], bsc_a[i], btc_a[i],
                                tron_a[i], base_a[i], arb_a[i]]
        ))
        for i in range(len(all_dates_asc))
    ]

    idxs3 = list(range(0, len(all_dates_asc), 3))
    idxs5 = list(range(0, len(all_dates_asc), 5))
    def sr3(lst): return [lst[i] for i in idxs3][::-1]
    def sr5(lst): return [lst[i] for i in idxs5][::-1]

    return {
        "tvl_dates":        sr3(all_dates_asc),
        "tvl_eth":          sr3(eth_a),   "tvl_sol":  sr3(sol_a),
        "tvl_bsc":          sr3(bsc_a),   "tvl_btc":  sr3(btc_a),
        "tvl_tron":         sr3(tron_a),  "tvl_base": sr3(base_a),
        "tvl_arb":          sr3(arb_a),   "tvl_other":sr3(other_a),
        "tvl_total":        sr3(total_a),
        "total_tvl_dates":  sr5(all_dates_asc),
        "total_tvl_vals":   sr5(total_a),
    }


def fetch_protocols():
    """Returns (top_protocols, cat_tvl_sorted)."""
    print("  Fetching protocols...")
    raw = get_json("https://api.llama.fi/protocols") or []
    protocols = []
    for p in raw:
        tvl = p.get("tvl")
        if p.get("name") and tvl is not None:
            protocols.append({
                "name":      p.get("name"),
                "category":  p.get("category") or "Unknown",
                "chain":     p.get("chain")    or "Unknown",
                "tvl":       tvl,
                "change_1d": p.get("change_1d"),
                "change_7d": p.get("change_7d"),
            })
    protocols.sort(key=lambda x: -(x["tvl"] or 0))
    cat_tvl = {}
    for p in protocols:
        cat_tvl[p["category"]] = cat_tvl.get(p["category"], 0) + (p["tvl"] or 0)
    return protocols[:50], sorted(cat_tvl.items(), key=lambda x: -x[1])[:15]


def fetch_volume():
    """CoinGecko daily volumes for USDT/USDC + monthly aggregation."""
    print("  Fetching stablecoin volumes from CoinGecko...")

    def _coin_vol(coin_id):
        raw = get_json(
            f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart",
            params={"vs_currency": "usd", "days": "365", "interval": "daily"},
            timeout=25,
        ) or {}
        by_date = {}
        for ts, vol in raw.get("total_volumes", []):
            d = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            by_date[d] = vol
        return by_date

    usdt_vol = _coin_vol("tether");  time.sleep(1.5)
    usdc_vol = _coin_vol("usd-coin")

    all_dates = sorted(set(usdt_vol) | set(usdc_vol), reverse=True)
    tvd_dates, tvd_usdt, tvd_usdc, tvd_total = [], [], [], []
    for d in all_dates:
        u = usdt_vol.get(d, 0) or 0
        c = usdc_vol.get(d, 0) or 0
        tvd_dates.append(d); tvd_usdt.append(u)
        tvd_usdc.append(c);  tvd_total.append(u + c)

    total_asc = tvd_total[::-1]
    tvd_total_7d = rolling7(total_asc)[::-1]

    month_sums = defaultdict(lambda: {"usdt": 0.0, "usdc": 0.0})
    for d, u, c in zip(tvd_dates, tvd_usdt, tvd_usdc):
        m = d[:7] + "-01"
        month_sums[m]["usdt"] += u
        month_sums[m]["usdc"] += c

    sorted_months = sorted(month_sums.keys(), reverse=True)
    return {
        "tvd_dates":    tvd_dates,
        "tvd_usdt":     tvd_usdt,
        "tvd_usdc":     tvd_usdc,
        "tvd_total":    tvd_total,
        "tvd_total_7d": tvd_total_7d,
        "tvm_months":   sorted_months,
        "tvm_usdt":     [month_sums[m]["usdt"] for m in sorted_months],
        "tvm_usdc":     [month_sums[m]["usdc"] for m in sorted_months],
        "tvm_total":    [month_sums[m]["usdt"] + month_sums[m]["usdc"] for m in sorted_months],
    }


def build_correlations(sc_usdt_by_date, sc_usdc_by_date, eth_prices, btc_prices):
    """90-day rolling Pearson correlations of % changes (newest-first output)."""
    print("  Computing correlations...")
    all_dates_asc = sorted(
        set(sc_usdt_by_date) & set(sc_usdc_by_date) & set(eth_prices) & set(btc_prices)
    )
    usdt_a = [sc_usdt_by_date.get(d) for d in all_dates_asc]
    usdc_a = [sc_usdc_by_date.get(d) for d in all_dates_asc]
    eth_a  = [eth_prices.get(d)      for d in all_dates_asc]
    btc_a  = [btc_prices.get(d)      for d in all_dates_asc]

    corr_te = rolling_corr(usdt_a, eth_a)
    corr_tb = rolling_corr(usdt_a, btc_a)
    corr_ce = rolling_corr(usdc_a, eth_a)
    corr_cb = rolling_corr(usdc_a, btc_a)

    return {
        "corr_dates":       all_dates_asc[::-1],
        "corr_tether_eth":  corr_te[::-1],
        "corr_tether_btc":  corr_tb[::-1],
        "corr_usdc_eth":    corr_ce[::-1],
        "corr_usdc_btc":    corr_cb[::-1],
        "eth_price":        eth_a[::-1],
        "btc_price":        btc_a[::-1],
        "corr_tether_mcap": usdt_a[::-1],
        "corr_usdc_mcap":   usdc_a[::-1],
    }


def build_fee_efficiency(fee_dates_desc, fee_raw_by_chain, tvl_by_chain_date):
    """Monthly fee/TVL efficiency ratios for key chains."""
    CHAINS_FE = ["Ethereum", "Solana", "BSC", "Bitcoin", "Tron", "Base"]
    CHAIN_MAP  = {
        "Ethereum": "ethereum", "Solana": "solana", "BSC": "bsc",
        "Bitcoin":  "bitcoin",  "Tron":   "tron",   "Base": "base",
    }

    monthly_fees = defaultdict(lambda: defaultdict(float))
    monthly_tvl  = defaultdict(lambda: defaultdict(float))

    for i, d in enumerate(fee_dates_desc):
        month = d[:7] + "-01"
        for chain_name in CHAINS_FE:
            slug  = CHAIN_MAP[chain_name]
            fees  = fee_raw_by_chain.get(slug, [])
            f_val = fees[i] if i < len(fees) else None
            if f_val:
                monthly_fees[month][chain_name] += f_val

    for chain_name in CHAINS_FE:
        slug = CHAIN_MAP[chain_name]
        for date, tvl in tvl_by_chain_date.get(slug, {}).items():
            month = date[:7] + "-01"
            monthly_tvl[month][chain_name] = tvl

    all_months  = sorted(set(monthly_fees) | set(monthly_tvl), reverse=True)
    fe_months   = []
    fe_eff      = {c: [] for c in CHAINS_FE}
    fe_eff_total= []

    for month in all_months:
        total_fees = sum(monthly_fees[month].values())
        total_tvl  = sum(monthly_tvl[month].values())
        fe_months.append(month)
        fe_eff_total.append((total_fees / total_tvl) if total_tvl else None)
        for chain_name in CHAINS_FE:
            f = monthly_fees[month].get(chain_name, 0)
            t = monthly_tvl[month].get(chain_name)
            fe_eff[chain_name].append((f / t) if t else None)

    return fe_months, fe_eff, fe_eff_total


# ── Main ──────────────────────────────────────────────────────────────────────
def fetch_all():
    print("Fetching all dashboard data...")

    stablecoin_overview, peg_mech = fetch_stablecoin_overview()
    sc_dates, sc_usdt, sc_usdc, sc_others, sc_total = fetch_stablecoin_market_caps()
    aa_dates, aa_usdt, aa_usdc = fetch_eth_active_addresses()

    fees            = fetch_fees_and_prices()
    btc_price_daily = fees.pop("_btc_price_daily")
    eth_price_daily = fees.pop("_eth_price_daily")

    tvl              = fetch_tvl_data()
    top_protocols, cat_tvl_sorted = fetch_protocols()
    vol              = fetch_volume()

    # Daily USDT/USDC market cap for correlations
    usdt_raw = get_json("https://stablecoins.llama.fi/stablecoin/1") or {}
    usdc_raw = get_json("https://stablecoins.llama.fi/stablecoin/2") or {}
    sc_usdt_daily = {
        ts_to_date(t["date"]): ((t.get("circulating") or {}).get("peggedUSD") or 0)
        for t in usdt_raw.get("tokens", [])
    }
    sc_usdc_daily = {
        ts_to_date(t["date"]): ((t.get("circulating") or {}).get("peggedUSD") or 0)
        for t in usdc_raw.get("tokens", [])
    }
    corr = build_correlations(sc_usdt_daily, sc_usdc_daily, eth_price_daily, btc_price_daily)

    tvd_btc_price = [btc_price_daily.get(d) for d in vol["tvd_dates"]]

    # Daily TVL per chain for fee efficiency
    print("  Fetching per-chain TVL for fee efficiency...")
    tvl_by_chain_date = {}
    for slug in ["ethereum", "solana", "bsc", "bitcoin", "tron", "base"]:
        raw = get_json(f"https://api.llama.fi/v2/historicalChainTvl/{slug}") or []
        tvl_by_chain_date[slug] = {ts_to_date(r["date"]): r.get("tvl", 0) for r in raw}
        time.sleep(0.2)

    fee_raw_by_chain = {
        "ethereum": fees["fee_eth"],  "solana": fees["fee_sol"],
        "bsc":      fees["fee_bsc"],  "bitcoin":fees["fee_btc"],
        "tron":     fees["fee_tron"], "base":   fees["fee_base"],
    }
    fe_months, fe_eff, fe_eff_total = build_fee_efficiency(
        fees["fee_dates"], fee_raw_by_chain, tvl_by_chain_date
    )

    latest_total_sc   = sc_total[0]           if sc_total           else 0
    latest_total_tvl  = tvl["tvl_total"][0]   if tvl["tvl_total"]   else 0
    latest_total_fees = fees["fee_total"][0]  if fees["fee_total"]  else 0

    all_dates_for_update = [
        dl[0] for dl in [sc_dates, fees["fee_dates"], vol["tvd_dates"], corr["corr_dates"]]
        if dl
    ]
    last_update = max(all_dates_for_update) if all_dates_for_update else "N/A"

    print("Done.")
    return {
        "stablecoin_overview": stablecoin_overview,
        "sc_dates": sc_dates, "sc_usdt": sc_usdt, "sc_usdc": sc_usdc,
        "sc_others": sc_others, "sc_total": sc_total,
        "aa_dates": aa_dates, "aa_usdt": aa_usdt, "aa_usdc": aa_usdc,
        **corr,
        **fees,
        **tvl,
        "top_protocols":  top_protocols,
        "cat_tvl":        cat_tvl_sorted,
        "peg_mech":       peg_mech,
        "tvm_months":     vol["tvm_months"], "tvm_usdt": vol["tvm_usdt"],
        "tvm_usdc":       vol["tvm_usdc"],   "tvm_total": vol["tvm_total"],
        "tvd_dates":      vol["tvd_dates"],  "tvd_usdt":  vol["tvd_usdt"],
        "tvd_usdc":       vol["tvd_usdc"],   "tvd_total": vol["tvd_total"],
        "tvd_total_7d":   vol["tvd_total_7d"],
        "tvd_btc_price":  tvd_btc_price,
        "fe_months":      fe_months,
        "fe_eff":         fe_eff,
        "fe_eff_total":   fe_eff_total,
        "has_tvm": len(vol["tvm_months"]) > 0,
        "has_tvd": len(vol["tvd_dates"])  > 0,
        "has_fe":  len(fe_months)         > 0,
        "kpi": {
            "total_sc_mcap":  latest_total_sc,
            "total_tvl":      latest_total_tvl,
            "total_fees":     latest_total_fees,
            "protocol_count": len(top_protocols),
        },
        "_last_update": last_update,
    }


if __name__ == "__main__":
    d = fetch_all()
    print(f"sc_dates:    {d['sc_dates'][:3]}")
    print(f"fee_dates:   {d['fee_dates'][:3]}")
    print(f"peg_mech:    {d['peg_mech']}")
    print(f"last_update: {d['_last_update']}")
