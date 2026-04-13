import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import numpy as np

# ==================== CONFIG ====================
st.set_page_config(page_title="Aktien-Tool Bäumer", layout="wide")

# ==================== CACHE ====================
@st.cache_data
def load_data(ticker):
    stock = yf.Ticker(ticker)
    try:
        info = stock.get_info()
    except:
        info = {}
    hist = stock.history(period="5y")
    return info, hist

# ==================== HELPER ====================
def get_color(value, good, ok):
    if value is None:
        return "⚪"
    if value >= good:
        return "🟢"
    elif value >= ok:
        return "🟡"
    else:
        return "🔴"

def get_color_inverse(value, good, ok):
    if value is None or value == 0:
        return "⚪"
    if value <= good:
        return "🟢"
    elif value <= ok:
        return "🟡"
    else:
        return "🔴"

# ==================== SESSION ====================
if "ticker" not in st.session_state:
    st.session_state["ticker"] = "AAPL"

# ==================== SIDEBAR ====================
with st.sidebar:
    ticker_input = st.text_input("Ticker", value=st.session_state["ticker"]).upper().strip()
    st.session_state["ticker"] = ticker_input

    st.divider()
    st.markdown("### ⚡ Schnellzugriff")

    tech = ["MSFT","AAPL","NVDA","GOOGL","META","AMZN"]
    growth = ["TSLA","SHOP","SNOW","CRWD","DDOG","NET"]
    value = ["BRK-B","JNJ","PG","KO","PEP","MCD"]
    finance = ["JPM","BAC","GS","MS","V","MA"]

    category = st.selectbox("Kategorie", ["Tech","Growth","Value","Finance"])
    tickers = {"Tech":tech,"Growth":growth,"Value":value,"Finance":finance}[category]

    cols = st.columns(3)
    for i,t in enumerate(tickers):
        if cols[i%3].button(t):
            st.session_state["ticker"] = t
            st.rerun()

    st.divider()
    st.markdown("### 🧠 Smart Presets")

    presets = {
        "High Growth": ["NVDA","TSLA","SNOW","CRWD"],
        "High FCF": ["AAPL","MSFT","GOOGL","META"],
        "Low Risk": ["JNJ","PG","KO","PEP"],
    }

    preset_choice = st.selectbox("Preset", list(presets.keys()))

    for t in presets[preset_choice]:
        if st.button(f"⭐ {t}"):
            st.session_state["ticker"] = t
            st.rerun()

# ==================== MAIN ====================
ticker = st.session_state["ticker"]
info, hist = load_data(ticker)

if hist.empty:
    st.error("Keine Daten")
    st.stop()

price = hist['Close'].iloc[-1]
fcf = info.get('freeCashflow')
market_cap = info.get('marketCap')
fcf_yield = (fcf/market_cap*100) if fcf and market_cap else 0
rev_growth = (info.get('revenueGrowth') or 0)*100
rule_of_40 = rev_growth + fcf_yield
gross_margin = (info.get('grossMargins') or 0)*100
pe = info.get('forwardPE') or info.get('trailingPE') or 0
debt = info.get('debtToEquity') or 0
beta = info.get('beta') or 1
roic = info.get("returnOnInvestedCapital")
roic_val = roic*100 if roic else None

st.title(f"{ticker} Dashboard")
st.metric("Kurs", f"${price:.2f}")

# ==================== CHART ====================
hist['log'] = np.log(hist['Close'])
x = np.arange(len(hist))
trend = np.exp(np.poly1d(np.polyfit(x,hist['log'],1))(x))

fig = go.Figure()
fig.add_trace(go.Scatter(x=hist.index,y=hist['Close'],name="Kurs"))
fig.add_trace(go.Scatter(x=hist.index,y=trend,name="Trend"))
st.plotly_chart(fig,use_container_width=True)

# ==================== METRICS ====================
st.markdown("## 📊 Kennzahlen")
c1,c2,c3,c4 = st.columns(4)

c1.metric(f"{get_color(rule_of_40,40,20)} Rule of 40",f"{rule_of_40:.1f}%")
c2.metric(f"{get_color(fcf_yield,5,2)} FCF Yield",f"{fcf_yield:.1f}%")
c3.metric(f"{get_color(gross_margin,60,40)} Margin",f"{gross_margin:.1f}%")
c4.metric(f"{get_color(roic_val,20,10)} ROIC",f"{roic_val:.1f}%" if roic_val else "N/A")

st.markdown("## ⚖️ Bewertung & Risiko")
c1,c2,c3 = st.columns(3)

c1.metric(f"{get_color_inverse(pe,25,40)} P/E",f"{pe:.1f}")
c2.metric(f"{get_color_inverse(debt,1,2)} Debt",f"{debt:.2f}")
c3.metric(f"{get_color_inverse(beta,1.2,1.6)} Beta",f"{beta:.2f}")

# ==================== SCANNER ====================
st.markdown("## 🚀 Mini Scanner")

scan_list = ["AAPL","MSFT","NVDA","GOOGL","META","AMZN","TSLA","JNJ"]
results = []

for t in scan_list:
    i,_ = load_data(t)
    try:
        fcf = i.get('freeCashflow')
        mc = i.get('marketCap')
        fy = (fcf/mc*100) if fcf and mc else 0
        rg = (i.get('revenueGrowth') or 0)*100
        r40 = rg + fy
        results.append((t,r40))
    except:
        pass

results = sorted(results,key=lambda x:x[1],reverse=True)

for t,val in results:
    st.write(f"{t} → {val:.1f}%")
