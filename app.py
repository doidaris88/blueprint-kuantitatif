import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. Konfigurasi Halaman & UI Clean
st.set_page_config(page_title="Growth Blueprint V3", layout="wide")

# PERBAIKAN 1 & 2: Header dimunculkan untuk tombol sidebar, warna judul disesuaikan otomatis
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .main-title {
        font-size: 22px !important;
        font-weight: bold;
        margin-bottom: 15px;
    }
    .ref-text {
        font-size: 12px;
        color: #888888;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">Maximum Growth Blueprint: AI-Energy Nexus</p>', unsafe_allow_html=True)

# 2. Panel Input Samping
st.sidebar.header("Konfigurasi Portofolio")
capital_base = st.sidebar.number_input("Modal Awal (Basis)", value=65.0, step=1.0)
capital_target = st.sidebar.number_input("Target Capital Gain", value=100.0, step=1.0)
benchmark_ticker = st.sidebar.text_input("Benchmark", value="SPY").upper()

st.sidebar.markdown("---")
num_assets = st.sidebar.number_input("Jumlah Aset", min_value=1, max_value=15, value=5)

assets = []
weights = []

# Logic Bobot Referensi (Strategi Aggressive Growth)
def get_ref_weight(index, total):
    if total == 5:
        return [35.0, 25.0, 20.0, 10.0, 10.0][index]
    else:
        decay = 0.7 ** index
        raw_weights = [0.7 ** i for i in range(total)]
        return round((decay / sum(raw_weights)) * 100, 1)

defaults = ["NVDA", "VST", "PLTR", "GLD", "BTC"]

for i in range(num_assets):
    ref_w = get_ref_weight(i, num_assets)
    col_a, col_w, col_r = st.sidebar.columns([2, 1, 1])
    
    with col_a:
        default_val = defaults[i] if i < len(defaults) else ""
        t = st.text_input(f"Ticker {i+1}", value=default_val, key=f"t{i}").upper()
    with col_w:
        w = st.number_input(f"% {i+1}", value=ref_w, step=1.0, key=f"w{i}")
    with col_r:
        st.markdown(f"<p class='ref-text'>Ref:<br>{ref_w}%</p>", unsafe_allow_html=True)
        
    if t:
        assets.append(t)
        weights.append(w)

weights_norm = np.array(weights) / 100 if sum(weights) > 0 else np.array(weights)

# 3. Pengambilan Data & Validasi
@st.cache_data(ttl=3600)
def get_data(tickers, benchmark):
    valid_tickers = [t for t in tickers if t]
    all_tickers = list(set(valid_tickers + [benchmark]))
    try:
        data = yf.download(all_tickers, period="3y", progress=False)['Close']
        return data
    except Exception as e:
        return pd.DataFrame()

data = get_data(assets, benchmark_ticker)

if not data.empty and all(a in data.columns for a in assets):
    returns = data.pct_change().dropna()
    port_returns = returns[assets].dot(weights_norm)
    bench_returns = returns[benchmark_ticker]

    port_cum_returns = (1 + port_returns).cumprod() * capital_base
    bench_cum_returns = (1 + bench_returns).cumprod() * capital_base

    current_value = port_cum_returns.iloc[-1]
    years_data = len(port_returns) / 252
    cagr = ((current_value / capital_base) ** (1 / years_data)) - 1

    if cagr > 0 and current_value < capital_target:
        time_to_target = np.log(capital_target / current_value) / np.log(1 + cagr)
        time_str = f"{time_to_target:.1f} Tahun"
    elif current_value >= capital_target:
        time_str = "Tercapai"
    else:
        time_str = "N/A"

    risk_free = 0.04 / 252
    sharpe = ((port_returns.mean() - risk_free) / port_returns.std()) * np.sqrt(252)
    beta = port_returns.cov(bench_returns) / bench_returns.var()
    alpha = (port_returns.mean() * 252) - (0.04 + beta * ((bench_returns.mean() * 252) - 0.04))

    # 4. Tampilan Dasbor
    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    
    # PERBAIKAN 3: Menambahkan kembali tulisan target hijau
    m1.metric("Nilai Portofolio", f"${current_value:.2f}", f"Target: ${capital_target}")
    m2.metric("Sharpe Ratio", f"{sharpe:.2f}")
    m3.metric("Alpha", f"{alpha*100:.1f}%")
    m4.metric("Estimasi Waktu", time_str)

    st.markdown("---")
    
    st.subheader("Visualisasi Pertumbuhan Portofolio")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=port_cum_returns.index, y=port_cum_returns, name='Portofolio', line=dict(color='#00FFCC', width=2)))
    fig.add_trace(go.Scatter(x=bench_cum_returns.index, y=bench_cum_returns, name='Benchmark', line=dict(color='#666666', width=1)))
    fig.add_hline(y=capital_target, line_dash="dot", line_color="#FF4B4B")

    # PERBAIKAN 4: Mengunci mati grafik agar tidak bisa disentuh/di-zoom
    fig.update_layout(
        height=450, 
        template="plotly_dark", 
        margin=dict(l=10, r=10, t=10, b=10),
        hovermode=False, 
        xaxis=dict(showgrid=False, fixedrange=True), # fixedrange mengunci axis X
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', fixedrange=True), # fixedrange mengunci axis Y
        legend=dict(orientation="h", y=1.1, x=0)
    )
    
    # Perintah 'staticPlot': True akan mematikan semua fungsi interaktif layar sentuh
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
else:
    st.warning("Menunggu input ticker yang valid...")
