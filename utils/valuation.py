"""
UltraProCalculator v2 — Otomatik sektör + düzeltilmiş 10 model
"""
import numpy as np
import pandas as pd

class UltraProCalculator:
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for fn in [self._fill, self._sekort, self._buyume, self._piotroski,
                   self._degskor, self._alpha, self._sekrel, self._toplam,
                   self._modeller, self._saglik, self._risk, self._piyasa,
                   self._karar, self._yorumlar, self._nihai]:
            try:
                df = fn(df)
            except Exception:
                pass
        return df.loc[:, ~df.columns.duplicated(keep="first")]

    @staticmethod
    def _fill(df):
        numeric_cols = ["fiyat","lot_sayisi","piyasa_degeri","halka_aciklik","sermaye","fk",
                        "fd_favok","pd_dd","guncel_net_kar","onceki_net_kar","eps","hbdd",
                        "net_satis","favok","aylik_degisim","yillik_degisim"]
        for c in numeric_cols:
            if c not in df.columns: df[c] = np.nan
            else: df[c] = pd.to_numeric(df[c], errors="coerce")
        if "sirket_adi" not in df.columns: df["sirket_adi"] = df["hisse_kodu"]
        if "sektor" not in df.columns: df["sektor"] = "Diğer"
        df["sektor"] = df["sektor"].fillna("Diğer").replace("","Diğer")
        return df

    @staticmethod
    def _sekort(df):
        """Sektör ortalamalarını hesapla — NaN güvenli."""
        def safe_mean(col):
            pos = df[col].where((df[col].notna()) & (df[col] > 0))
            grp = pos.groupby(df["sektor"]).mean()
            return df["sektor"].map(grp).fillna(pos.median() or 0)

        df["sek_fk"]   = safe_mean("fk")
        df["sek_fdfa"] = safe_mean("fd_favok")
        df["sek_pddd"] = safe_mean("pd_dd")
        df["sek_pd"]   = df["sektor"].map(df.groupby("sektor")["piyasa_degeri"].mean()).fillna(0)
        df["sek_kar"]  = df["sektor"].map(df.groupby("sektor")["guncel_net_kar"].mean()).fillna(0)
        df["sek_ser"]  = df["sektor"].map(df.groupby("sektor")["sermaye"].mean()).fillna(0)

        roe_series = df["guncel_net_kar"] / df["sermaye"].replace(0, np.nan)
        df["sek_roe"] = df["sektor"].map(roe_series.groupby(df["sektor"]).mean()).fillna(0)
        return df

    @staticmethod
    def _buyume(df):
        cur = df["guncel_net_kar"]; prv = df["onceki_net_kar"]
        df["net_kar_buyume"] = np.where(
            (prv.notna())&(prv.abs()>0.001)&(cur.notna()),
            (cur - prv) / prv.abs(), np.nan)
        df["roe"] = np.where((df["sermaye"]>0.001)&(df["guncel_net_kar"]>0),
                             df["guncel_net_kar"]/df["sermaye"], np.nan)
        favok_col = df.get("favok", pd.Series(np.nan, index=df.index))
        df["favok_marji"] = np.where((df["net_satis"]>0.001)&(favok_col>0),
                                     favok_col/df["net_satis"], np.nan)
        return df

    @staticmethod
    def _piotroski(df):
        f = pd.Series(0, index=df.index)
        f += (df["guncel_net_kar"] > 0).astype(int)
        f += (df.get("roe", pd.Series(np.nan,index=df.index)) > 0).fillna(0).astype(int)
        f += (df["net_kar_buyume"] > 0).fillna(0).astype(int)
        f += (df["pd_dd"] < df["sek_pddd"]).fillna(0).astype(int)
        f += (df["halka_aciklik"] > 10).fillna(0).astype(int)
        f += (df["fk"] < df["sek_fk"]).fillna(0).astype(int)
        f += (df["net_kar_buyume"] > 0.10).fillna(0).astype(int)
        f += (df["roe"] > df["sek_roe"]).fillna(0).astype(int)
        f += (df["guncel_net_kar"] > df["onceki_net_kar"]).fillna(0).astype(int)
        df["piotroski_f"] = f
        df["piotroski_label"] = np.select(
            [f>=8, f>=6, f>=4, f>=2],
            ["🏆 GÜÇLÜ (8-9)","✅ İYİ (6-7)","⚠️ ORTA (4-5)","🔍 ZAYIF (2-3)"],
            default="⛔ KRİTİK (0-1)")
        return df

    @staticmethod
    def _degskor(df):
        fk=df["fk"]; sfk=df["sek_fk"]; fd=df["fd_favok"]; sfd=df["sek_fdfa"]
        pd_=df["pd_dd"]; spd=df["sek_pddd"]; bym=df["net_kar_buyume"]
        roe=df.get("roe",pd.Series(0,index=df.index)); pio=df["piotroski_f"]
        # Geçerli sektör ortalaması var mı?
        valid_sector = (sfk.notna()) & (sfk > 0)
        q = (np.where(valid_sector & (fk<sfk), 25, np.where(valid_sector & (fk<sfk*1.2), 15, 5)) +
             np.where((sfd>0)&(fd<sfd), 25, np.where((sfd>0)&(fd<sfd*1.2), 15, 5)) +
             np.where((spd>0)&(pd_<spd), 20, np.where((spd>0)&(pd_<spd*1.2), 10, 5)) +
             np.where(bym>0.2, 20, np.where(bym>0, 10, np.where(bym<-0.2, -10, 0))) +
             np.where(roe>0.20, 10, np.where(roe>0.10, 5, 0)) +
             np.where(pio>=7, 10, np.where(pio>=5, 5, 0)))
        df["degerleme_skoru"] = pd.Series(q, index=df.index).clip(0, 100).fillna(0)
        return df

    @staticmethod
    def _alpha(df):
        ay=df["aylik_degisim"].fillna(0); yil=df["yillik_degisim"].fillna(0)
        bym=df["net_kar_buyume"].fillna(0); pio=df["piotroski_f"]
        r = (np.where(ay>0.10,5,np.where(ay>0.05,4,np.where(ay>0,2,0))) +
             np.where(yil>0.30,4,np.where(yil>0.20,3,np.where(yil>0,1,0))) +
             np.where(bym>0.50,3,np.where(bym>0.20,2,np.where(bym>0,1,0))) +
             np.where(pio>=7,2,np.where(pio>=5,1,0)))
        df["alpha_skor"] = r
        df["sek_degval"] = df["sektor"].map(df.groupby("sektor")["degerleme_skoru"].mean()).fillna(0)
        df["sek_alpha"]  = df["sektor"].map(df.groupby("sektor")["alpha_skor"].mean()).fillna(0)
        df["alpha_yon"]  = np.where(df["aylik_degisim"]>0,"📈 POZİTİF","📉 NEGATİF")
        return df

    @staticmethod
    def _sekrel(df):
        fk=df["fk"]; sfk=df["sek_fk"]; pd_=df["pd_dd"]; spd=df["sek_pddd"]
        s = (np.where((fk>0)&(sfk>0)&(fk<sfk),10,np.where((fk>0)&(sfk>0)&(fk<sfk*1.2),5,0)) +
             np.where((pd_>0)&(spd>0)&(pd_<spd),10,np.where((pd_>0)&(spd>0)&(pd_<spd*1.2),5,0)))
        df["sektor_relatif"] = pd.Series(s, index=df.index).fillna(0)
        return df

    @staticmethod
    def _toplam(df):
        df["toplam_skor"] = (
            df["degerleme_skoru"]*0.45 +
            df["alpha_skor"]*10*0.25 +
            df["sektor_relatif"]*0.15*(100/20) +
            df["piotroski_f"]*10*0.15
        ).clip(0,100)
        df["siralama"] = df["toplam_skor"].rank(ascending=False, method="min").astype(int)
        return df

    @staticmethod
    def _modeller(df):
        """
        10 değerleme modeli — NaN güvenli.
        Sektör ortalaması yoksa piyasa geneli ortalaması kullanılır.
        """
        c   = df["fiyat"]
        eps = df["eps"]
        hbdd= df["hbdd"]
        fk  = df["fk"]
        sfk = df["sek_fk"].where(df["sek_fk"]>0, df["fk"].median())  # fallback: medyan
        pd_ = df["pd_dd"]
        spd = df["sek_pddd"].where(df["sek_pddd"]>0, df["pd_dd"].median())
        fd  = df["fd_favok"]
        sfd = df["sek_fdfa"].where(df["sek_fdfa"]>0, df["fd_favok"].median())
        nk  = df["guncel_net_kar"]
        ser = df["sermaye"]

        # M1: PD/DD değer — sektör PD/DD ile normalize
        df["m1_pddd_deger"] = np.where(
            (c>0)&(pd_>0)&(spd>0) & (pd_!=spd),
            (c/pd_)*spd, np.nan)

        # M2: F/K × EPS — sektör F/K ile beklenen fiyat
        df["m2_fk_eps"] = np.where(
            (eps.notna())&(eps>0)&(sfk.notna())&(sfk>0),
            eps*sfk, np.nan)

        # M3: F/K Normalizasyon — cari fiyatı sektör F/K ile düzelt
        df["m3_fk_norm"] = np.where(
            (fk>0)&(sfk>0)&(c>0)&(fk!=sfk),
            (c/fk)*sfk, np.nan)

        # M4: Defter değeri bazlı — hisse başı defter × ortalama PD/DD
        df["m4_defter"] = np.where(
            (hbdd.notna())&(hbdd>0)&(spd.notna())&(spd>0),
            hbdd*spd, np.nan)

        # M5: Kazanç gücü — normalize EPS × sektör büyüme çarpanı
        büyüme_çarpan = df["net_kar_buyume"].clip(-0.5, 2.0).fillna(0) + 1.0
        df["m5_kazanc"] = np.where(
            (eps.notna())&(eps>0)&(sfk>0),
            eps * sfk * büyüme_çarpan, np.nan)

        # M6: Ödenmiş sermaye değeri (Konservatif)
        df["m6_oser"] = np.where(eps>0, np.maximum(0, eps*10), np.nan)

        # M7: Graham Formülü — √(22.5 × EPS × BVPS)
        df["m7_graham"] = np.where(
            (eps.notna())&(eps>0)&(hbdd.notna())&(hbdd>0),
            np.sqrt(22.5 * eps * hbdd), np.nan)

        # M8: FD/FAVÖK değeri
        df["m8_fdfavok"] = np.where(
            (fd.notna())&(fd>0)&(sfd.notna())&(sfd>0)&(c>0)&(fd!=sfd),
            (c/fd)*sfd, np.nan)

        # M9: ROE × Defter → Fiyat tahmini
        roe = df.get("roe", pd.Series(np.nan, index=df.index))
        df["m9_roe_defter"] = np.where(
            (roe.notna())&(roe>0)&(hbdd.notna())&(hbdd>0),
            roe * hbdd * 10, np.nan)  # 10 = konservatif çarpan

        # M10: Piyasa değeri / Net kâr çarpanı
        df["m10_roe_fk"] = np.where(
            (nk.notna())&(nk>0)&(fk.notna())&(fk>0)&(ser.notna())&(ser>0),
            (nk*fk)/ser, np.nan)

        # Ortalamalar — en az 2 model geçerli olmalı
        vc = ["m1_pddd_deger","m2_fk_eps","m3_fk_norm","m4_defter",
              "m5_kazanc","m6_oser","m7_graham","m8_fdfavok","m9_roe_defter","m10_roe_fk"]
        vdf = df[vc].where(df[vc] > 0)

        # Aşırı değerleri filtrele (fiyatın 10 katından fazla olanlar)
        for col in vc:
            vdf[col] = vdf[col].where(vdf[col] < c * 10)

        valid_count = vdf.notna().sum(axis=1)
        df["ort_deger"]  = np.where(valid_count >= 2, vdf.mean(axis=1), np.nan)
        df["min_deger"]  = np.where(valid_count >= 2, vdf.min(axis=1), np.nan)
        df["max_deger"]  = np.where(valid_count >= 2, vdf.max(axis=1), np.nan)
        df["model_count"]= valid_count

        df["ort_getiri"] = np.where(
            (df["ort_deger"].notna())&(df["ort_deger"]>0)&(c>0),
            (df["ort_deger"]-c)/c, np.nan)
        df["tum_deger_getiri"] = df["ort_getiri"]
        return df

    @staticmethod
    def _saglik(df):
        fk=df["fk"]; pd_=df["pd_dd"]; bym=df["net_kar_buyume"].fillna(0); pio=df["piotroski_f"]
        df["finansal_saglik"] = (
            np.where(fk>0,np.where(fk<5,3,np.where(fk<10,2,np.where(fk<15,1,0))),0) +
            np.where(pd_>0,np.where(pd_<0.5,3,np.where(pd_<1,2,np.where(pd_<2,1,0))),0) +
            np.where(bym>0.2,3,np.where(bym>0,2,np.where(bym>-0.1,1,0))) +
            np.where(pio>=7,2,np.where(pio>=5,1,0))
        )
        df["temel_skor"] = (
            (df["guncel_net_kar"]>0).astype(int) +
            (df["net_kar_buyume"]>0).fillna(0).astype(int) +
            (df["pd_dd"]<df["sek_pddd"]).fillna(0).astype(int) +
            (df["fk"]<df["sek_fk"]).fillna(0).astype(int) +
            (df["fd_favok"]<df["sek_fdfa"]).fillna(0).astype(int) +
            (df["piotroski_f"]>=6).astype(int)
        )
        return df

    @staticmethod
    def _risk(df):
        lot=df["lot_sayisi"].fillna(1e8)
        ha=df["halka_aciklik"].fillna(20)
        bym=df["net_kar_buyume"].fillna(0)
        yil=df.get("yillik_degisim",pd.Series(0,index=df.index)).fillna(0)
        cb = (
            np.where(lot<1e6,5,np.where(lot<5e6,4,np.where(lot<20e6,3,np.where(lot<50e6,2,1)))) +
            np.where(ha<5,4,np.where(ha<15,3,np.where(ha<30,2,1))) +
            np.where(bym<-0.2,5,np.where(bym<0,3,1)) +
            np.where(yil<-0.3,4,np.where(yil<-0.1,3,1))
        )
        df["risk_skoru"]  = pd.Series(cb, index=df.index).fillna(15)
        df["getiri_risk"] = np.where(
            (df["ort_getiri"].notna())&(df["risk_skoru"]>0),
            df["ort_getiri"]/(df["risk_skoru"]/20), 0)
        return df

    @staticmethod
    def _piyasa(df):
        bko = df["piyasa_degeri"].median()
        bkk = df["guncel_net_kar"].median()
        bm  = (bko/bkk) if (bkk and bkk>0.001) else np.nan
        df["bn_deger"] = np.where(df["guncel_net_kar"]>0, df["guncel_net_kar"]*bm, np.nan)
        df["bv_genel_yorum"] = np.where(
            (df["guncel_net_kar"]>0)&(df["bn_deger"]>df["piyasa_degeri"])&(df["piyasa_degeri"]<bko),
            "🚀 GENEL ELMAS",
            np.where((df["guncel_net_kar"]>0)&(df["piyasa_degeri"]<bko),"⏳ POTANSİYEL",
                     np.where(df["guncel_net_kar"]<=0,"🔴 ZARARDA","✅ DEĞERİNDE")))
        return df

    @staticmethod
    def _karar(df):
        ts=df["toplam_skor"]; og=df["ort_getiri"].fillna(0)
        tsk=df["temel_skor"]; pio=df["piotroski_f"]
        ca = (
            np.where(ts>=80,25,np.where(ts>=60,15,np.where(ts>=40,5,0))) +
            np.where(og>0.3,25,np.where(og>0.2,20,np.where(og>0.1,15,np.where(og>0,10,0)))) +
            np.where(tsk>=5,25,np.where(tsk>=4,20,np.where(tsk==3,12,np.where(tsk==2,5,0)))) +
            np.where(pio>=8,5,np.where(pio>=6,3,0))
        )
        df["son_karar_skoru"] = pd.Series(ca, index=df.index).clip(0,100).fillna(0)
        df["sonuc_skoru"] = np.where(
            (og>0.4)&(tsk>=5)&(pio>=7),"💎 ELMAS",
            np.where((og>0.2)&(tsk>=4),"⭐ ALTIN",
                     np.where(og>0,"🥈 GÜMÜŞ","📋 İZLEME")))
        df["oncelik"] = np.where(
            df["son_karar_skoru"]>=75,"🔥 ACİL ALIM",
            np.where(df["son_karar_skoru"]>=60,"✅ KADEMELİ AL",
                     np.where(df["son_karar_skoru"]>=50,"👁️ İZLEME","⬛ DİĞER")))
        df["optimum_fiyat"] = np.where(
            (df["fiyat"]>0)&(df["ort_deger"].notna())&(df["ort_deger"]>0),
            df["fiyat"]*0.65 + df["ort_deger"]*0.35, np.nan)
        return df

    @staticmethod
    def _yorumlar(df):
        def bi(row):
            t=row.get("toplam_skor",0) or 0; pio=row.get("piotroski_f",0) or 0
            mc=row.get("model_count",0) or 0
            if mc < 2: return "Yetersiz veri: Temel finansal veriler eksik."
            if t>=85 and pio>=7: return "GÜÇLÜ AL: Temel+Momentum+Piotroski mükemmel."
            if t>=75: return "AL: İskontolu ve hareket başlamış."
            if t>=60: return "KADEMELİ AL: Ucuz ama piyasa henüz fark etmemiş."
            if t>=45: return "NÖTR: Sektör ortalamasında."
            return "DİKKAT: Pahalı veya negatif momentum."

        def ft(row):
            ca=row.get("son_karar_skoru",0) or 0
            og=row.get("ort_getiri",0) or 0
            mc=row.get("model_count",0) or 0
            opt=row.get("optimum_fiyat",0) or 0
            fiy=row.get("fiyat",0) or 0
            pio=row.get("piotroski_f",0) or 0
            cb=row.get("risk_skoru",15) or 15
            if mc < 2:
                return "📊 YETERSİZ VERİ — Finansal tablolar eksik"
            if ca>=75 and cb<=10 and og>0.3 and pio>=6:
                s = "🔥 YÜKSEK GÜVENİLİRLİK — GÜÇLÜ AL"
                s += (f" (OPTİMUM: {opt:.2f} ₺)" if opt>fiy>0 else " (ALINABİLİR)")
            elif ca>=65: s = "✅ ORTA-YÜKSEK — KADEMELİ AL"
            elif ca>=55: s = "🟡 ORTA — İZLE"
            elif ca>=45: s = "⚠️ DÜŞÜK — DİKKAT"
            else: s = "⛔ YÜKSEK RİSK / DİĞER"
            return s

        df["bi_yorum"]      = df.apply(bi, axis=1)
        df["final_tavsiye"] = df.apply(ft, axis=1)
        df["saglik_label"]  = pd.cut(df["finansal_saglik"], bins=[-1,2,4,6,8,100],
            labels=["⛔ KRİTİK","🔍 ZAYIF","⚠️ ORTA","👍 SAĞLAM","💪 ÇOK SAĞLAM"]).astype(str)
        df["risk_label"] = pd.cut(df["risk_skoru"], bins=[-1,8,12,15,100],
            labels=["🟢 DÜŞÜK","🟡 ORTA","🟠 YÜKSEK","🔴 ÇOK YÜKSEK"]).astype(str)
        return df

    @staticmethod
    def _nihai(df):
        def norm(s):
            mn,mx = s.min(), s.max()
            return pd.Series(50, index=s.index) if (mx-mn)<0.001 else (s-mn)/(mx-mn)*100
        komp = (
            norm(df["son_karar_skoru"].fillna(0))*0.35 +
            norm(df["ort_getiri"].fillna(0).clip(-1,5))*0.25 +
            norm(df["piotroski_f"].fillna(0))*0.20 +
            norm(100-df["risk_skoru"].fillna(15))*0.10 +
            norm(df["alpha_skor"].fillna(0))*0.10
        )
        df["kompozit_skor"]  = komp.clip(0,100)
        df["nihai_siralama"] = df["kompozit_skor"].rank(ascending=False,method="min").astype(int)
        df["yatirim_kategorisi"] = np.select(
            [(df["nihai_siralama"]<=3)&(df["sonuc_skoru"]=="💎 ELMAS"),
             df["nihai_siralama"]<=5, df["nihai_siralama"]<=10,
             df["oncelik"].str.contains("ACİL|KADEMELİ",na=False)],
            ["🥇 PORTFÖY LİDERİ","🎯 ÖNCE ALINANLAR","📌 YAKINDA AL","👁️ TAKİP"],
            default="⏳ BEKLE")
        return df
