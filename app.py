import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. Konfigurasi Halaman & UI Clean
st.set_page_config(page_title="Growth Blueprint V4", layout="wide")

# CSS Khusus untuk memanipulasi tampilan (Kapital, Hapus Spin Button, Margin)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Mematikan tombol plus-minus (-+) pada input angka */
    input::-webkit-outer-spin-button,
    input::-webkit-inner-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }
    input[type=number] {
        -moz-appearance: textfield;
    }
    
    /* Memaksa input teks selalu huruf kapital di layar */
    input[type=text] {
        text-transform: uppercase;
    }

    .main-title {
        font-size: 24px !important;
        font-weight: bold;
        margin-bottom: 15px;
    }
    .col-header {
        font-size: 13px;
        font-weight: bold;
        color: #888888;
        margin-bottom: 0px;
    }
    .ref-text {
        font-size: 14px;
        color: #888888;
        margin-top: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# PERBAIKAN 7: Menambahkan ikon grafik di depan judul
st.markdown('<p class="main-title">📈 Maximum Growth Blueprint: AI-Energy Nexus</p>', unsafe_allow_html=True)

# --- MANAJEMEN STATE UNTUK TOMBOL TAMBAH ASET ---
if 'num_assets' not in st.session_state:
    st.session_state.num_assets = 3 # PERBAIKAN 2: Munculkan 3 default di awal

# 2. Panel Input Samping
st.sidebar.header("Konfigurasi Portofolio")
capital_base = st.sidebar.number_input("Modal Awal (Basis)", value=65.0, label_visibility="visible")
capital_target = st.sidebar.number_input("Target Capital Gain", value=100.0, label_visibility="visible")
benchmark_ticker = st.sidebar.text_input("Benchmark", value="SPY").upper()

st.sidebar.markdown("---")

# PERBAIKAN 1: Judul baru & Tombol Tambah Aset berbentuk kotak kecil di kiri
st.sidebar.markdown('<p style="font-size: 16px; font-weight: bold; margin-bottom: 5px;">Aset & Alokasi</p>', unsafe_allow_html=True)
col_btn, _ = st.sidebar.columns([1, 1]) # Membuat tombol setengah ukuran di kiri
with col_btn:
    if st.button("➕ Tambah Aset", use_container_width=True):
        st.session_state.num_assets += 1

# PERBAIKAN 4: Title Sejajar Satu Baris (Nama Aset | Alokasi | Reff)
h1, h2, h3 = st.sidebar.columns([2, 1.2, 1])
h1.markdown('<p class="col-header">Nama Aset</p>', unsafe_allow_html=True)
h2.markdown('<p class="col-header">Alokasi(%)</p>', unsafe_allow_html=True)
h3.markdown('<p class="col-header">Reff</p>', unsafe_allow_html=True)

assets = []
weights = []
defaults = ["NVDA", "VST", "PLTR", "GLD", "BTC", "TSM", "AMD"]

# Logic Bobot Referensi
def get_ref_weight(index, total):
    decay = 0.7 ** index
    raw_weights = [0.7 ** i for i in range(total)]
    return round((decay / sum(raw_weights)) * 100, 1)

# PERBAIKAN 2: Menampilkan 3 aset pertama, sisanya di dropdown
for i in range(st.session_state.num_assets):
    ref_w = get_ref_weight(i, st.session_state.num_assets)
    default_val = defaults[i] if i < len(defaults) else ""
    
    # Pisahkan lokasi penempatan (Langsung vs Expander/Dropdown)
    if i < 3:
        container = st.sidebar
    else:
        if i == 3:
            expander = st.sidebar.expander("⬇️ Tampilkan Aset Tambahan", expanded=False)
        container = expander
        
    col_a, col_w, col_r = container.columns([2, 1.2, 1])
    
    with col_a:
        # PERBAIKAN 5: Huruf kapital ditangani oleh CSS dan backend .upper()
        # label_visibility="collapsed" membuat tampilan menjadi kotak rapi tanpa teks label
        t = st.text_input(f"t{i}", value=default_val, key=f"t_{i}", label_visibility="collapsed").upper()
    with col_w:
        # PERBAIKAN 3: Tanda (-+) dihilangkan otomatis lewat CSS di atas
        w = st.number_input(f"w{i}", value=float(ref_w), key=f"w_{i}", label_visibility="collapsed")
    with col_r:
        st.markdown(f"<p class='ref-text'>{ref_w}%</p>", unsafe_allow_html=True)
        
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

    fig.update_layout(
        height=450, 
        template="plotly_dark", 
        margin=dict(l=10, r=10, t=10, b=10),
        hovermode=False, 
        xaxis=dict(showgrid=False, fixedrange=True),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', fixedrange=True),
        legend=dict(orientation="h", y=1.1, x=0)
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False, 'staticPlot': True})
else:
    st.warning("Menunggu input ticker yang valid...")
