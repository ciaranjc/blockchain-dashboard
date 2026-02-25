import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(SCRIPT_DIR, 'blockchain_dashboard.html')

# Fetch all data from public APIs (replaces Excel / Power Query)
sys.path.insert(0, SCRIPT_DIR)
from fetch_data import fetch_all

data        = fetch_all()
last_update = data.pop('_last_update', 'N/A')

data_json = json.dumps(data, default=str)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Blockchain Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Roboto+Condensed:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Roboto Condensed', 'Segoe UI', system-ui, sans-serif;
    background: #ffffff;
    color: #333333;
    min-height: 100vh;
  }}
  .header {{
    background: linear-gradient(135deg, #004a6e 0%, #007a99 100%);
    padding: 24px 40px;
    border-bottom: 1px solid #e0e0e0;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }}
  .header h1 {{
    font-size: 28px;
    font-weight: 700;
    color: #ffffff;
  }}
  .header .subtitle {{ color: rgba(255,255,255,0.75); font-size: 14px; }}
  .header .date {{ color: #ffffff; font-size: 14px; font-weight: 500; }}
  .kpi-row {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    padding: 20px 40px;
  }}
  .kpi-card {{
    background: #f7f8fa;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 20px 24px;
    transition: transform 0.2s, box-shadow 0.2s;
  }}
  .kpi-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.06);
  }}
  .kpi-label {{ font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
  .kpi-value {{ font-size: 28px; font-weight: 700; color: #222; }}
  .kpi-value .unit {{ font-size: 16px; color: #888; font-weight: 400; }}
  .dashboard {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    padding: 0 40px 40px;
  }}
  .chart-card {{
    background: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 16px;
    min-height: 420px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }}
  .chart-card.full-width {{
    grid-column: 1 / -1;
  }}
  .chart-card h3 {{
    font-size: 15px;
    font-weight: 600;
    color: #333;
    margin-bottom: 4px;
    padding-left: 4px;
  }}
  .chart-card .chart-desc {{
    font-size: 11px;
    color: #888;
    margin-bottom: 8px;
    padding-left: 4px;
  }}
  .chart-source {{
    font-size: 10px;
    color: #aaa;
    margin-top: 6px;
    padding-left: 4px;
    border-top: 1px solid #f0f0f0;
    padding-top: 4px;
  }}
  .tabs {{
    display: flex;
    gap: 4px;
    margin-bottom: 8px;
    padding-left: 4px;
    flex-wrap: wrap;
  }}
  .tab-btn {{
    background: #f0f1f3;
    color: #666;
    border: 1px solid #ddd;
    padding: 5px 14px;
    border-radius: 6px;
    font-size: 12px;
    font-family: 'Roboto Condensed', sans-serif;
    cursor: pointer;
    transition: all 0.2s;
  }}
  .tab-btn:hover {{ background: #e4e6e9; }}
  .tab-btn.active {{ background: #00A2BD; color: #fff; border-color: #00A2BD; font-weight: 600; }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }}
  th {{ text-align: left; padding: 10px 8px; color: #666; font-weight: 600; border-bottom: 2px solid #e0e0e0; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px; }}
  td {{ padding: 8px; border-bottom: 1px solid #f0f0f0; color: #333; }}
  tr:hover td {{ background: rgba(0, 162, 189, 0.04); }}
  .positive {{ color: #4a7a00; }}
  .negative {{ color: #B50063; }}
  .nav-tabs {{
    display: flex;
    gap: 0;
    padding: 10px 40px 0;
    border-bottom: 2px solid #e0e0e0;
    margin-bottom: 16px;
  }}
  .nav-tab {{
    padding: 10px 24px;
    color: #888;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    font-size: 14px;
    transition: all 0.2s;
    font-weight: 500;
    margin-bottom: -2px;
    font-family: 'Roboto Condensed', sans-serif;
  }}
  .nav-tab:hover {{ color: #333; }}
  .nav-tab.active {{ color: #00A2BD; border-bottom-color: #00A2BD; }}
  .section {{ display: block; }}
  .section.hidden {{ display: none; }}
  .scrollable-table {{ max-height: 380px; overflow-y: auto; }}
  .scrollable-table::-webkit-scrollbar {{ width: 6px; }}
  .scrollable-table::-webkit-scrollbar-track {{ background: #f5f5f5; }}
  .scrollable-table::-webkit-scrollbar-thumb {{ background: #ccc; border-radius: 3px; }}
  @media (max-width: 900px) {{
    .kpi-row {{ grid-template-columns: repeat(2, 1fr); }}
    .dashboard {{ grid-template-columns: 1fr; }}
    .header, .kpi-row, .dashboard, .nav-tabs {{ padding-left: 16px; padding-right: 16px; }}
  }}
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>Blockchain & DeFi Dashboard</h1>
    <div class="subtitle">Stablecoins, TVL, Fees, Protocols & Crypto-stablecoin interactions</div>
  </div>
  <div class="date">Last updated: {last_update}</div>
</div>

<div class="kpi-row" id="kpis"></div>

<div class="nav-tabs">
  <div class="nav-tab active" onclick="showSection('stablecoins', this)">Stablecoins</div>
  <div class="nav-tab" onclick="showSection('defi', this)">Total value locked</div>
  <div class="nav-tab" onclick="showSection('fees', this)">Fees</div>
  <div class="nav-tab" onclick="showSection('protocols', this)">Protocols</div>
  <div class="nav-tab" onclick="showSection('insights', this)">Crypto-stablecoin interactions</div>
</div>

<div id="stablecoins" class="section active">
  <div class="dashboard">
    <div class="chart-card full-width">
      <h3>Stablecoin Market Cap Over Time</h3>
      <div class="chart-desc">Historical market cap breakdown: USDT, USDC, and Others</div>
      <div class="tabs">
        <button class="tab-btn active" onclick="updateScChart('stacked', this)">Stacked</button>
        <button class="tab-btn" onclick="updateScChart('lines', this)">Lines</button>
        <button class="tab-btn" onclick="updateScChart('pct', this)">% Share</button>
      </div>
      <div id="chart-sc-mcap" style="height:360px"></div>
      <div class="chart-source">Source: DefiLlama | Data as of {last_update}</div>
    </div>
    <div class="chart-card">
      <h3>Market Share (Current)</h3>
      <div class="chart-desc">Current circulating supply breakdown of top stablecoins</div>
      <div id="chart-sc-pie" style="height:370px"></div>
      <div class="chart-source">Source: DefiLlama | Data as of {last_update}</div>
    </div>
    <div class="chart-card">
      <h3>Peg Mechanism Breakdown</h3>
      <div class="chart-desc">Distribution by backing type: fiat-backed vs crypto-backed</div>
      <div id="chart-peg-mech" style="height:370px"></div>
      <div class="chart-source">Source: DefiLlama | Data as of {last_update}</div>
    </div>
    <div class="chart-card">
      <h3>Active Addresses on Ethereum</h3>
      <div class="chart-desc">Monthly active addresses for USDT and USDC on Ethereum</div>
      <div id="chart-active-addr" style="height:370px"></div>
      <div class="chart-source">Source: Etherscan | Data as of {last_update}</div>
    </div>
    <div class="chart-card">
      <h3>Stablecoin Transaction Volume (Monthly)</h3>
      <div class="chart-desc">Monthly USDT and USDC transaction volume</div>
      <div id="chart-tx-vol-monthly" style="height:370px"></div>
      <div class="chart-source">Source: Artemis | Data as of {last_update}</div>
    </div>
    <div class="chart-card full-width">
      <h3>Stablecoin Overview Table</h3>
      <div class="chart-desc">Top 30 stablecoins by circulating supply with 1D/1W/1M changes</div>
      <div class="scrollable-table" id="sc-table"></div>
      <div class="chart-source">Source: DefiLlama | Data as of {last_update}</div>
    </div>
  </div>
</div>

<div id="defi" class="section">
  <div class="dashboard">
    <div class="chart-card full-width">
      <h3>Total Value Locked (All Chains)</h3>
      <div class="chart-desc">Aggregate TVL across all tracked chains since 2017</div>
      <div id="chart-total-tvl" style="height:380px"></div>
      <div class="chart-source">Source: DefiLlama | Data as of {last_update}</div>
    </div>
    <div class="chart-card full-width">
      <h3>TVL by Chain</h3>
      <div class="chart-desc">Breakdown of TVL across major chains</div>
      <div class="tabs">
        <button class="tab-btn active" onclick="updateTvlChart('stacked', this)">Stacked</button>
        <button class="tab-btn" onclick="updateTvlChart('lines', this)">Lines</button>
        <button class="tab-btn" onclick="updateTvlChart('pct', this)">% Share</button>
      </div>
      <div id="chart-tvl-chain" style="height:380px"></div>
      <div class="chart-source">Source: DefiLlama | Data as of {last_update}</div>
    </div>
  </div>
</div>

<div id="fees" class="section">
  <div class="dashboard">
    <div class="chart-card full-width">
      <h3>Total Market Fees (7D Average)</h3>
      <div class="chart-desc">Daily protocol fees across all chains, smoothed with 7-day average</div>
      <div id="chart-total-fees" style="height:380px"></div>
      <div class="chart-source">Source: DefiLlama | Data as of {last_update}</div>
    </div>
    <div class="chart-card full-width">
      <h3>Fees by Chain (7D Average)</h3>
      <div class="chart-desc">Fee revenue breakdown by chain</div>
      <div class="tabs">
        <button class="tab-btn active" onclick="updateFeeChart('stacked', this)">Stacked</button>
        <button class="tab-btn" onclick="updateFeeChart('lines', this)">Lines</button>
      </div>
      <div id="chart-fees-chain" style="height:380px"></div>
      <div class="chart-source">Source: DefiLlama | Data as of {last_update}</div>
    </div>
    <div class="chart-card">
      <h3>Activity vs Token Price (Ethereum)</h3>
      <div class="chart-desc">ETH fees (7D avg) overlaid with Ethereum price</div>
      <div class="tabs">
        <button class="tab-btn active" onclick="updateActivityEth('usd', this)">Fees (USD)</button>
        <button class="tab-btn" onclick="updateActivityEth('native', this)">Fees (ETH)</button>
      </div>
      <div id="chart-activity-eth" style="height:340px"></div>
      <div class="chart-source">Source: DefiLlama, CoinGecko | Data as of {last_update}</div>
    </div>
    <div class="chart-card">
      <h3>Activity vs Token Price (Solana)</h3>
      <div class="chart-desc">SOL fees (7D avg) overlaid with Solana price</div>
      <div class="tabs">
        <button class="tab-btn active" onclick="updateActivitySol('usd', this)">Fees (USD)</button>
        <button class="tab-btn" onclick="updateActivitySol('native', this)">Fees (SOL)</button>
      </div>
      <div id="chart-activity-sol" style="height:340px"></div>
      <div class="chart-source">Source: DefiLlama, CoinGecko | Data as of {last_update}</div>
    </div>
    <div class="chart-card">
      <h3>Activity vs Token Price (Bitcoin)</h3>
      <div class="chart-desc">BTC fees (7D avg) overlaid with Bitcoin price</div>
      <div id="chart-activity-btc" style="height:340px"></div>
      <div class="chart-source">Source: DefiLlama, CoinGecko | Data as of {last_update}</div>
    </div>
    <div class="chart-card full-width">
      <h3>Stablecoin Transaction Volume (Daily)</h3>
      <div class="chart-desc">Daily USDT and USDC transaction volume</div>
      <div class="tabs">
        <button class="tab-btn active" onclick="updateTxVolChart('stacked', this)">Stacked</button>
        <button class="tab-btn" onclick="updateTxVolChart('lines', this)">Lines</button>
      </div>
      <div id="chart-tx-vol" style="height:380px"></div>
      <div class="chart-source">Source: Artemis | Data as of {last_update}</div>
    </div>
    <div class="chart-card full-width">
      <h3>Stablecoin Transaction Volume vs Token Prices</h3>
      <div class="chart-desc">7D average stablecoin transaction volume overlaid with crypto token prices</div>
      <div class="tabs">
        <button class="tab-btn active" onclick="updateTxVsPrice('btc', this)">Bitcoin</button>
        <button class="tab-btn" onclick="updateTxVsPrice('eth', this)">Ethereum</button>
        <button class="tab-btn" onclick="updateTxVsPrice('sol', this)">Solana</button>
      </div>
      <div id="chart-tx-vs-btc" style="height:350px"></div>
      <div class="chart-source">Source: Artemis, CoinGecko | Data as of {last_update}</div>
    </div>
  </div>
</div>

<div id="protocols" class="section">
  <div class="dashboard">
    <div class="chart-card full-width">
      <h3>Protocol Table (Top 50)</h3>
      <div class="scrollable-table" id="proto-table" style="max-height:500px"></div>
      <div class="chart-source">Source: DefiLlama | Data as of {last_update}</div>
    </div>
  </div>
</div>

<div id="insights" class="section">
  <div class="dashboard">
    <div class="chart-card full-width">
      <h3>Stablecoin Market Cap vs BTC/ETH Correlation (30D Rolling)</h3>
      <div class="chart-desc">Rolling 30-day correlation between stablecoin market cap changes and crypto prices</div>
      <div class="tabs">
        <button class="tab-btn active" onclick="updateCorrChart('tether', this)">USDT Correlations</button>
        <button class="tab-btn" onclick="updateCorrChart('usdc', this)">USDC Correlations</button>
        <button class="tab-btn" onclick="updateCorrChart('all', this)">All</button>
      </div>
      <div id="chart-correlation" style="height:380px"></div>
      <div class="chart-source">Source: CoinGecko, DefiLlama | Data as of {last_update}</div>
    </div>
    <div class="chart-card full-width">
      <h3>Bitcoin Price vs Stablecoin Market Cap</h3>
      <div class="chart-desc">Bitcoin price overlaid with stablecoin market cap</div>
      <div class="tabs">
        <button class="tab-btn active" onclick="updatePriceChart('usdt', this)">USDT Market Cap</button>
        <button class="tab-btn" onclick="updatePriceChart('usdc', this)">USDC Market Cap</button>
        <button class="tab-btn" onclick="updatePriceChart('both', this)">Both</button>
      </div>
      <div id="chart-prices" style="height:380px"></div>
      <div class="chart-source">Source: CoinGecko, DefiLlama | Data as of {last_update}</div>
    </div>
    <div class="chart-card full-width">
      <h3>Fee Efficiency by Chain (Fees / TVL)</h3>
      <div class="chart-desc">Monthly fee revenue as a percentage of TVL per chain</div>
      <div id="chart-efficiency" style="height:400px"></div>
      <div class="chart-source">Source: DefiLlama | Data as of {last_update}</div>
    </div>
  </div>
</div>

<script>
const D = {data_json};
const plotBg = '#ffffff';
const paperBg = '#ffffff';
const gridColor = '#e8e8e8';
const fontColor = '#666666';
const colors = ['#00A2BD','#F79608','#B50063','#4A04A5','#ADBA00','#8fa4b5','#33b5ce','#f9ab39','#c73382','#6e36b7','#bec833','#c4d1de'];
const layoutBase = {{
  paper_bgcolor: paperBg, plot_bgcolor: plotBg, font: {{ color: fontColor, size: 11, family: 'Roboto Condensed, sans-serif' }},
  margin: {{ l: 50, r: 20, t: 10, b: 40 }},
  xaxis: {{ gridcolor: gridColor, linecolor: gridColor, zerolinecolor: gridColor }},
  yaxis: {{ gridcolor: gridColor, linecolor: gridColor, zerolinecolor: gridColor }},
  legend: {{ bgcolor: 'rgba(255,255,255,0)', font: {{ size: 10 }} }},
  hovermode: 'x unified',
}};
const config = {{ responsive: true, displayModeBar: true, modeBarButtonsToRemove: ['lasso2d','select2d'], displaylogo: false }};

function fmt(n) {{
  if (n == null) return '-';
  if (Math.abs(n) >= 1e12) return '$' + (n/1e12).toFixed(2) + 'T';
  if (Math.abs(n) >= 1e9) return '$' + (n/1e9).toFixed(2) + 'B';
  if (Math.abs(n) >= 1e6) return '$' + (n/1e6).toFixed(2) + 'M';
  if (Math.abs(n) >= 1e3) return '$' + (n/1e3).toFixed(1) + 'K';
  return '$' + n.toFixed(2);
}}
function pctFmt(n) {{
  if (n == null) return '-';
  let v = (n * 100).toFixed(2);
  let cls = n >= 0 ? 'positive' : 'negative';
  return '<span class="' + cls + '">' + (n >= 0 ? '+' : '') + v + '%</span>';
}}

// Helper: find oldest date where all series have non-null non-zero values
// Data is sorted descending (newest first), so scan from end (oldest) forward
function firstValidDate(dates, ...arrays) {{
  for (let i = dates.length - 1; i >= 0; i--) {{
    if (arrays.every(arr => arr[i] != null && arr[i] !== 0)) return dates[i];
  }}
  return dates[dates.length - 1];
}}

// Fix y-axis compression — three layers:
// 1. patchLayout: set autorange:false + explicit range before Plotly renders
// 2. relayout override: inject saved y ranges into x-only calls (rangeslider/zoom)
// 3. lockEl listener: restore saved ranges on plotly_relayout as final fallback
(function() {{
  var _saved = {{}};

  function calcRanges(traces) {{
    var y1lo=Infinity,y1hi=-Infinity,y2lo=Infinity,y2hi=-Infinity,stacks={{}};
    (traces||[]).forEach(function(tr){{
      if(!tr.y) return;
      var a2=tr.yaxis==='y2';
      if(tr.stackgroup){{
        var k=(a2?'2':'1')+tr.stackgroup;
        if(!stacks[k]) stacks[k]={{a2:a2,v:{{}}}};
        tr.y.forEach(function(v,i){{if(v!=null) stacks[k].v[i]=(stacks[k].v[i]||0)+(+v);}});
      }}else{{
        tr.y.forEach(function(v){{
          if(v==null) return; v=+v;
          if(a2){{if(v<y2lo)y2lo=v;if(v>y2hi)y2hi=v;}}
          else{{if(v<y1lo)y1lo=v;if(v>y1hi)y1hi=v;}}
        }});
      }}
    }});
    Object.values(stacks).forEach(function(sg){{
      Object.values(sg.v).forEach(function(s){{
        if(sg.a2){{if(s<y2lo)y2lo=s;if(s>y2hi)y2hi=s;}}
        else{{if(s<y1lo)y1lo=s;if(s>y1hi)y1hi=s;}}
      }});
    }});
    function rng(lo,hi){{
      if(lo===Infinity) return null;
      var p=(hi-lo)*0.06||Math.abs(hi)*0.06||1;
      return [lo>=0?0:lo-p,hi+p];
    }}
    return {{y1:rng(y1lo,y1hi),y2:rng(y2lo,y2hi)}};
  }}

  function patchLayout(layout,ranges){{
    var lay=Object.assign({{}},layout);
    if(ranges.y1) lay.yaxis=Object.assign({{}},lay.yaxis,{{autorange:false,range:ranges.y1,fixedrange:true}});
    if(ranges.y2&&layout&&layout.yaxis2)
      lay.yaxis2=Object.assign({{}},lay.yaxis2,{{autorange:false,range:ranges.y2,fixedrange:true}});
    return lay;
  }}

  function lockEl(gd,ranges){{
    _saved[gd.id]=ranges;
    if(gd._yLocked) return;
    gd._yLocked=true;
    var busy=false;
    gd.on('plotly_relayout',function(ed){{
      if(busy) return;
      if(ed['xaxis.range[0]']===undefined&&ed['xaxis.range']===undefined) return;
      var r=_saved[gd.id]; if(!r) return;
      var upd={{}};
      if(r.y1){{upd['yaxis.range']=r.y1;upd['yaxis.autorange']=false;}}
      if(r.y2){{upd['yaxis2.range']=r.y2;upd['yaxis2.autorange']=false;}}
      if(Object.keys(upd).length){{busy=true;Plotly.relayout(gd,upd).then(function(){{busy=false;}});}}
    }});
  }}

  // Layer 2: intercept Plotly.relayout — add y ranges to x-only updates so
  // Plotly sets x and y in one pass, never triggering an autorange recalculation.
  var _origRL=Plotly.relayout.bind(Plotly);
  Plotly.relayout=function(gd,update){{
    var id=typeof gd==='string'?gd:(gd&&gd.id);
    var upd=Object.assign({{}},update);
    var keys=Object.keys(upd);
    var hasX=keys.some(function(k){{return k.indexOf('xaxis')===0;}});
    var hasY=keys.some(function(k){{return k.indexOf('yaxis')===0;}});
    if(hasX&&!hasY&&id&&_saved[id]){{
      var r=_saved[id];
      if(r.y1){{upd['yaxis.range']=r.y1;upd['yaxis.autorange']=false;}}
      if(r.y2){{upd['yaxis2.range']=r.y2;upd['yaxis2.autorange']=false;}}
    }}
    return _origRL(gd,upd);
  }};

  var _np=Plotly.newPlot.bind(Plotly),_re=Plotly.react.bind(Plotly);
  function _wrap(orig){{
    return function(id,data,layout,cfg){{
      var r=calcRanges(data);
      var res=orig(id,data,patchLayout(layout||{{}},r),cfg);
      Promise.resolve(res).then(function(gd){{if(gd) lockEl(gd,r);}});
      return res;
    }};
  }}
  Plotly.newPlot=_wrap(_np);
  Plotly.react=_wrap(_re);
}})();


// Pre-compute x-axis start dates (first date where all series are non-zero)
let scStart = firstValidDate(D.sc_dates, D.sc_usdt, D.sc_usdc, D.sc_others);
let tvlTotalStart = firstValidDate(D.total_tvl_dates, D.total_tvl_vals);
let tvlChainStart = firstValidDate(D.tvl_dates, D.tvl_eth, D.tvl_sol, D.tvl_tron);
let feeTotalStart = firstValidDate(D.fee_dates, D.fee_total);
let feeChainStart = firstValidDate(D.fee_dates, D.fee_eth, D.fee_sol, D.fee_tron);

// KPIs
document.getElementById('kpis').innerHTML = `
  <div class="kpi-card"><div class="kpi-label">Stablecoin Market Cap</div><div class="kpi-value">${{fmt(D.kpi.total_sc_mcap)}}</div></div>
  <div class="kpi-card"><div class="kpi-label">Total Value Locked</div><div class="kpi-value">${{fmt(D.kpi.total_tvl)}}</div></div>
  <div class="kpi-card"><div class="kpi-label">Daily Fees (7D Avg)</div><div class="kpi-value">${{fmt(D.kpi.total_fees)}}</div></div>
  <div class="kpi-card"><div class="kpi-label">Tracked Protocols</div><div class="kpi-value">${{D.kpi.protocol_count.toLocaleString()}}</div></div>
`;

// Section navigation - uses explicit btn parameter
function showSection(id, btn) {{
  document.querySelectorAll('.section').forEach(s => {{ s.classList.add('hidden'); s.classList.remove('active'); }});
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  let sec = document.getElementById(id);
  sec.classList.remove('hidden');
  sec.classList.add('active');
  if (btn) btn.classList.add('active');
  setTimeout(() => {{
    sec.querySelectorAll('.js-plotly-plot').forEach(el => Plotly.Plots.resize(el));
  }}, 50);
}}

// After all charts render, hide non-active sections
setTimeout(() => {{
  document.querySelectorAll('.section:not(.active)').forEach(s => s.classList.add('hidden'));
}}, 500);

// --- STABLECOINS ---
function updateScChart(mode, btn) {{
  document.querySelector('#chart-sc-mcap').closest('.chart-card').querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  let traces;
  if (mode === 'stacked') {{
    traces = [
      {{ x: D.sc_dates, y: D.sc_usdt, name: 'USDT', stackgroup: 'one', fillcolor: 'rgba(0,162,189,0.6)', line: {{ width: 0 }} }},
      {{ x: D.sc_dates, y: D.sc_usdc, name: 'USDC', stackgroup: 'one', fillcolor: 'rgba(247,150,8,0.6)', line: {{ width: 0 }} }},
      {{ x: D.sc_dates, y: D.sc_others, name: 'Others', stackgroup: 'one', fillcolor: 'rgba(181,0,99,0.4)', line: {{ width: 0 }} }},
    ];
  }} else if (mode === 'lines') {{
    traces = [
      {{ x: D.sc_dates, y: D.sc_usdt, name: 'USDT', line: {{ color: colors[0] }} }},
      {{ x: D.sc_dates, y: D.sc_usdc, name: 'USDC', line: {{ color: colors[1] }} }},
      {{ x: D.sc_dates, y: D.sc_others, name: 'Others', line: {{ color: colors[2] }} }},
      {{ x: D.sc_dates, y: D.sc_total, name: 'Total', line: {{ color: '#333', dash: 'dot' }} }},
    ];
  }} else {{
    let pUsdt = D.sc_usdt.map((v,i) => D.sc_total[i] ? v/D.sc_total[i]*100 : 0);
    let pUsdc = D.sc_usdc.map((v,i) => D.sc_total[i] ? v/D.sc_total[i]*100 : 0);
    let pOther = D.sc_others.map((v,i) => D.sc_total[i] ? v/D.sc_total[i]*100 : 0);
    traces = [
      {{ x: D.sc_dates, y: pUsdt, name: 'USDT %', stackgroup: 'one', fillcolor: 'rgba(0,162,189,0.6)', line: {{ width: 0 }} }},
      {{ x: D.sc_dates, y: pUsdc, name: 'USDC %', stackgroup: 'one', fillcolor: 'rgba(247,150,8,0.6)', line: {{ width: 0 }} }},
      {{ x: D.sc_dates, y: pOther, name: 'Others %', stackgroup: 'one', fillcolor: 'rgba(181,0,99,0.4)', line: {{ width: 0 }} }},
    ];
  }}
  let layout = {{...layoutBase, xaxis: {{...layoutBase.xaxis, rangeslider: {{ visible: true, bgcolor: '#f5f5f5', bordercolor: '#e0e0e0' }}, type: 'date', range: [scStart, D.sc_dates[0]]}}, yaxis: {{...layoutBase.yaxis}}}};
  Plotly.react('chart-sc-mcap', traces, layout, config);
}}
updateScChart('stacked');

// Pie chart
Plotly.newPlot('chart-sc-pie', [{{
  labels: D.stablecoin_overview.slice(0,10).map(s => s.symbol),
  values: D.stablecoin_overview.slice(0,10).map(s => s.circulating),
  type: 'pie', hole: 0.5, marker: {{ colors: colors }},
  textinfo: 'label+percent', textfont: {{ size: 11, color: '#333' }},
  hovertemplate: '%{{label}}<br>%{{value:$,.0f}}<br>%{{percent}}<extra></extra>'
}}], {{...layoutBase, margin: {{ l: 10, r: 10, t: 10, b: 10 }}, showlegend: false}}, config);

// Peg mechanism
Plotly.newPlot('chart-peg-mech', [{{
  labels: D.peg_mech.map(p => p[0]),
  values: D.peg_mech.map(p => p[1]),
  type: 'pie', hole: 0.45, marker: {{ colors: ['#00A2BD','#F79608','#B50063','#4A04A5'] }},
  textinfo: 'label+percent', textfont: {{ size: 12, color: '#333' }},
  hovertemplate: '%{{label}}<br>%{{value:$,.0f}}<extra></extra>'
}}], {{...layoutBase, margin: {{ l: 10, r: 10, t: 10, b: 10 }}, showlegend: false}}, config);

// Active addresses - STACKED BAR
Plotly.newPlot('chart-active-addr', [
  {{ x: D.aa_dates, y: D.aa_usdt, name: 'USDT', type: 'bar', marker: {{ color: '#00A2BD' }} }},
  {{ x: D.aa_dates, y: D.aa_usdc, name: 'USDC', type: 'bar', marker: {{ color: '#F79608' }} }},
], {{...layoutBase, barmode: 'stack', xaxis: {{...layoutBase.xaxis, type: 'date'}}}}, config);

// Transaction Volume Monthly - BAR CHART (if data available)
if (D.has_tvm) {{
  Plotly.newPlot('chart-tx-vol-monthly', [
    {{ x: D.tvm_months, y: D.tvm_usdt, name: 'USDT', type: 'bar', marker: {{ color: '#00A2BD' }} }},
    {{ x: D.tvm_months, y: D.tvm_usdc, name: 'USDC', type: 'bar', marker: {{ color: '#F79608' }} }},
  ], {{...layoutBase, barmode: 'stack', xaxis: {{...layoutBase.xaxis, type: 'date', dtick: 'M1', tickformat: '%b %Y'}}}}, config);
}} else {{
  document.querySelector('#chart-tx-vol-monthly').closest('.chart-card').style.display = 'none';
}}

// Stablecoin table
let tableHtml = '<table><thead><tr><th>#</th><th>Name</th><th>Symbol</th><th>Type</th><th>Circulating</th><th>Market Share</th><th>1D</th><th>1W</th><th>1M</th><th>Peg</th></tr></thead><tbody>';
D.stablecoin_overview.forEach((s, i) => {{
  tableHtml += `<tr><td>${{i+1}}</td><td>${{s.name}}</td><td>${{s.symbol}}</td><td>${{s.peg_mechanism || '-'}}</td><td>${{fmt(s.circulating)}}</td><td>${{(s.market_share*100).toFixed(2)}}%</td><td>${{pctFmt(s.change_1d)}}</td><td>${{pctFmt(s.change_1w)}}</td><td>${{pctFmt(s.change_1m)}}</td><td>${{s.peg ? s.peg.toFixed(4) : '-'}}</td></tr>`;
}});
tableHtml += '</tbody></table>';
document.getElementById('sc-table').innerHTML = tableHtml;

// --- DEFI & TVL ---
Plotly.newPlot('chart-total-tvl', [{{
  x: D.total_tvl_dates, y: D.total_tvl_vals, type: 'scatter', mode: 'lines',
  fill: 'tozeroy', fillcolor: 'rgba(0,162,189,0.12)', line: {{ color: '#00A2BD', width: 2 }},
  hovertemplate: '%{{x}}<br>TVL: %{{y:$,.0f}}<extra></extra>'
}}], {{...layoutBase, xaxis: {{...layoutBase.xaxis, rangeslider: {{ visible: true, bgcolor: '#f5f5f5' }}, type: 'date', range: [tvlTotalStart, D.total_tvl_dates[0]]}}}}, config);

function updateTvlChart(mode, btn) {{
  document.querySelector('#chart-tvl-chain').closest('.chart-card').querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  let chains = [
    {{ data: D.tvl_eth, name: 'Ethereum', color: colors[0] }},
    {{ data: D.tvl_sol, name: 'Solana', color: colors[1] }},
    {{ data: D.tvl_bsc, name: 'BSC', color: colors[2] }},
    {{ data: D.tvl_btc, name: 'Bitcoin', color: colors[3] }},
    {{ data: D.tvl_tron, name: 'Tron', color: colors[4] }},
    {{ data: D.tvl_base, name: 'Base', color: colors[5] }},
    {{ data: D.tvl_arb, name: 'Arbitrum', color: colors[6] }},
    {{ data: D.tvl_other, name: 'Other', color: colors[7] }},
  ];
  let traces;
  if (mode === 'stacked') {{
    traces = chains.map(c => ({{ x: D.tvl_dates, y: c.data, name: c.name, stackgroup: 'one', fillcolor: c.color + '88', line: {{ width: 0 }} }}));
  }} else if (mode === 'lines') {{
    traces = chains.map(c => ({{ x: D.tvl_dates, y: c.data, name: c.name, line: {{ color: c.color }} }}));
  }} else {{
    traces = chains.map(c => {{
      let pct = c.data.map((v,i) => D.tvl_total[i] ? (v||0)/D.tvl_total[i]*100 : 0);
      return {{ x: D.tvl_dates, y: pct, name: c.name, stackgroup: 'one', fillcolor: c.color + '88', line: {{ width: 0 }} }};
    }});
  }}
  Plotly.react('chart-tvl-chain', traces, {{...layoutBase, xaxis: {{...layoutBase.xaxis, rangeslider: {{ visible: true, bgcolor: '#f5f5f5' }}, type: 'date', range: [tvlChainStart, D.tvl_dates[0]]}}}}, config);
}}
updateTvlChart('stacked');


// --- FEES ---
Plotly.newPlot('chart-total-fees', [{{
  x: D.fee_dates, y: D.fee_total, type: 'scatter', mode: 'lines',
  fill: 'tozeroy', fillcolor: 'rgba(247,150,8,0.12)', line: {{ color: '#F79608', width: 2 }},
  hovertemplate: '%{{x}}<br>Fees: %{{y:$,.0f}}<extra></extra>'
}}], {{...layoutBase, xaxis: {{...layoutBase.xaxis, rangeslider: {{ visible: true, bgcolor: '#f5f5f5' }}, type: 'date', range: [feeTotalStart, D.fee_dates[0]]}}}}, config);

function updateFeeChart(mode, btn) {{
  document.querySelector('#chart-fees-chain').closest('.chart-card').querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  let chains = [
    {{ data: D.fee_eth, name: 'Ethereum', color: colors[0] }},
    {{ data: D.fee_sol, name: 'Solana', color: colors[1] }},
    {{ data: D.fee_bsc, name: 'BSC', color: colors[2] }},
    {{ data: D.fee_btc, name: 'Bitcoin', color: colors[3] }},
    {{ data: D.fee_tron, name: 'Tron', color: colors[4] }},
    {{ data: D.fee_base, name: 'Base', color: colors[5] }},
  ];
  let traces;
  if (mode === 'stacked') {{
    traces = chains.map(c => ({{ x: D.fee_dates, y: c.data, name: c.name, stackgroup: 'one', fillcolor: c.color + '88', line: {{ width: 0 }} }}));
  }} else {{
    traces = chains.map(c => ({{ x: D.fee_dates, y: c.data, name: c.name, line: {{ color: c.color }} }}));
  }}
  Plotly.react('chart-fees-chain', traces, {{...layoutBase, xaxis: {{...layoutBase.xaxis, rangeslider: {{ visible: true, bgcolor: '#f5f5f5' }}, type: 'date', range: [feeChainStart, D.fee_dates[0]]}}}}, config);
}}
updateFeeChart('stacked');

// Activity vs Token Price (Ethereum) - with USD/native toggle
let ethActStart = firstValidDate(D.fee_dates, D.fee_eth);
function updateActivityEth(mode, btn) {{
  document.querySelector('#chart-activity-eth').closest('.chart-card').querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  let feeData = mode === 'native' ? D.fee_eth_native : D.fee_eth;
  let feeLabel = mode === 'native' ? 'ETH Fees 7D Avg (ETH)' : 'ETH Fees 7D Avg (USD)';
  let feeAxisTitle = mode === 'native' ? 'Fees (ETH)' : 'Fees ($)';
  Plotly.react('chart-activity-eth', [
    {{ x: D.fee_dates, y: feeData, name: feeLabel, fill: 'tozeroy', fillcolor: 'rgba(0,162,189,0.12)', line: {{ color: '#00A2BD', width: 2 }}, yaxis: 'y' }},
    {{ x: D.fee_dates, y: D.fee_eth_price, name: 'ETH Price', line: {{ color: '#F79608', width: 2 }}, yaxis: 'y2' }},
  ], {{
    ...layoutBase,
    xaxis: {{...layoutBase.xaxis, rangeslider: {{ visible: true, bgcolor: '#f5f5f5' }}, type: 'date', range: [ethActStart, D.fee_dates[0]] }},
    yaxis: {{...layoutBase.yaxis, title: feeAxisTitle, titlefont: {{ color: '#00A2BD' }}, tickfont: {{ color: '#00A2BD' }} }},
    yaxis2: {{ title: 'ETH Price ($)', titlefont: {{ color: '#F79608' }}, tickfont: {{ color: '#F79608' }}, overlaying: 'y', side: 'right', gridcolor: 'transparent' }},
  }}, config);
}}
updateActivityEth('usd');

// Activity vs Token Price (Solana) - with USD/native toggle
let solActStart = firstValidDate(D.fee_dates, D.fee_sol);
function updateActivitySol(mode, btn) {{
  document.querySelector('#chart-activity-sol').closest('.chart-card').querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  let feeData = mode === 'native' ? D.fee_sol_native : D.fee_sol;
  let feeLabel = mode === 'native' ? 'SOL Fees 7D Avg (SOL)' : 'SOL Fees 7D Avg (USD)';
  let feeAxisTitle = mode === 'native' ? 'Fees (SOL)' : 'Fees ($)';
  Plotly.react('chart-activity-sol', [
    {{ x: D.fee_dates, y: feeData, name: feeLabel, fill: 'tozeroy', fillcolor: 'rgba(181,0,99,0.12)', line: {{ color: '#B50063', width: 2 }}, yaxis: 'y' }},
    {{ x: D.fee_dates, y: D.fee_sol_price, name: 'SOL Price', line: {{ color: '#ADBA00', width: 2 }}, yaxis: 'y2' }},
  ], {{
    ...layoutBase,
    xaxis: {{...layoutBase.xaxis, rangeslider: {{ visible: true, bgcolor: '#f5f5f5' }}, type: 'date', range: [solActStart, D.fee_dates[0]] }},
    yaxis: {{...layoutBase.yaxis, title: feeAxisTitle, titlefont: {{ color: '#B50063' }}, tickfont: {{ color: '#B50063' }}, range: [0, 60000000] }},
    yaxis2: {{ title: 'SOL Price ($)', titlefont: {{ color: '#ADBA00' }}, tickfont: {{ color: '#ADBA00' }}, overlaying: 'y', side: 'right', gridcolor: 'transparent' }},
  }}, config);
}}
updateActivitySol('usd');

// Activity vs Token Price (Bitcoin)
let btcActStart = firstValidDate(D.fee_dates, D.fee_btc);
Plotly.newPlot('chart-activity-btc', [
  {{ x: D.fee_dates, y: D.fee_btc, name: 'BTC Fees 7D Avg (USD)', fill: 'tozeroy', fillcolor: 'rgba(247,150,8,0.12)', line: {{ color: '#F79608', width: 2 }}, yaxis: 'y' }},
  {{ x: D.fee_dates, y: D.fee_btc_price, name: 'BTC Price', line: {{ color: '#4A04A5', width: 2 }}, yaxis: 'y2' }},
], {{
  ...layoutBase,
  xaxis: {{...layoutBase.xaxis, rangeslider: {{ visible: true, bgcolor: '#f5f5f5' }}, type: 'date', range: [btcActStart, D.fee_dates[0]] }},
  yaxis: {{...layoutBase.yaxis, title: 'Fees ($)', titlefont: {{ color: '#F79608' }}, tickfont: {{ color: '#F79608' }} }},
  yaxis2: {{ title: 'BTC Price ($)', titlefont: {{ color: '#4A04A5' }}, tickfont: {{ color: '#4A04A5' }}, overlaying: 'y', side: 'right', gridcolor: 'transparent' }},
}}, config);

// Transaction Volume Daily (if data available)
if (D.has_tvd) {{
  let txVolStart = firstValidDate(D.tvd_dates, D.tvd_usdt, D.tvd_usdc);
  function updateTxVolChart(mode, btn) {{
    document.querySelector('#chart-tx-vol').closest('.chart-card').querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    let coins = [
      {{ data: D.tvd_usdt, name: 'USDT', color: '#00A2BD' }},
      {{ data: D.tvd_usdc, name: 'USDC', color: '#F79608' }},
    ];
    let traces;
    if (mode === 'stacked') {{
      traces = coins.map(c => ({{ x: D.tvd_dates, y: c.data, name: c.name, stackgroup: 'one', fillcolor: c.color + '88', line: {{ width: 0 }} }}));
    }} else {{
      traces = coins.map(c => ({{ x: D.tvd_dates, y: c.data, name: c.name, line: {{ color: c.color }} }}));
    }}
    Plotly.react('chart-tx-vol', traces, {{...layoutBase, xaxis: {{...layoutBase.xaxis, rangeslider: {{ visible: true, bgcolor: '#f5f5f5' }}, type: 'date', range: [txVolStart, D.tvd_dates[0]]}}}}, config);
  }}
  updateTxVolChart('stacked');

  // Transaction Volume vs Token Prices (BTC/ETH/SOL toggle)
  let txVolDataStart = firstValidDate(D.tvd_dates, D.tvd_total_7d);
  function updateTxVsPrice(mode, btn) {{
    document.querySelector('#chart-tx-vs-btc').closest('.chart-card').querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    let priceDates, priceData, priceName, priceColor, priceAxisTitle;
    if (mode === 'eth') {{
      priceDates = D.tvd_dates; priceData = D.tvd_eth_price;
      priceName = 'Ethereum Price'; priceColor = '#00A2BD'; priceAxisTitle = 'ETH Price ($)';
    }} else if (mode === 'sol') {{
      priceDates = D.tvd_dates; priceData = D.tvd_sol_price;
      priceName = 'Solana Price'; priceColor = '#B50063'; priceAxisTitle = 'SOL Price ($)';
    }} else {{
      priceDates = D.tvd_dates; priceData = D.tvd_btc_price;
      priceName = 'Bitcoin Price'; priceColor = '#F79608'; priceAxisTitle = 'BTC Price ($)';
    }}
    Plotly.react('chart-tx-vs-btc', [
      {{ x: D.tvd_dates, y: D.tvd_total_7d, name: 'Stablecoin Volume 7D Avg', fill: 'tozeroy', fillcolor: 'rgba(0,162,189,0.12)', line: {{ color: '#00A2BD', width: 2 }}, yaxis: 'y', connectgaps: true }},
      {{ x: priceDates, y: priceData, name: priceName, line: {{ color: priceColor, width: 2 }}, yaxis: 'y2', connectgaps: true }},
    ], {{
      ...layoutBase,
      xaxis: {{...layoutBase.xaxis, rangeslider: {{ visible: true, bgcolor: '#f5f5f5' }}, type: 'date', range: [txVolDataStart, D.tvd_dates[0]]}},
      yaxis: {{...layoutBase.yaxis, title: 'Volume ($)', titlefont: {{ color: '#00A2BD' }}, tickfont: {{ color: '#00A2BD' }} }},
      yaxis2: {{ title: priceAxisTitle, titlefont: {{ color: priceColor }}, tickfont: {{ color: priceColor }}, overlaying: 'y', side: 'right', gridcolor: 'transparent' }},
    }}, config);
  }}
  updateTxVsPrice('btc');
}} else {{
  let txEl = document.querySelector('#chart-tx-vol');
  if (txEl) txEl.closest('.chart-card').style.display = 'none';
  let txBtcEl = document.querySelector('#chart-tx-vs-btc');
  if (txBtcEl) txBtcEl.closest('.chart-card').style.display = 'none';
}}

// --- PROTOCOLS ---

// Protocol table
let ptHtml = '<table><thead><tr><th>#</th><th>Name</th><th>Category</th><th>Chain</th><th>TVL</th><th>1D Change</th><th>7D Change</th></tr></thead><tbody>';
D.top_protocols.forEach((p, i) => {{
  ptHtml += `<tr><td>${{i+1}}</td><td>${{p.name}}</td><td>${{p.category}}</td><td>${{p.chain}}</td><td>${{fmt(p.tvl)}}</td><td>${{pctFmt(p.change_1d ? p.change_1d/100 : null)}}</td><td>${{pctFmt(p.change_7d ? p.change_7d/100 : null)}}</td></tr>`;
}});
ptHtml += '</tbody></table>';
document.getElementById('proto-table').innerHTML = ptHtml;

// --- INSIGHTS ---
function updateCorrChart(mode, btn) {{
  document.querySelector('#chart-correlation').closest('.chart-card').querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  let traces = [];
  if (mode === 'tether' || mode === 'all') {{
    traces.push({{ x: D.corr_dates, y: D.corr_tether_eth, name: 'USDT vs ETH', line: {{ color: '#00A2BD' }}, connectgaps: true }});
    traces.push({{ x: D.corr_dates, y: D.corr_tether_btc, name: 'USDT vs BTC', line: {{ color: '#B50063' }}, connectgaps: true }});
  }}
  if (mode === 'usdc' || mode === 'all') {{
    traces.push({{ x: D.corr_dates, y: D.corr_usdc_eth, name: 'USDC vs ETH', line: {{ color: '#F79608' }}, connectgaps: true }});
    traces.push({{ x: D.corr_dates, y: D.corr_usdc_btc, name: 'USDC vs BTC', line: {{ color: '#ADBA00' }}, connectgaps: true }});
  }}
  let corrStart = firstValidDate(D.corr_dates, D.corr_tether_eth, D.corr_tether_btc, D.corr_usdc_eth, D.corr_usdc_btc);
  let layout = {{...layoutBase,
    xaxis: {{...layoutBase.xaxis, type: 'date', range: [corrStart, D.corr_dates[0]], rangeslider: {{ visible: true, bgcolor: '#f5f5f5' }} }},
    shapes: [{{ type: 'line', x0: corrStart, x1: D.corr_dates[0], y0: 0, y1: 0, line: {{ color: '#ccc', dash: 'dash', width: 1 }} }}]
  }};
  Plotly.react('chart-correlation', traces, layout, config);
}}
updateCorrChart('tether');

// Bitcoin Price vs Stablecoin Market Cap (with toggle)
function updatePriceChart(mode, btn) {{
  document.querySelector('#chart-prices').closest('.chart-card').querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  let btcMcapStart = firstValidDate(D.corr_dates, D.btc_price, D.corr_tether_mcap, D.corr_usdc_mcap);
  let traces = [
    {{ x: D.corr_dates, y: D.btc_price, name: 'Bitcoin Price', line: {{ color: '#F79608', width: 2 }}, yaxis: 'y' }},
  ];
  if (mode === 'usdt' || mode === 'both') {{
    traces.push({{ x: D.corr_dates, y: D.corr_tether_mcap, name: 'USDT Market Cap', line: {{ color: '#00A2BD', width: 2 }}, yaxis: 'y2' }});
  }}
  if (mode === 'usdc' || mode === 'both') {{
    traces.push({{ x: D.corr_dates, y: D.corr_usdc_mcap, name: 'USDC Market Cap', line: {{ color: '#B50063', width: 2 }}, yaxis: 'y2' }});
  }}
  Plotly.react('chart-prices', traces, {{
    ...layoutBase,
    xaxis: {{...layoutBase.xaxis, type: 'date', range: [btcMcapStart, D.corr_dates[0]], rangeslider: {{ visible: true, bgcolor: '#f5f5f5' }} }},
    yaxis: {{...layoutBase.yaxis, title: 'BTC Price ($)', titlefont: {{ color: '#F79608' }}, tickfont: {{ color: '#F79608' }} }},
    yaxis2: {{ title: 'Market Cap ($)', titlefont: {{ color: '#00A2BD' }}, tickfont: {{ color: '#00A2BD' }}, overlaying: 'y', side: 'right', gridcolor: 'transparent' }},
  }}, config);
}}
updatePriceChart('usdt');


// Fee Efficiency by Chain (if data available)
if (D.has_fe) {{
  let feTraces = [];
  let feChainNames = Object.keys(D.fe_eff);
  feChainNames.forEach((chain, idx) => {{
    let vals = D.fe_eff[chain].map(v => (v != null && typeof v === 'number') ? v * 100 : null);
    feTraces.push({{
      x: D.fe_months, y: vals, name: chain,
      line: {{ color: colors[idx % colors.length], width: 2 }},
      connectgaps: true,
      hovertemplate: '%{{x}}<br>' + chain + ': %{{y:.3f}}%<extra></extra>'
    }});
  }});
  let feTotalVals = D.fe_eff_total.map(v => (v != null && typeof v === 'number') ? v * 100 : null);
  feTraces.push({{
    x: D.fe_months, y: feTotalVals, name: 'All Chains',
    line: {{ color: '#333', width: 2, dash: 'dot' }},
    connectgaps: true,
  }});
  let feAllArrays = Object.values(D.fe_eff);
  let feEffStart = firstValidDate(D.fe_months, ...feAllArrays);
  Plotly.newPlot('chart-efficiency', feTraces, {{
    ...layoutBase,
    xaxis: {{...layoutBase.xaxis, type: 'date', rangeslider: {{ visible: true, bgcolor: '#f5f5f5' }}, range: [feEffStart, D.fe_months[0]] }},
    yaxis: {{...layoutBase.yaxis, title: 'Fees / TVL (%)' }},
    margin: {{ l: 60, r: 20, t: 10, b: 40 }},
  }}, config);
}} else {{
  // Fallback: compute efficiency from latest fee/TVL data
  let chainNames = ['Ethereum', 'Solana', 'BSC', 'Bitcoin', 'Tron', 'Base'];
  let latestTvl = [D.tvl_eth[0], D.tvl_sol[0], D.tvl_bsc[0], D.tvl_btc[0], D.tvl_tron[0], D.tvl_base[0]];
  let latestFees = [D.fee_eth[0], D.fee_sol[0], D.fee_bsc[0], D.fee_btc[0], D.fee_tron[0], D.fee_base[0]];
  let annFees = latestFees.map(f => (f || 0) * 365);
  let efficiency = latestTvl.map((t, i) => t && annFees[i] ? (annFees[i] / t * 100) : 0);
  Plotly.newPlot('chart-efficiency', [{{
    x: chainNames, y: efficiency, type: 'bar',
    marker: {{ color: colors.slice(0, 6) }},
    text: efficiency.map(e => e.toFixed(2) + '%'),
    textposition: 'outside', textfont: {{ size: 11 }},
    hovertemplate: '%{{x}}<br>Annualized Fees/TVL: %{{y:.3f}}%<extra></extra>'
  }}], {{
    ...layoutBase,
    yaxis: {{...layoutBase.yaxis, title: 'Annualized Fees / TVL (%)' }},
    margin: {{ l: 50, r: 20, t: 10, b: 60 }},
  }}, config);
}}

</script>
</body>
</html>"""

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print("Dashboard generated successfully!")
print(f"File size: {len(html):,} bytes")
