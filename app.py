import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 1. Konfigurasi Halaman & UI Clean
st.set_page_config(page_title="Growth Blueprint V20", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    input[type=text] { text-transform: uppercase; }
    
    .main-title {
        font-size: 36px !important; 
        font-weight: bold;
        margin-bottom: 25px;
        letter-spacing: -1px;
        color: #111111;
    }
    
    .locked-weight {
        background-color: rgba(128, 128, 128, 0.05);
        padding: 8px 10px;
        border-radius: 6px;
        font-size: 15px;
        font-weight: bold;
        color: #0088ff;
        text-align: center;
        border: 1px solid rgba(128, 128, 128, 0.1);
        margin-top: 2px;
    }

    /* CSS untuk menghilangkan kotak pada tombol slider agar murni simbol */
    div[data-testid="stHorizontalBlock"] .stButton > button {
        border: none !important;
        background-color: transparent !important;
        box-shadow: none !important;
        color: #555555 !important;
        font-size: 20px !important;
        padding: 0px !important;
        margin-top: 10px !important;
    }

    /* Mempertegas Judul Menu Kluster */
    .cluster-header {
        font-size: 20px !important;
        font-weight: 900 !important;
        color: #222222;
        letter-spacing: 0.5px;
        margin-top: 20px;
        margin-bottom: 5px;
    }

    input::-webkit-outer-spin-button,
    input::-webkit-inner-spin-button {
        -webkit-appearance: none;
        margin: 0;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">📈 Maximum Growth Blueprint: AI-Energy</p>', unsafe_allow_html=True)

# 2. State Manajemen
if 's_growth' not in st.session_state: st.session_state.s_growth = 65
if 's_tactical' not in st.session_state: st.session_state.s_tactical = 20
if 's_hedging' not in st.session_state: st.session_state.s_hedging = 15

if 'assets_data' not in st.session_state:
    st.session_state.assets_data = {
        'Growth': ["NVDA", "VST", "PLTR"],
        'Tactical': ["TSM", "AMD"],
        'Hedging': ["GLD", "BTC"]
    }

# 3. Sidebar: Kontrol Modal Dasar
st.sidebar.header("Konfigurasi Portofolio")
cap_base = st.sidebar.number_input("Modal Awal (Basis)", value=65.0)
cap_target = st.sidebar.number_input("Target Capital Gain", value=100.0)
bench_ticker = st.sidebar.text_input("Benchmark", value="SPY").strip().upper()

st.sidebar.markdown("---")

# 4. Sidebar: Target Alokasi Kluster (Format: - Slider +)
st.sidebar.header("⚖️ Target Alokasi Kluster (%)")

def symbol_slider(label, key, min_v, max_v):
    st.sidebar.markdown(f"<p style='font-size:13px; font-weight:bold; margin-bottom:-10px; color:#666666;'>{label}</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.sidebar.columns([1, 8, 1])
    with c1:
        if st.button("−", key=f"m_{key}"):
            if st.session_state[key] > min_v: st.session_state[key] -= 1
    with c2:
        st.slider(label, min_v, max_v, key=key, label_visibility="collapsed")
    with c3:
        if st.button("+", key=f"p_{key}"):
            if st.session_state[key] < max_v: st.session_state[key] += 1

symbol_slider("1. Growth Engine", "s_growth", 10, 85)
symbol_slider("2. Tactical Support", "s_tactical", 5, 40)
symbol_slider("3. Hedging & Defense", "s_hedging", 5, 40)

total_check = st.session_state.s_growth + st.session_state.s_tactical + st.session_state.s_hedging
if total_check != 100:
    st.sidebar.error(f"⚠️ Total: {total_check}% (Harus 100%)")

# 5. Fungsi Hierarki Internal Kluster
def get_cluster_weights(assets, cluster_total):
    n = len(assets)
    if n == 0: return []
    decay = 0.5 
    raw = [decay ** i for i in range(n)]
    norm = np.array(raw) / sum(raw)
    return [round(val * cluster_total, 1) for val in norm]

# 6. Sidebar: Area Input Aset (Desain Menu Besar + Gerigi)
final_assets = []
final_weights = []

def render_cluster_ui(name, display_name, color, state_key):
    # Header Kluster (Tanpa expander)
    st.sidebar.markdown(f'<p class="cluster-header">{display_name.upper()}</p>', unsafe_allow_html=True)
    
    # Menu Pengaturan Gerigi (Dropdown untuk Aset & Tombol)
    with st.sidebar.expander(f"⚙️ Pengaturan {display_name}", expanded=False):
        current_assets = st.session_state.assets_data[name]
        c_weight_limit = st.session_state[state_key]
        w_list = get_cluster_weights(current_assets, c_weight_limit)

        # Tombol Tambah/Hapus di dalam dropdown
        col_t1, col_t2 = st.columns(2)
        if col_t1.button(f"➕ Aset", key=f"add_{name}", use_container_width=True):
            st.session_state.assets_data[name].append("")
            st.rerun()
        if col_t2.button(f"➖ Aset", key=f"del_{name}", use_container_width=True):
            if len(current_assets) > 1:
                st.session_state.assets_data[name].pop()
                st.rerun()
        
        st.markdown("---")

        # List Aset di dalam dropdown
        for idx, asset in enumerate(current_assets):
            col_a, col_w = st.columns([2, 1.5])
            with col_a:
                new_val = st.text_input(f"t_{name}_{idx}", value=asset, key=f"in_{name}_{idx}", label_visibility="collapsed").strip().upper()
                st.session_state.assets_data[name][idx] = new_val
            with col_w:
                st.markdown(f"<div class='locked-weight'>{w_list[idx]}% 🔒</div>", unsafe_allow_html=True)
            if new_val:
                final_assets.append(new_val)
                final_weights.append(w_list[idx])

render_cluster_ui('Growth', 'Growth Engine', '#0088ff', 's_growth')
render_cluster_ui('Tactical', 'Tactical Support', '#ffaa00', 's_tactical')
render_cluster_ui('Hedging', 'Hedging & Defense', '#00cc66', 's_hedging')

if st.sidebar.button("💾 SAVE CONFIGURATION", use_container_width=True):
    st.sidebar.success("Blueprint Locked!")

# 7. Komputasi Data Utama
@st.cache_data(ttl=3600)
def fetch_data(tickers, benchmark):
    all_t = list(set([t for t in tickers if t] + [benchmark]))
    try:
        data = yf.download(all_t, period="3y", progress=False)['Close']
        return data.ffill()
    except: return pd.DataFrame()

df = fetch_data(final_assets, bench_ticker)

if not df.empty and all(a in df.columns for a in final_assets) and bench_ticker in df.columns:
    df_clean = df[final_assets + [bench_ticker]].dropna()
    if not df_clean.empty:
        rets = df_clean.pct_change().dropna()
        w_norm = np.array(final_weights) / 100
        if w_norm.sum() > 0: w_norm = w_norm / w_norm.sum()
            
        p_ret = rets[final_assets].dot(w_norm)
        b_ret = rets[bench_ticker]

        p_cum = (1 + p_ret).cumprod() * cap_base
        b_cum = (1 + b_ret).cumprod() * cap_base
        dd = (p_cum / p_cum.cummax()) - 1
        sharpe = ((p_ret.mean() - (0.04/252)) / p_ret.std()) * np.sqrt(252)
        alpha = (p_ret.mean() * 252) - (0.04 + (p_ret.cov(b_ret)/b_ret.var()) * ((b_ret.mean() * 252) - 0.04))

        s_n = "🔵 Baik" if sharpe > 1.5 else "🟡 Sedang" if sharpe >= 1.0 else "🔴 Kurang"
        a_n = "🔵 Baik" if alpha*100 > 5 else "🟡 Sedang" if alpha*100 >= 0 else "🔴 Kurang"
        d_n = "🔵 Baik" if dd.min() >= -0.15 else "🟡 Sedang" if dd.min() >= -0.30 else "🔴 Kurang"

        def kpi_box(label, val, status, legend):
            return f"""
            <div style="background-color: #ffffff; padding: 18px; border-radius: 10px; border: 1px solid #eeeeee; height: 100%;">
                <div style="color: #555555; font-size: 14px; margin-bottom: 8px;">{label}</div>
                <div style="display: flex; align-items: baseline;">
                    <div style="font-size: 34px; font-weight: 500; color: #222222;">{val}</div>
                    <div style="font-size: 14px; margin-left: 12px; font-weight: 500; color: #666666;">{status}</div>
                </div>
                <div style="font-size: 11px; color: #999999; margin-top: 12px; border-top: 1px solid #f0f0f0; padding-top: 8px;">{legend}</div>
            </div>"""

        # 8. Render Dasbor Dasbor Utama
        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.markdown(kpi_box("Current Value vs Target", f"${p_cum.iloc[-1]:.2f}", "🎯 Target", f"Basis: ${cap_base:.0f} → Target: ${cap_target:.0f}"), unsafe_allow_html=True)
        with m2: st.markdown(kpi_box("Sharpe Ratio (Efficiency)", f"{sharpe:.2f}", s_n, "🔴 <1.0 | 🟡 1.0-1.5 | 🔵 >1.5"), unsafe_allow_html=True)
        with m3: st.markdown(kpi_box("Alpha vs Benchmark", f"{alpha*100:.1f}%", a_n, "🔴 <0% | 🟡 0-5% | 🔵 >5%"), unsafe_allow_html=True)
        with m4: st.markdown(kpi_box("Max Drawdown", f"{dd.min()*100:.2f}%", d_n, "🔵 >-15% | 🟡 -30% | 🔴 <-30%"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Equity Curve")
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=p_cum.index, y=p_cum, name='Portfolio', line=dict(color='#0088ff', width=2.5)))
            fig1.add_trace(go.Scatter(x=b_cum.index, y=b_cum, name=f'S&P 500 ({bench_ticker})', line=dict(color='#333333', width=2)))
            fig1.add_hline(y=cap_target, line_dash="dot", line_color="#ff4b4b")
            fig1.update_layout(height=380, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True), template="simple_white", legend=dict(orientation="h", y=1.1, x=0))
            st.plotly_chart(fig1, use_container_width=True, config={'staticPlot': True})
        with g2:
            st.subheader("Drawdown Map")
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=dd.index, y=dd, fill='tozeroy', line=dict(color='#ff4b4b', width=1)))
            fig2.update_layout(height=380, margin=dict(l=0,r=0,t=0,b=0), xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True, tickformat='.1%'), template="simple_white")
            st.plotly_chart(fig2, use_container_width=True, config={'staticPlot': True})
else:
    st.info("Atur Ticker di Menu Pengaturan (⚙️) untuk memulai.")
