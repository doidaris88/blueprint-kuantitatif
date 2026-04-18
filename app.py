import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. Konfigurasi Halaman & UI Clean
st.set_page_config(page_title="Growth Blueprint V9", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    input[type=text] {
        text-transform: uppercase;
    }

    .main-title {
        font-size: 36px !important; 
        font-weight: bold;
        margin-bottom: 20px;
        letter-spacing: -0.5px;
    }
    .locked-weight {
        background-color: #1e2130;
        padding: 8px 10px;
        border-radius: 5px;
        font-size: 15px;
        color: #00FFCC;
        text-align: center;
        border: 1px solid #333333;
        margin-top: 2px;
    }
    .stButton>button {
        padding: 2px 5px;
        font-size: 12px;
        height: 32px;
    }
    /* GAYA BARU UNTUK CATATAN KECIL */
    .catatan-kecil {
        font-size: 12px;
        color: #888888;
        margin-top: -12px;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">📈 Maximum Growth Blueprint: AI-Energy Nexus</p>', unsafe_allow_html=True)

if 'num_assets' not in st.session_state:
    st.session_state.num_assets = 3 

# 2. Panel Input Samping
st.sidebar.header("Konfigurasi Portofolio")
capital_base = st.sidebar.number_input("Modal Awal (Basis)", value=65.0)
capital_target = st.sidebar.number_input("Target Capital Gain", value=100.0)
benchmark_ticker = st.sidebar.text_input("Benchmark", value="SPY").upper()

st.sidebar.markdown("---")
st.sidebar.header("Aset & Alokasi Sistem")

with st.sidebar.expander("⚙️ Pengaturan Aset", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ Tambah"):
            st.session_state.num_assets += 1
    with c2:
        if st.button("➖ Hapus"):
            if st.session_state.num_assets > 1:
                st.session_state.num_assets -= 1
    
    if st.button("💾 Simpan Urutan", use_container_width=True):
        st.success("Tersimpan!")

assets = []
weights = []
defaults = ["NVDA", "VST", "PLTR", "GLD", "BTC", "TSM", "AMD"]

def get_ref_weight(index, total):
    decay = 0.7 ** index
    raw_weights = [0.7 ** i for i in range(total)]
    return round((decay / sum(raw_weights)) * 100, 1)

for i in range(st.session_state.num_assets):
    ref_w = get_ref_weight(i, st.session_state.num_assets)
    default_val = defaults[i] if i < len(defaults) else ""
    
    if i < 3:
        container = st.sidebar
    else:
        if i == 3:
            expander = st.sidebar.expander("⬇️ Aset Tambahan", expanded=False)
        container = expander
        
    col_a, col_w = container.columns([2, 1.5])
    with col_a:
        t = st.text_input(f"t{i}", value=default_val, key=f"t_{i}", label_visibility="collapsed").upper()
    with col_w:
        st.markdown(f"<div class='locked-weight'>{ref_w}% 🔒</div>", unsafe_allow_html=True)
        
    if t:
        assets.append(t)
        weights.append(ref_w)

weights_norm = np.array(weights) / 100 if sum(weights) > 0 else np.array(weights)

# 3. Pengambilan Data & Komputasi
@st.cache_data(ttl=3600)
def get_data(tickers, benchmark):
    valid_tickers = [t for t in tickers if t]
    all_tickers = list(set(valid_tickers + [benchmark]))
    try:
        data = yf.download(all_tickers, period="3y", progress=False)['Close']
        return data
    except:
        return pd.DataFrame()

data = get_data(assets, benchmark_ticker)

if not data.empty and all(a in data.columns for a in assets):
    returns = data.pct_change().dropna()
    port_returns = returns[assets].dot(weights_norm)
    bench_returns = returns[benchmark_ticker]

    port_cum = (1 + port_returns).cumprod() * capital_base
    bench_cum = (1 + bench_returns).cumprod() * capital_base
    
    roll_max = port_cum.cummax()
    drawdown = (port_cum / roll_max) - 1
    max_dd = drawdown.min()
    
    curr_val = port_cum.iloc[-1]
    sharpe = ((port_returns.mean() - (0.04/252)) / port_returns.std()) * np.sqrt(252)
    alpha = (port_returns.mean() * 252) - (0.04 + (port_returns.cov(bench_returns)/bench_returns.var()) * ((bench_returns.mean() * 252) - 0.04))
    alpha_pct = alpha * 100

    # 4. LOGIKA ATURAN BAKU (CATATAN KECIL)
    # Sharpe Note
    if sharpe < 1.0:
        note_sharpe = "Sedang (< 1.0)"
    elif sharpe <= 1.5:
        note_sharpe = "Baik (1.0 - 1.5)"
    else:
        note_sharpe = "Bagus (> 1.5)"

    # Alpha Note
    if alpha_pct < 0:
        note_alpha = "Kurang (< 0%)"
    elif alpha_pct <= 5.0:
        note_alpha = "Normal (0 - 5%)"
    else:
        note_alpha = "Bagus (> 5%)"

    # Drawdown Note
    if max_dd >= -0.15:
        note_dd = "Normal (0% s.d -15%)"
    elif max_dd >= -0.30:
        note_dd = "Medium (-15% s.d -30%)"
    else:
        note_dd = "Ekstrem (< -30%)"

    # 5. Tampilan Dasbor
    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    
    m1.metric("Nilai Portofolio", f"${curr_val:.2f}", f"Target: ${capital_target}")
    
    m2.metric("Sharpe Ratio", f"{sharpe:.2f}")
    m2.markdown(f"<p class='catatan-kecil'>Skor: {note_sharpe}</p>", unsafe_allow_html=True)
    
    m3.metric("Alpha", f"{alpha_pct:.1f}%")
    m3.markdown(f"<p class='catatan-kecil'>Kategori: {note_alpha}</p>", unsafe_allow_html=True)
    
    m4.metric("Max Drawdown", f"{max_dd*100:.2f}%")
    m4.markdown(f"<p class='catatan-kecil'>Risiko: {note_dd}</p>", unsafe_allow_html=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Kurva Ekuitas vs Benchmark")
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=port_cum.index, y=port_cum, name='Portofolio', line=dict(color='#00FFCC', width=2)))
        fig1.add_trace(go.Scatter(x=bench_cum.index, y=bench_cum, name='Benchmark', line=dict(color='#666666', width=1)))
        fig1.add_hline(y=capital_target, line_dash="dot", line_color="#FF4B4B")
        fig1.update_layout(height=350, template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10),
                          hovermode=False, xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True),
                          legend=dict(orientation="h", y=1.1, x=0))
        st.plotly_chart(fig1, use_container_width=True, config={'staticPlot': True})

    with c2:
        st.subheader("Peta Drawdown")
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=drawdown.index, y=drawdown, fill='tozeroy', line=dict(color='#ff4444', width=1)))
        fig2.update_layout(height=350, template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10),
                          hovermode=False, xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True, tickformat='.1%'))
        st.plotly_chart(fig2, use_container_width=True, config={'staticPlot': True})
else:
    st.warning("Menunggu input ticker yang valid...")
