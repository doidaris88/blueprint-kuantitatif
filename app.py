import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. Konfigurasi Halaman & UI (Putih Bersih)
st.set_page_config(page_title="Growth Blueprint V14", layout="wide")

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
        margin-bottom: 25px;
        letter-spacing: -1px;
        color: #111111;
    }

    .locked-weight {
        background-color: #f8f9fa;
        padding: 8px 10px;
        border-radius: 6px;
        font-size: 15px;
        font-weight: bold;
        color: #0088ff;
        text-align: center;
        border: 1px solid #eeeeee;
        margin-top: 2px;
    }

    input::-webkit-outer-spin-button,
    input::-webkit-inner-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">📈 Maximum Growth Blueprint: AI-Energy</p>', unsafe_allow_html=True)

if 'num_assets' not in st.session_state:
    st.session_state.num_assets = 3 

# 2. Sidebar (Pengaturan Aset)
st.sidebar.header("Konfigurasi Portofolio")
cap_base = st.sidebar.number_input("Modal Awal (Basis)", value=65.0)
cap_target = st.sidebar.number_input("Target Capital Gain", value=100.0)
bench_ticker = st.sidebar.text_input("Benchmark", value="SPY").upper()

st.sidebar.markdown("---")
st.sidebar.header("Aset & Alokasi Sistem")

with st.sidebar.expander("⚙️ Pengaturan Aset", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ Tambah"): st.session_state.num_assets += 1
    with c2:
        if st.button("➖ Hapus"):
            if st.session_state.num_assets > 1: st.session_state.num_assets -= 1
    
    if st.button("💾 SAVE", use_container_width=True):
        st.success("Urutan Tersimpan")

assets = []
weights = []
defaults = ["NVDA", "VST", "PLTR", "GLD", "BTC", "TSM", "AMD"]

def get_ref_weight(index, total):
    decay = 0.7 ** index
    raw_weights = [0.7 ** i for i in range(total)]
    return round((decay / sum(raw_weights)) * 100, 1)

# PERBAIKAN 2: Expander Aset Tambahan hanya dibuat satu kali
expander_tambahan = st.sidebar.expander("⬇️ Aset Tambahan", expanded=False) if st.session_state.num_assets > 3 else None

for i in range(st.session_state.num_assets):
    ref_w = get_ref_weight(i, st.session_state.num_assets)
    def_val = defaults[i] if i < len(defaults) else ""
    
    container = st.sidebar if i < 3 else expander_tambahan
    
    col_a, col_w = container.columns([2, 1.5])
    with col_a:
        t = st.text_input(f"t{i}", value=def_val, key=f"t_{i}", label_visibility="collapsed").upper()
    with col_w:
        st.markdown(f"<div class='locked-weight'>{ref_w}% 🔒</div>", unsafe_allow_html=True)
    if t:
        assets.append(t)
        weights.append(ref_w)

# 3. Komputasi Data
@st.cache_data(ttl=3600)
def fetch_data(tickers, benchmark):
    all_t = list(set([t for t in tickers if t] + [benchmark]))
    try:
        # PERBAIKAN 1: ffill() untuk menambal data kosong agar grafik S&P (SPY) tidak hilang
        df = yf.download(all_t, period="3y", progress=False)['Close']
        df = df.ffill().dropna() 
        return df
    except:
        return pd.DataFrame()

df = fetch_data(assets, bench_ticker)

if not df.empty and all(a in df.columns for a in assets) and bench_ticker in df.columns:
    rets = df.pct_change().dropna()
    w_norm = np.array(weights) / 100
    p_ret = rets[assets].dot(w_norm)
    b_ret = rets[bench_ticker]

    p_cum = (1 + p_ret).cumprod() * cap_base
    b_cum = (1 + b_ret).cumprod() * cap_base
    
    dd = (p_cum / p_cum.cummax()) - 1
    sharpe = ((p_ret.mean() - (0.04/252)) / p_ret.std()) * np.sqrt(252)
    alpha = (p_ret.mean() * 252) - (0.04 + (p_ret.cov(b_ret)/b_ret.var()) * ((b_ret.mean() * 252) - 0.04))

    s_note = "🔵 Baik" if sharpe > 1.5 else "🟡 Sedang" if sharpe >= 1.0 else "🔴 Kurang"
    a_note = "🔵 Baik" if alpha*100 > 5 else "🟡 Sedang" if alpha*100 >= 0 else "🔴 Kurang"
    d_note = "🔵 Baik" if dd.min() >= -0.15 else "🟡 Sedang" if dd.min() >= -0.30 else "🔴 Kurang"

    # PERBAIKAN 3: font-weight diturunkan menjadi 500 agar angka tidak terlalu tebal
    def kpi_box(label, val, status, legend):
        return f"""
        <div style="background-color: #ffffff; padding: 18px; border-radius: 10px; border: 1px solid #eeeeee; height: 100%;">
            <div style="color: #555555; font-size: 14px; margin-bottom: 8px;">{label}</div>
            <div style="display: flex; align-items: baseline;">
                <div style="font-size: 34px; font-weight: 500; color: #222222;">{val}</div>
                <div style="font-size: 14px; margin-left: 12px; font-weight: 500; color: #666666;">{status}</div>
            </div>
            <div style="font-size: 11px; color: #999999; margin-top: 12px; border-top: 1px solid #f0f0f0; padding-top: 8px;">
                {legend}
            </div>
        </div>
        """

    # 5. Dashboard Grid
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_box("Current Value vs Target", f"${p_cum.iloc[-1]:.2f}", "🎯 Target", f"Basis: ${cap_base:.0f} → Target: ${cap_target:.0f}"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_box("Sharpe Ratio (Efficiency)", f"{sharpe:.2f}", s_note, "🔴 <1.0 | 🟡 1.0-1.5 | 🔵 >1.5"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_box("Alpha vs Benchmark", f"{alpha*100:.1f}%", a_note, "🔴 <0% | 🟡 0-5% | 🔵 >5%"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_box("Max Drawdown", f"{dd.min()*100:.2f}%", d_note, "🔵 >-15% | 🟡 -30% | 🔴 <-30%"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("Equity Curve")
        f1 = go.Figure()
        f1.add_trace(go.Scatter(x=p_cum.index, y=p_cum, name='Portfolio', line=dict(color='#0088ff', width=2.5)))
        f1.add_trace(go.Scatter(x=b_cum.index, y=b_cum, name='Benchmark', line=dict(color='#555555', width=2)))
        f1.add_hline(y=cap_target, line_dash="dot", line_color="#ff4b4b")
        f1.update_layout(height=380, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True), template="simple_white")
        st.plotly_chart(f1, use_container_width=True, config={'staticPlot': True})

    with g2:
        st.subheader("Drawdown Map")
        f2 = go.Figure()
        f2.add_trace(go.Scatter(x=dd.index, y=dd, fill='tozeroy', line=dict(color='#ff4b4b', width=1)))
        f2.update_layout(height=380, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True, tickformat='.1%'), template="simple_white")
        st.plotly_chart(f2, use_container_width=True, config={'staticPlot': True})
else:
    st.info("Input valid Tickers to generate blueprint...")
