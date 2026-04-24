"""
Temel Analiz & Değerleme — Ultra Pro
10 model, Piotroski, sektör analizi, ELMAS/ALTIN taraması
"""
import streamlit as st
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.data import BISTDataFetcher, _FALLBACK, BIST30, INDEX_GROUPS
from utils.valuation import UltraProCalculator

def fp(v):
    if v is None or (isinstance(v,float) and np.isnan(v)): return "—"
    return f"%{v*100:.1f}"

def render():
    st.markdown("""
    <div style="margin-bottom:20px;">
        <h1 style="font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;
            color:#f1f5f9;margin:0;">💎 Temel Analiz & Değerleme</h1>
        <p style="font-family:'Space Mono',monospace;font-size:.65rem;color:#475569;margin:4px 0 0 0;">
            10 Değerleme Modeli · Piotroski F-Skor · Graham · Kompozit Skor
        </p>
    </div>""", unsafe_allow_html=True)

    # ── Parametreler
    pc1, pc2, pc3 = st.columns([1,1,2])
    with pc1:
        idx_grp = st.selectbox("Hisse Havuzu", list(INDEX_GROUPS.keys()), key="vl_idx")
    with pc2:
        max_n = st.slider("Max Hisse", 5, 50, 20, key="vl_maxn")
    with pc3:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("💡 Değerleme yfinance verilerini kullanır. Bağlantı hızına göre 1-3 dk sürebilir.")

    symbols = INDEX_GROUPS[idx_grp][:max_n]

    # Özel seçim
    with st.expander("🔧 Özel hisse listesi"):
        custom = st.multiselect("Hisse seç", sorted(_FALLBACK),
                                format_func=lambda x: x, key="vl_custom")
        if custom:
            symbols = custom[:50]

    run = st.button("🚀 Değerleme Başlat", type="primary", use_container_width=True, key="vl_run")

    if run:
        prog = st.progress(0, "Veriler çekiliyor...")
        fetcher = BISTDataFetcher(workers=6, rate_delay=0.08)

        def cb(done, total):
            prog.progress(done/total, f"{done}/{total} hisse işlendi...")

        with st.spinner("Temel veriler çekiliyor..."):
            raw_df = fetcher.fetch_all(symbols, prog_cb=cb)

        prog.empty()

        if raw_df.empty:
            st.error("Veri çekilemedi. Lütfen tekrar deneyin.")
            return

        # Hesapla
        with st.spinner("10 model hesaplanıyor..."):
            calc = UltraProCalculator()
            df   = calc.compute(raw_df)

        st.session_state["vl_df"] = df
        st.success(f"✅ {len(df)} hisse değerlendirildi!")

    if "vl_df" not in st.session_state:
        _show_explainer()
        return

    df = st.session_state["vl_df"]

    # ── Özet Metrikler
    st.markdown("---")
    m1,m2,m3,m4,m5,m6 = st.columns(6)
    m1.metric("💎 ELMAS",  (df["sonuc_skoru"]=="💎 ELMAS").sum())
    m2.metric("⭐ ALTIN",  (df["sonuc_skoru"]=="⭐ ALTIN").sum())
    m3.metric("🥈 GÜMÜŞ", (df["sonuc_skoru"]=="🥈 GÜMÜŞ").sum())
    m4.metric("🔥 ACİL",   df["oncelik"].str.contains("ACİL").sum())
    m5.metric("Ort. Kompozit", f"{df['kompozit_skor'].mean():.1f}")
    m6.metric("Ort. Getiri Pot.", fp(df["ort_getiri"].mean()))

    # ── Tablar
    tab1,tab2,tab3,tab4,tab5 = st.tabs([
        "🏆 Sıralama","💎 ELMAS & ALTIN","📐 10 Model","🏭 Sektör","⚠️ Risk & Sağlık"
    ])

    ds = df.sort_values("nihai_siralama")
    PC = {
        "kompozit_skor":   st.column_config.ProgressColumn("Kompozit",min_value=0,max_value=100,format="%.1f"),
        "son_karar_skoru": st.column_config.ProgressColumn("Karar",min_value=0,max_value=100,format="%.1f"),
        "piotroski_f":     st.column_config.NumberColumn("Piotroski",format="%d /9"),
        "nihai_siralama":  st.column_config.NumberColumn("#",width="small"),
    }

    with tab1:
        sc = ["nihai_siralama","hisse_kodu","sirket_adi","kompozit_skor","son_karar_skoru",
              "piotroski_f","piotroski_label","ort_getiri","risk_label","yatirim_kategorisi",
              "oncelik","sonuc_skoru","final_tavsiye"]
        av = [c for c in sc if c in ds.columns]
        d  = ds[av].copy()
        if "ort_getiri" in d.columns:
            d["ort_getiri"] = d["ort_getiri"].apply(fp)
        st.dataframe(d, use_container_width=True, hide_index=True, height=500, column_config=PC)

    with tab2:
        el = df[df["sonuc_skoru"].str.contains("ELMAS|ALTIN",na=False)].sort_values("nihai_siralama")
        if el.empty:
            st.warning("Bu grupta ELMAS/ALTIN bulunamadı. Daha geniş havuz deneyin.")
        else:
            st.success(f"🏆 {len(el)} hisse ELMAS/ALTIN kategorisinde!")
            sc2 = ["nihai_siralama","hisse_kodu","sirket_adi","sonuc_skoru","kompozit_skor",
                   "ort_getiri","piotroski_f","piotroski_label","fiyat","ort_deger",
                   "optimum_fiyat","risk_label","oncelik","final_tavsiye","bi_yorum"]
            av2 = [c for c in sc2 if c in el.columns]
            d2  = el[av2].copy()
            if "ort_getiri" in d2.columns:
                d2["ort_getiri"] = d2["ort_getiri"].apply(fp)
            st.dataframe(d2, use_container_width=True, hide_index=True,
                column_config={**PC,
                    "fiyat":       st.column_config.NumberColumn("Fiyat",format="%.2f ₺"),
                    "ort_deger":   st.column_config.NumberColumn("Ort.Değer",format="%.2f ₺"),
                    "optimum_fiyat":st.column_config.NumberColumn("Optimum",format="%.2f ₺"),
                })

    with tab3:
        st.caption("10 farklı değerleme modeli — her model farklı bir perspektif sunar.")
        mc = ["hisse_kodu","sirket_adi","fiyat",
              "m1_pddd_deger","m2_fk_eps","m3_fk_norm","m4_recep_pddd","m5_cari_fk",
              "m6_oser","m7_graham","m8_fdfavok","m10_roe_fk","ort_deger","ort_getiri",
              "fk","pd_dd","fd_favok","eps","hbdd","roe","piotroski_f"]
        av3 = [c for c in mc if c in ds.columns]
        pfmt = "%.2f ₺"
        d3  = ds[av3].copy()
        if "ort_getiri" in d3.columns:
            d3["ort_getiri"] = d3["ort_getiri"].apply(fp)
        st.dataframe(d3, use_container_width=True, hide_index=True, height=500,
            column_config={
                "fiyat":         st.column_config.NumberColumn("Fiyat",format=pfmt),
                "m1_pddd_deger": st.column_config.NumberColumn("M1:PD/DD",format=pfmt),
                "m2_fk_eps":     st.column_config.NumberColumn("M2:F/K×EPS",format=pfmt),
                "m3_fk_norm":    st.column_config.NumberColumn("M3:F/K Norm",format=pfmt),
                "m4_recep_pddd": st.column_config.NumberColumn("M4:Recep",format=pfmt),
                "m5_cari_fk":    st.column_config.NumberColumn("M5:Cari F/K",format=pfmt),
                "m6_oser":       st.column_config.NumberColumn("M6:Öd.Ser",format=pfmt),
                "m7_graham":     st.column_config.NumberColumn("M7:Graham",format=pfmt),
                "m8_fdfavok":    st.column_config.NumberColumn("M8:FD/FAVÖK",format=pfmt),
                "m10_roe_fk":    st.column_config.NumberColumn("M10:ROE×F/K",format=pfmt),
                "ort_deger":     st.column_config.NumberColumn("Ort.Değer",format=pfmt),
                "roe":           st.column_config.NumberColumn("ROE",format="%.2f"),
                "piotroski_f":   st.column_config.NumberColumn("Piotroski",format="%d /9"),
            })

    with tab4:
        sk = df.groupby("sektor").agg(
            Hisse=("hisse_kodu","count"),
            Ort_Skor=("kompozit_skor","mean"),
            Ort_Getiri=("ort_getiri","mean"),
            Ort_FK=("fk","mean"),
            Ort_PDDD=("pd_dd","mean"),
            Ort_Piotroski=("piotroski_f","mean"),
            Elmas=("sonuc_skoru",lambda x:(x=="💎 ELMAS").sum()),
        ).sort_values("Ort_Skor",ascending=False).reset_index()
        sk["Ort_Getiri"]    = sk["Ort_Getiri"].apply(fp)
        sk["Ort_Skor"]      = sk["Ort_Skor"].round(1)
        sk["Ort_Piotroski"] = sk["Ort_Piotroski"].round(1)
        st.dataframe(sk, use_container_width=True, hide_index=True,
            column_config={"Ort_Skor":st.column_config.ProgressColumn("Ort.Skor",min_value=0,max_value=100,format="%.1f")})

    with tab5:
        rc = ["nihai_siralama","hisse_kodu","sirket_adi","risk_skoru","risk_label",
              "finansal_saglik","saglik_label","piotroski_f","piotroski_label",
              "halka_aciklik","piyasa_degeri","yatirim_kategorisi"]
        av5 = [c for c in rc if c in df.columns]
        st.dataframe(df.sort_values("nihai_siralama")[av5], use_container_width=True,
            hide_index=True, height=500,
            column_config={
                "risk_skoru":     st.column_config.NumberColumn("Risk",format="%d"),
                "finansal_saglik":st.column_config.NumberColumn("Sağlık",format="%d /12"),
                "piotroski_f":    st.column_config.NumberColumn("Piotroski",format="%d /9"),
                "halka_aciklik":  st.column_config.NumberColumn("Halka%",format="%.1f"),
                "piyasa_degeri":  st.column_config.NumberColumn("PD(MN₺)",format="%.0f"),
            })

    # CSV indirme
    st.markdown("---")
    csv = df.loc[:,~df.columns.duplicated()].to_csv(index=False).encode("utf-8")
    st.download_button("📥 Tüm Değerleme Verisini İndir (CSV)", csv, "degerleme.csv", "text/csv",
                       use_container_width=True)


