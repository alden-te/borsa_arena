"""
Korelasyon Analizi — Düzeltilmiş versiyon
Boş veri kontrolü + NaN önleme + gerçek veri çekme
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.data import get_multi_stock_close, _FALLBACK, BIST30, INDEX_GROUPS, get_name, SECTOR_MAP
from utils.charts import correlation_heatmap, COLORS
from scipy import stats
import plotly.graph_objects as go

def _safe_corr(symbols: list, period: str, method: str) -> tuple:
    """
    Güvenli korelasyon hesaplama.
    Returns: (corr_df or None, error_msg or None, n_valid_symbols)
    """
    if len(symbols) < 2:
        return None, "En az 2 hisse seçin.", 0

    with st.spinner(f"{len(symbols)} hisse için günlük getiri verisi çekiliyor..."):
        closes = get_multi_stock_close(symbols, period=period)

    if closes is None or closes.empty:
        return None, "Veri çekilemedi. İnternet bağlantısını kontrol edin.", 0

    # Geçerli sütunları filtrele (en az 20 gözlem olan)
    valid_cols = [c for c in closes.columns if closes[c].dropna().shape[0] >= 20]
    if len(valid_cols) < 2:
        return None, f"Yeterli veri bulunamadı. ({len(valid_cols)}/{len(symbols)} hisse için veri geldi)", len(valid_cols)

    closes = closes[valid_cols].copy()
    returns = closes.pct_change().dropna(how="all")

    # Satır bazında NaN kontrolü — en az %70 dolu satırlar
    min_non_null = max(2, int(len(valid_cols) * 0.7))
    returns = returns.dropna(thresh=min_non_null)

    # Kolon bazında NaN kontrolü
    returns = returns.dropna(axis=1, thresh=max(20, int(len(returns)*0.5)))

    if returns.shape[0] < 10 or returns.shape[1] < 2:
        return None, f"Veri yetersiz: {returns.shape[0]} gün × {returns.shape[1]} hisse.", len(valid_cols)

    try:
        corr = returns.corr(method=method)
        # NaN dolu satır/kolon temizle
        corr = corr.dropna(how="all").dropna(axis=1, how="all")
        if corr.empty or corr.shape[0] < 2:
            return None, "Korelasyon hesaplanamadı (veri uyumsuz).", len(valid_cols)
        return corr, None, len(valid_cols)
    except Exception as e:
        return None, f"Hesaplama hatası: {e}", 0


def render():
    st.markdown("""
    <div style="margin-bottom:20px;">
        <h1 style="font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;
            color:#f1f5f9;margin:0;">🌡️ Korelasyon & İlişki Analizi</h1>
        <p style="font-family:'Space Mono',monospace;font-size:.65rem;color:#475569;margin:4px 0 0 0;">
            Pearson/Spearman Korelasyonu · Isı Haritası · Lead-Lag Analizi
        </p>
    </div>""", unsafe_allow_html=True)

    tab_corr, tab_sector, tab_lead = st.tabs([
        "🌡️ Korelasyon Haritası","🏭 Sektör Analizi","🔮 Öncü Gösterge"
    ])

    # ══ KORELASYON HARİTASI ══════════════════════════════════
    with tab_corr:
        st.markdown("##### Hisse Senedi Korelasyon Matrisi")

        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            idx_grp = st.selectbox("Endeks Havuzu", list(INDEX_GROUPS.keys()), key="cr_idx")
        with c2:
            period  = st.selectbox("Dönem", ["1mo","3mo","6mo","1y","2y"], index=3, key="cr_per")
        with c3:
            method  = st.selectbox("Yöntem", ["pearson","spearman"], key="cr_meth")

        pool = INDEX_GROUPS[idx_grp][:20]

        with st.expander("🔧 Özel hisse seç"):
            custom_syms = st.multiselect(
                "Hisse seç (2–25)",
                sorted(_FALLBACK),
                default=[],
                format_func=lambda x: f"{x}  {get_name(x)}",
                key="cr_custom",
                max_selections=25,
            )
            if len(custom_syms) >= 2:
                pool = custom_syms

        max_n = st.slider("Max hisse sayısı", 4, 25, min(15, len(pool)), key="cr_maxn")
        pool  = pool[:max_n]

        # Seçili hisseler göster
        st.markdown(f"""
        <div style="background:#111827;border:1px solid #1e2d4a;border-radius:6px;
            padding:8px 12px;margin-bottom:12px;font-family:'Space Mono',monospace;font-size:.65rem;color:#64748b;">
            📋 Seçili: {', '.join(pool[:10])}{'...' if len(pool)>10 else ''} ({len(pool)} hisse)
        </div>""", unsafe_allow_html=True)

        if st.button("🔥 Korelasyon Haritasını Oluştur", type="primary", key="cr_calc"):
            corr, err, n_valid = _safe_corr(pool, period, method)
            if err:
                st.error(f"❌ {err}")
                if n_valid > 0:
                    st.info(f"💡 {n_valid}/{len(pool)} hisse için veri geldi. Daha kısa dönem veya daha az hisse deneyin.")
            else:
                st.session_state["cr_corr"]   = corr
                st.session_state["cr_period"] = period
                st.session_state["cr_method"] = method
                st.session_state["cr_n"]      = n_valid
                st.success(f"✅ {n_valid} hisse, {period} dönemi, {corr.shape[0]}×{corr.shape[1]} matris")

        if "cr_corr" in st.session_state:
            corr    = st.session_state["cr_corr"]
            n_valid = st.session_state.get("cr_n", corr.shape[0])

            # Yüklenme bilgisi
            st.markdown(f"""
            <div style="background:#0d2818;border:1px solid #166534;border-radius:6px;
                padding:8px 12px;margin-bottom:8px;font-family:'Space Mono',monospace;font-size:.65rem;color:#86efac;">
                ✅ {corr.shape[0]} hisse · {st.session_state.get('cr_period','?')} dönem · 
                {st.session_state.get('cr_method','?').title()} yöntemi
            </div>""", unsafe_allow_html=True)

            fig = correlation_heatmap(corr, f"Korelasyon Matrisi ({st.session_state.get('cr_method','').title()})")
            st.plotly_chart(fig, use_container_width=True)

            # En yüksek/düşük çiftler
            cc1, cc2 = st.columns(2)
            with cc1:
                st.markdown("**🔴 En Yüksek Korelasyon**")
                for p in _top_pairs(corr, 5, "high"):
                    _pair_card(p, "#f59e0b")
            with cc2:
                st.markdown("**🟢 En Düşük (Çeşitlendirme İçin İdeal)**")
                for p in _top_pairs(corr, 5, "low"):
                    _pair_card(p, "#00d4aa")

            st.markdown("""
            <div style="background:#111827;border:1px solid #1e3a5f;border-radius:8px;
                padding:12px 16px;margin-top:12px;font-family:'Space Mono',monospace;font-size:.65rem;color:#64748b;">
                📌 r > 0.7 → Yüksek korelasyon (birlikte hareket eder)<br>
                📌 0.3 < r < 0.7 → Orta korelasyon<br>
                📌 r &lt; 0.3 → Düşük korelasyon (portföy çeşitlendirmesi için ideal)
            </div>""", unsafe_allow_html=True)

            # İndir
            csv = corr.round(4).to_csv().encode("utf-8")
            st.download_button("📥 Korelasyon Matrisini İndir", csv,
                               "korelasyon.csv", "text/csv", use_container_width=False)
        else:
            _placeholder_hint("🔥 Korelasyon Haritasını Oluştur butonuna tıklayın.")

    # ══ SEKTÖR ANALİZİ ════════════════════════════════════════
    with tab_sector:
        st.markdown("##### 🏭 Sektör Bazlı Korelasyon Analizi")

        sc1, sc2 = st.columns([2,1])
        with sc1:
            sector  = st.selectbox("Sektör", list(SECTOR_MAP.keys()), key="sec_sel")
        with sc2:
            sec_per = st.selectbox("Dönem", ["3mo","6mo","1y","2y"], index=2, key="sec_per")

        syms = SECTOR_MAP[sector]
        st.caption(f"Sektördeki hisseler: {', '.join(syms)}")

        if st.button("📊 Sektör Analizi Yap", type="primary", key="sec_btn"):
            corr, err, n_valid = _safe_corr(syms, sec_per, "pearson")
            if err:
                st.error(f"❌ {err}")
            else:
                st.session_state["sec_corr"]   = corr
                st.session_state["sec_sector"] = sector

        if "sec_corr" in st.session_state:
            corr   = st.session_state["sec_corr"]
            sector_name = st.session_state.get("sec_sector","")
            fig = correlation_heatmap(corr, f"{sector_name} Sektörü Korelasyonu")
            st.plotly_chart(fig, use_container_width=True)

            # Getiri ve volatilite istatistikleri (son çekilen veri)
            with st.expander("📊 Sektör Hisse İstatistikleri"):
                closes = get_multi_stock_close(syms[:15], period=sec_per)
                if closes is not None and not closes.empty:
                    ret = closes.pct_change().dropna(how="all").dropna(axis=1, thresh=10)
                    rows = []
                    for col in ret.columns:
                        s = ret[col].dropna()
                        if len(s) < 5: continue
                        rows.append({
                            "Sembol":    col,
                            "İsim":      get_name(col),
                            "Yıllık Getiri%": round(float(s.mean())*252*100,2),
                            "Volatilite%":    round(float(s.std())*np.sqrt(252)*100,2),
                            "Sharpe":         round(float(s.mean())/float(s.std())*np.sqrt(252),2) if float(s.std())>0 else 0,
                        })
                    if rows:
                        st.dataframe(
                            pd.DataFrame(rows).sort_values("Sharpe",ascending=False),
                            use_container_width=True, hide_index=True,
                        )

    # ══ ÖNCÜ GÖSTERGE ═════════════════════════════════════════
    with tab_lead:
        st.markdown("##### 🔮 Lead-Lag (Öncü-Takipçi) Analizi")
        st.markdown("""
        <div style="background:#111827;border:1px solid #1e3a5f;border-radius:8px;
            padding:12px 16px;margin-bottom:14px;">
            <div style="font-family:'Space Mono',monospace;font-size:.68rem;color:#94a3b8;">
                Hangi hisse diğerini <strong style="color:#00d4aa;">kaç gün önceden</strong> haber veriyor?<br>
                Cross-korelasyon ile öncü (lead) ve takipçi hisseler tespit edilir.
            </div>
        </div>""", unsafe_allow_html=True)

        all_opts = sorted(_FALLBACK)
        ll1, ll2 = st.columns(2)
        with ll1:
            lead_sym = st.selectbox("Öncü Hisse", all_opts,
                                    format_func=lambda x: f"{x}  {get_name(x)}", key="ll_lead")
        with ll2:
            lag_sym  = st.selectbox("Takipçi Hisse", all_opts, index=1,
                                    format_func=lambda x: f"{x}  {get_name(x)}", key="ll_lag")

        ll3, ll4 = st.columns([1,2])
        with ll3:
            max_lag = st.slider("Max gecikme (gün)", 1, 30, 15, key="ll_maxlag")
        with ll4:
            ll_per  = st.selectbox("Dönem", ["6mo","1y","2y"], index=1, key="ll_per")

        if st.button("🔍 Lead-Lag Analiz Et", type="primary", key="ll_run"):
            if lead_sym == lag_sym:
                st.error("Aynı hisseyi seçemezsiniz.")
            else:
                closes = get_multi_stock_close([lead_sym, lag_sym], period=ll_per)
                if closes is None or closes.empty or closes.shape[1] < 2:
                    st.error("Veri çekilemedi.")
                else:
                    valid_cols = [c for c in closes.columns if closes[c].dropna().shape[0] >= 20]
                    if len(valid_cols) < 2:
                        st.error(f"Yeterli veri yok. ({len(valid_cols)} hisse)")
                    else:
                        r1 = closes[valid_cols[0]].pct_change().dropna()
                        r2 = closes[valid_cols[1]].pct_change().dropna()
                        common = r1.index.intersection(r2.index)
                        r1, r2 = r1[common], r2[common]

                        if len(r1) < 30:
                            st.error(f"Yeterli gün yok: {len(r1)} gün.")
                        else:
                            lags  = list(range(-max_lag, max_lag+1))
                            corrs = []; pvals = []
                            for lag in lags:
                                try:
                                    if lag < 0:
                                        a, b = r1.iloc[:lag].values, r2.iloc[-lag:].values
                                    elif lag > 0:
                                        a, b = r1.iloc[lag:].values, r2.iloc[:-lag].values
                                    else:
                                        a, b = r1.values, r2.values
                                    if len(a) > 10:
                                        c_val, p_val = stats.pearsonr(a, b)
                                        corrs.append(float(c_val))
                                        pvals.append(float(p_val))
                                    else:
                                        corrs.append(0); pvals.append(1)
                                except Exception:
                                    corrs.append(0); pvals.append(1)

                            fig = go.Figure()
                            bar_colors = [COLORS["green"] if c > 0 else COLORS["red"] for c in corrs]
                            fig.add_trace(go.Bar(
                                x=lags, y=corrs,
                                marker_color=bar_colors, opacity=0.85, name="Pearson r",
                                hovertemplate="Gecikme: %{x} gün<br>r = %{y:.3f}<extra></extra>",
                            ))
                            ci = 1.96 / np.sqrt(max(len(r1)-1, 1))
                            for yv, lbl in [(ci,"+ %95 CI"),(-ci,"− %95 CI")]:
                                fig.add_hline(y=yv, line_color="#94a3b8", line_dash="dash",
                                              line_width=1, opacity=0.5, annotation_text=lbl,
                                              annotation_font_color="#94a3b8")
                            fig.add_hline(y=0, line_color=COLORS["grid"], line_width=1)
                            fig.update_layout(
                                paper_bgcolor=COLORS["bg"], plot_bgcolor=COLORS["bg2"],
                                font=dict(family="Space Mono,monospace",color=COLORS["text"]),
                                xaxis=dict(title="Gecikme (gün)", gridcolor=COLORS["grid"]),
                                yaxis=dict(title="Pearson r", gridcolor=COLORS["grid"]),
                                title=dict(text=f"{lead_sym} ↔ {lag_sym} Cross-Korelasyon",
                                           font=dict(color=COLORS["title"])),
                                height=360, margin=dict(l=40,r=20,t=40,b=40),
                                legend=dict(bgcolor="rgba(0,0,0,0)"),
                            )
                            st.plotly_chart(fig, use_container_width=True)

                            best_idx  = int(np.argmax(np.abs(corrs)))
                            best_lag  = lags[best_idx]
                            best_corr = corrs[best_idx]
                            best_p    = pvals[best_idx]
                            sig_str   = "✅ istatistiksel olarak anlamlı (p<0.05)" if best_p < 0.05 else "⚠️ anlamsız (p≥0.05)"

                            if abs(best_corr) < ci:
                                msg = "İki hisse arasında anlamlı bir gecikme ilişkisi bulunamadı."
                            elif best_lag < 0:
                                msg = f"**{lag_sym}**, **{lead_sym}**'yi ~{abs(best_lag)} gün önceden haber veriyor."
                            elif best_lag > 0:
                                msg = f"**{lead_sym}**, **{lag_sym}**'yi ~{abs(best_lag)} gün önceden haber veriyor."
                            else:
                                msg = "İki hisse eş zamanlı hareket ediyor."

                            color = "#00d4aa" if abs(best_corr) > ci else "#f59e0b"
                            st.markdown(f"""
                            <div style="background:#111827;border:1px solid {color}55;
                                border-left:4px solid {color};border-radius:8px;padding:14px 16px;margin-top:8px;">
                                <div style="font-family:'Syne',sans-serif;font-weight:700;
                                    color:#e2e8f0;font-size:.9rem;">🔮 {msg}</div>
                                <div style="font-family:'Space Mono',monospace;font-size:.65rem;
                                    color:#64748b;margin-top:6px;">r = {best_corr:.3f} · {sig_str}</div>
                            </div>""", unsafe_allow_html=True)


def _top_pairs(corr: pd.DataFrame, n: int, direction: str) -> list:
    pairs = []
    cols  = corr.columns.tolist()
    for i in range(len(cols)):
        for j in range(i+1, len(cols)):
            v = corr.iloc[i,j]
            if pd.notna(v):
                pairs.append({"pair": f"{cols[i]} ↔ {cols[j]}", "corr": v})
    if not pairs:
        return []
    pairs.sort(key=lambda x: x["corr"], reverse=(direction == "high"))
    return pairs[:n]

def _pair_card(p: dict, color: str):
    st.markdown(f"""
    <div style="background:#111827;border:1px solid #1e2d4a;border-radius:6px;
        padding:9px 12px;margin:3px 0;display:flex;justify-content:space-between;">
        <span style="font-family:'Space Mono',monospace;font-size:.7rem;color:#e2e8f0;">{p['pair']}</span>
        <span style="font-family:'Space Mono',monospace;font-size:.7rem;color:{color};font-weight:700;">
            {p['corr']:.3f}</span>
    </div>""", unsafe_allow_html=True)

def _placeholder_hint(msg: str):
    st.markdown(f"""
    <div style="background:#111827;border:2px dashed #1e2d4a;border-radius:12px;
        height:200px;display:flex;align-items:center;justify-content:center;margin-top:16px;">
        <div style="font-family:'Space Mono',monospace;font-size:.72rem;color:#334155;text-align:center;">
            {msg}
        </div>
    </div>""", unsafe_allow_html=True)
