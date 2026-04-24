"""
Dashboard — Gerçek Piyasa Verisi
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.data import (get_market_overview, get_bist_snapshot,
                         get_stock_data, BIST30, BIST100, BIST_ALL,
                         INDEX_GROUPS, STOCK_NAMES, get_name)
from utils.charts import candlestick_chart, COLORS
import plotly.graph_objects as go

def render():
    st.markdown("""
    <div style="margin-bottom:20px;">
        <h1 style="font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;
            color:#f1f5f9;margin:0;">🏠 Piyasa Genel Bakış</h1>
        <p style="font-family:'Space Mono',monospace;font-size:.65rem;color:#475569;margin:4px 0 0 0;">
            Gerçek zamanlı BIST verileri · ~15dk gecikme
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Piyasa Genel Durum ──
    with st.spinner("Piyasa verileri yükleniyor..."):
        overview = get_market_overview()

    if overview:
        cols = st.columns(len(overview))
        icons = {"BIST 100":"📈","USD/TRY":"💵","Altın (USD)":"🥇",
                 "Brent (USD)":"⛽","EUR/USD":"💶","Gümüş (USD)":"🥈"}
        for i, (label, data) in enumerate(overview.items()):
            val = data["value"]
            chg = data["change"]
            fmt = f"{val:,.2f}"
            delta_str = f"{chg:+.2f}%"
            with cols[i % len(cols)]:
                st.metric(
                    f"{icons.get(label,'📊')} {label}",
                    fmt,
                    delta=delta_str,
                    delta_color="normal"
                )
    else:
        st.info("Piyasa verisi yüklenemedi. İnternet bağlantısını kontrol edin.")

    st.markdown("---")

    # ── Endeks Seçimi + Snapshot ──
    hcol1, hcol2, hcol3 = st.columns([1, 1, 3])
    with hcol1:
        idx_group = st.selectbox("Endeks", list(INDEX_GROUPS.keys()), key="dash_idx")
    with hcol2:
        sort_by = st.selectbox("Sırala", ["Değ% ↓","Değ% ↑","Fiyat ↓","Hacim ↓"], key="dash_sort")
    with hcol3:
        st.markdown("<br>", unsafe_allow_html=True)
        refresh = st.button("🔄 Güncelle", key="dash_refresh")

    with st.spinner(f"{idx_group} verileri çekiliyor..."):
        snap = get_bist_snapshot(idx_group)

    if not snap.empty:
        # Sırala
        sort_map = {
            "Değ% ↓": ("Değ%", False), "Değ% ↑": ("Değ%", True),
            "Fiyat ↓": ("Fiyat", False), "Hacim ↓": ("Hacim", False),
        }
        scol, sasc = sort_map.get(sort_by, ("Değ%", False))
        if scol in snap.columns:
            snap = snap.sort_values(scol, ascending=sasc)

        col_table, col_charts = st.columns([1.6, 1])

        with col_table:
            st.markdown(f"#### 📊 {idx_group} Hisseleri ({len(snap)} hisse)")
            display = snap.copy()
            display["Değ%"] = display["Değ%"].apply(
                lambda x: f"{'▲' if x>=0 else '▼'} {abs(x):.2f}%"
            )
            display["Hacim"] = display["Hacim"].apply(
                lambda x: f"{x/1e6:.1f}M" if x >= 1e6 else f"{x/1e3:.0f}K"
            )
            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True,
                height=450,
                column_config={
                    "Sembol": st.column_config.TextColumn("Sembol", width=70),
                    "İsim":   st.column_config.TextColumn("Hisse"),
                    "Fiyat":  st.column_config.NumberColumn("Fiyat ₺", format="%.2f"),
                    "Değ%":   st.column_config.TextColumn("Değişim", width=90),
                    "Hacim":  st.column_config.TextColumn("Hacim"),
                },
            )

        with col_charts:
            st.markdown("#### 🏆 En Çok Yükselen")
            top5 = snap.nlargest(5, "Değ%") if "Değ%" in snap.columns else snap.head(5)
            for _, row in top5.iterrows():
                pct = row.get("Değ%", 0)
                if isinstance(pct, str):
                    continue
                bar_w = min(int(abs(pct) * 12), 100)
                st.markdown(f"""
                <div style="background:#111827;border-radius:6px;padding:8px 12px;
                    margin-bottom:4px;border-left:3px solid #00d4aa;display:flex;
                    justify-content:space-between;">
                    <span style="font-family:'Space Mono',monospace;font-size:.75rem;
                        color:#e2e8f0;font-weight:700;">{row['Sembol']}</span>
                    <span style="font-family:'Space Mono',monospace;font-size:.75rem;
                        color:#00d4aa;">▲ {abs(pct):.2f}%</span>
                </div>""", unsafe_allow_html=True)

            st.markdown("#### 📉 En Çok Düşen")
            bot5 = snap.nsmallest(5, "Değ%") if "Değ%" in snap.columns else snap.tail(5)
            for _, row in bot5.iterrows():
                pct = row.get("Değ%", 0)
                if isinstance(pct, str):
                    continue
                st.markdown(f"""
                <div style="background:#111827;border-radius:6px;padding:8px 12px;
                    margin-bottom:4px;border-left:3px solid #f87171;display:flex;
                    justify-content:space-between;">
                    <span style="font-family:'Space Mono',monospace;font-size:.75rem;
                        color:#e2e8f0;font-weight:700;">{row['Sembol']}</span>
                    <span style="font-family:'Space Mono',monospace;font-size:.75rem;
                        color:#f87171;">▼ {abs(pct):.2f}%</span>
                </div>""", unsafe_allow_html=True)
    else:
        st.warning("Veri çekilemedi.")

    st.markdown("---")

    # ── Hızlı Grafik ──
    st.markdown("#### ⚡ Hisse Grafiği")
    all_syms = BIST30 + [s for s in BIST100 if s not in BIST30]

    qc1, qc2, qc3, qc4 = st.columns([2, 1, 1, 1])
    with qc1:
        sym = st.selectbox(
            "Hisse", all_syms,
            format_func=lambda x: f"{x}  {get_name(x)}",
            key="dash_sym"
        )
    with qc2:
        period = st.selectbox("Dönem", ["1mo","3mo","6mo","1y","2y","5y"],
                              index=3, key="dash_per")
    with qc3:
        chart_type = st.selectbox("Grafik", ["Mum","Çizgi","Çubuk"], key="dash_ctype")
    with qc4:
        st.markdown("<br>", unsafe_allow_html=True)
        go_btn = st.button("📊 Göster", use_container_width=True, key="dash_go")

    if go_btn or "dash_df" not in st.session_state or st.session_state.get("dash_last_sym") != sym:
        st.session_state["dash_last_sym"] = sym
        with st.spinner(f"{sym} verisi çekiliyor..."):
            df = get_stock_data(sym, period=period)
        st.session_state["dash_df"]  = df
        st.session_state["dash_per_last"] = period

    df = st.session_state.get("dash_df", pd.DataFrame())
    if not df.empty:
        fig = go.Figure()
        if chart_type == "Mum":
            fig.add_trace(go.Candlestick(
                x=df.index, open=df["open"], high=df["high"],
                low=df["low"],  close=df["close"],
                increasing_line_color=COLORS["candle_up"],
                decreasing_line_color=COLORS["candle_dn"],
                name=sym,
            ))
        elif chart_type == "Çizgi":
            fig.add_trace(go.Scatter(
                x=df.index, y=df["close"],
                line=dict(color=COLORS["green"], width=2),
                fill="tozeroy", fillcolor="rgba(0,212,170,0.05)",
                name=sym,
            ))
        else:
            fig.add_trace(go.Bar(
                x=df.index, y=df["close"],
                marker_color=COLORS["blue"], name=sym
            ))

        # Hacim
        colors_vol = [COLORS["candle_up"] if c >= o else COLORS["candle_dn"]
                      for c, o in zip(df["close"], df["open"])]
        fig.add_trace(go.Bar(
            x=df.index, y=df["volume"],
            marker_color=colors_vol, opacity=0.5,
            name="Hacim", yaxis="y2"
        ))

        fig.update_layout(
            paper_bgcolor=COLORS["bg"],
            plot_bgcolor=COLORS["bg2"],
            font=dict(family="Space Mono,monospace", color=COLORS["text"], size=11),
            xaxis=dict(
                gridcolor=COLORS["grid"], rangeslider_visible=False,
                rangeselector=dict(
                    bgcolor=COLORS["bg2"],
                    activecolor=COLORS["grid"],
                    buttons=[
                        dict(count=1,  label="1A",  step="month", stepmode="backward"),
                        dict(count=3,  label="3A",  step="month", stepmode="backward"),
                        dict(count=6,  label="6A",  step="month", stepmode="backward"),
                        dict(count=1,  label="1Y",  step="year",  stepmode="backward"),
                        dict(count=2,  label="2Y",  step="year",  stepmode="backward"),
                        dict(step="all", label="Tümü"),
                    ]
                )
            ),
            yaxis=dict(
                gridcolor=COLORS["grid"], title="Fiyat (₺)",
                domain=[0.25, 1.0], side="right"
            ),
            yaxis2=dict(
                gridcolor=COLORS["grid"], title="Hacim",
                domain=[0.0, 0.22], showgrid=False,
            ),
            height=520,
            margin=dict(l=10, r=60, t=40, b=40),
            title=dict(
                text=f"{sym}  {get_name(sym)} · {period}",
                font=dict(color=COLORS["title"], size=14)
            ),
            legend=dict(bgcolor="rgba(0,0,0,0)"),
            dragmode="zoom",
            hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True, config={
            "displayModeBar": True,
            "modeBarButtonsToAdd": ["drawline","drawopenpath","eraseshape"],
            "scrollZoom": True,
            "toImageButtonOptions": {"format": "png", "filename": f"borsa_arena_{sym}"},
        })

        # İstatistik özeti
        s1, s2, s3, s4, s5 = st.columns(5)
        last  = float(df["close"].iloc[-1])
        first = float(df["close"].iloc[0])
        ret   = (last - first) / first * 100
        high  = float(df["high"].max())
        low   = float(df["low"].min())
        avg_vol = float(df["volume"].mean())

        s1.metric("Son Fiyat",     f"₺{last:,.2f}")
        s2.metric("Dönem Getirisi",f"{ret:+.2f}%", delta=f"{ret:+.2f}%")
        s3.metric("Dönem Yüksek",  f"₺{high:,.2f}")
        s4.metric("Dönem Düşük",   f"₺{low:,.2f}")
        s5.metric("Ort. Hacim",    f"{avg_vol/1e6:.1f}M")
    else:
        st.error(f"{sym} için veri çekilemedi. Hisse sembolünü kontrol edin veya daha sonra tekrar deneyin.")