def _show_explainer():
    st.markdown("""
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:16px;">
    """, unsafe_allow_html=True)
    models = [
        ("M1","PD/DD Değer","Sektör PD/DD ortalamasına göre adil değer"),
        ("M2","F/K × EPS","Sektör F/K ile normalize EPS"),
        ("M3","F/K Normalizasyon","Cari fiyatı sektör F/K ile düzeltir"),
        ("M4","Recep PD/DD","Piyasa/defter tersine dayalı değer"),
        ("M5","Cari F/K","Şirket F/K'sını sektör F/K'sıyla kıyaslar"),
        ("M6","Ödenmiş Sermaye","EPS × 10 konservatif değer"),
        ("M7","Graham Formülü","√(22.5 × EPS × BVPS) — efsane formül"),
        ("M8","FD/FAVÖK","Sektör çarpanına göre değer"),
        ("Piotroski","F-Skor","9 kriterli finansal sağlık skoru"),
        ("Kompozit","Nihai Skor","Karar%35 + Getiri%25 + Piotroski%20 + Risk%10 + Momentum%10"),
    ]
    for key, name, desc in models:
        st.markdown(f"""
        <div style="background:#111827;border:1px solid #1e2d4a;border-radius:8px;padding:12px 14px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
                <span style="background:#0066ff22;border:1px solid #0066ff44;border-radius:4px;
                    padding:2px 7px;font-family:'Space Mono',monospace;font-size:.65rem;color:#60a5fa;">
                    {key}</span>
                <span style="font-family:'Syne',sans-serif;font-weight:700;color:#e2e8f0;font-size:.8rem;">
                    {name}</span>
            </div>
            <div style="font-family:'Space Mono',monospace;font-size:.62rem;color:#64748b;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
