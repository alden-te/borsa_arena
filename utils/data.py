"""
Veri Motoru v3 — Tam Otomatik
==============================
Hisse listesi, isim, sektör → 3 katmanlı otomatik sistem:
  Katman 1: tradingview_screener  (500+ hisse + sektör, prod'da)
  Katman 2: yfinance .info        (sektör, isim)
  Katman 3: Zengin statik fallback (448 hisse)

Dışarıda kullanılan tüm değişkenler:
  _FALLBACK, BIST_ALL, BIST100, BIST100_TICKERS,
  BIST30, STOCK_NAMES, SECTOR_MAP, INDEX_GROUPS
  get_name(), bist_ticker()
  get_stock_data(), get_multi_stock_close()
  get_market_overview(), get_bist_snapshot()
  BISTDataFetcher
"""

import re, time, requests
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Dict

# ══════════════════════════════════════════════════════════════
# STATIK FALLBACK — 448 hisse (kaynak koddan alındı)
# ══════════════════════════════════════════════════════════════
_FALLBACK: List[str] = sorted([
    "ACSEL","ADEL","AEFES","AFYON","AGESA","AGHOL","AGYO","AKBNK","AKCNS",
    "AKFGY","AKGRT","AKSA","AKSEN","AKSGY","ALARK","ALBRK","ALCAR","ALCTL",
    "ALFAS","ALGYO","ALKIM","ALTNY","ALVES","ANELE","ANGEN","ANHYT","ANSGR",
    "ARCLK","ARDYZ","ARENA","ARSAN","ARTMS","ARZUM","ASELS","ASGYO","ASTOR",
    "ATAGY","ATAKP","ATATP","ATEKS","ATLAS","AVHOL","AVOD","AVTUR","AYCES",
    "AYDEM","AYEN","AYGAZ","BAGFS","BAKAB","BALAT","BANVT","BARMA","BASGZ",
    "BAYRK","BEGYO","BERA","BFREN","BIMAS","BIOEN","BIOGR","BIZIM","BJKAS",
    "BLCYT","BNTAS","BOSSA","BRISA","BRKO","BRMEN","BRKVY","BRSAN","BRYAT",
    "BSOKE","BTCIM","BUCIM","BURCE","BURVA","BUYUK","BVSAN","CANTE","CASA",
    "CEMAS","CEMTS","CIMSA","CLEBI","CMBTN","CONSE","COSMO","CRDFA","CRFSA",
    "CUSAN","CVKMD","CWENE","DAGHL","DAGI","DARDL","DENGE","DENIZ","DERIM",
    "DESA","DESPC","DEVA","DITAS","DMSAS","DOAS","DOBUR","DOCO","DOHOL",
    "DOKTA","DURDO","DYOBY","DZGYO","ECILC","ECZYT","EDATA","EDIP","EFORC",
    "EGEEN","EGGUB","EGPRO","EGSER","EKGYO","EKSUN","ELITE","EMKEL","EMNIS",
    "ENERY","ENGYO","ENKAI","ENPLU","EPLAS","ERBOS","EREGL","ERGLI","ESCAR",
    "ESCOM","ESEN","ETILR","ETYAT","EUHOL","EUPWR","EUREN","EUYO","FENER",
    "FLAP","FONET","FORMT","FORTE","FRIGO","FROTO","FZLGY","GARAN","GARFA",
    "GEDIK","GEDZA","GENTS","GEREL","GESAN","GIPTA","GLBMD","GLCVY","GLRYH",
    "GLYHO","GMTAS","GOKNR","GOLTS","GOODY","GOZDE","GRSEL","GRTRK","GSDDE",
    "GSDHO","GSRAY","GUBRF","GUNDG","GUNES","GUSGR","GWIND","GZNMI","HALKB",
    "HATEK","HEDEF","HEKTS","HKTM","HLGYO","HTTBT","HUBVC","HURGZ","ICBCT",
    "IDEAS","IDGYO","IEYHO","IHLGM","IHLAS","IHYAY","IMASM","INDES","INFO",
    "INTEM","INVEO","INVES","IPEKE","ISBIR","ISCTR","ISFIN","ISGSY","ISGYO",
    "ISKPL","ISMEN","ISYAT","ITTFK","IZENR","IZFAS","IZGYO","IZINV","IZMDC",
    "JANTS","KAPLM","KAREL","KARSN","KARTN","KATMR","KBORU","KCAER","KCHOL",
    "KERVN","KERVT","KGYO","KLGYO","KLKIM","KLMSN","KLNMA","KMPUR","KNFRT",
    "KOCMT","KONKA","KONTR","KONYA","KOPOL","KORDS","KOTON","KOZAA","KOZAL",
    "KRDMA","KRDMB","KRDMD","KRGYO","KRSTL","KRTEK","KRVGD","KSTUR","KTSKR",
    "KUTPO","KUVVA","KUYAS","LIDER","LIDFA","LIFEZ","LKMNH","LRSHO","MAALT",
    "MACKO","MAGEN","MAKIM","MAKTK","MANAS","MARBL","MARKA","MARTI","MAVI",
    "MEDTR","MEGAP","MEPET","MERCN","MERIT","MERKO","METRO","METUR","MGROS",
    "MIATK","MIPAZ","MNDRS","MNDTR","MOBTL","MOGAN","MPARK","MRSHL","MSGLD",
    "MTRKS","MTRYO","MUTLU","NATEN","NETAS","NETHL","NIBAS","NILYT","NKHOL",
    "NNDNG","NTHOL","NTTUR","NUGYO","NUHCM","OBASE","ODAS","ODINE","OFSYM",
    "ONCSM","ONRYT","ORCAY","ORGE","ORMA","OSMEN","OSTIM","OTKAR","OTTO",
    "OYAKC","OYAYO","OYLUM","OYYAT","OZGYO","OZKGY","OZRDN","OZSUB","PAGYO",
    "PAMEL","PAPIL","PAREG","PARSN","PASEU","PEGYO","PEKGY","PENTA","PETKM",
    "PETUN","PGSUS","PKART","PKENT","PLTUR","PNLSN","POLHO","POLTK","PRKAB",
    "PRKME","PRZMA","PSDTC","PSGYO","QNBFB","QNBFL","RAYSG","RNPOL","RODRG",
    "ROYAL","RTALB","RUBNS","RYGYO","SAFKR","SAHOL","SAMAT","SANEL","SANFM",
    "SANKO","SARKY","SASA","SAYAS","SEGYO","SEKFK","SEKUR","SELEC","SELVA",
    "SEYKM","SISE","SKBNK","SMRTG","SNGYO","SNICA","SNKRN","SNPAM","SOKM",
    "SONME","SRVGY","SUNTK","SUWEN","TABGD","TACTR","TATGD","TAVHL","TBORG",
    "TCELL","TCKRC","TDGYO","TEKTU","TEZOL","THYAO","TKFEN","TKNSA",
    "TLMAN","TMPOL","TMSN","TOASO","TPGYO","TRGYO","TRILC","TSGYO",
    "TSKB","TSPOR","TTKOM","TTRAK","TUKAS","TUPRS","TUREX","TURGG","ULUFA",
    "ULUSE","ULYGT","ULUUN","UMPAS","UNLU","USAK","UTPYA","UZERB","VAKBN",
    "VAKFB","VAKKO","VANGD","VBTS","VERTU","VERUS","VESTL","VKFYO","VKGYO",
    "VKING","VRGYO","WINTA","YAPRK","YATAS","YBTAS","YEOTK","YESIL","YGGYO",
    "YKBNK","YKSLN","YONGA","YUNSA","YYLGD","ZEDUR","ZOREN","ZRGYO","SODA",
    "AKBNK","GARAN","ISCTR","HALKB","VAKBN","PGSUS","FROTO","BIMAS",
])
_FALLBACK = sorted(list(set(_FALLBACK)))

# ── BIST 30 ──────────────────────────────────────────────────
BIST30: List[str] = [
    "AKBNK","ARCLK","ASELS","BIMAS","EKGYO","EREGL","FROTO","GARAN",
    "HALKB","ISCTR","KCHOL","KOZAL","KRDMD","PETKM","PGSUS","SAHOL",
    "SISE","TAVHL","TCELL","THYAO","TKFEN","TOASO","TTKOM","TUPRS",
    "ULKER","VAKBN","VESTL","YKBNK","ZRGYO","SODA",
]

# ── Alias'lar (diğer modüller bunu import eder) ───────────────
BIST100: List[str]        = _FALLBACK[:100]
BIST_ALL: List[str]       = _FALLBACK          # tüm liste
BIST100_TICKERS: Dict[str,str] = {}            # sembol → isim (aşağıda doldurulur)

# ── Statik isim haritası (yfinance çekemeyince fallback) ──────
_STATIC_NAMES: Dict[str,str] = {
    "AKBNK":"Akbank","GARAN":"Garanti BBVA","ISCTR":"İş Bankası",
    "YKBNK":"Yapı Kredi","HALKB":"Halk Bankası","VAKBN":"Vakıfbank",
    "THYAO":"Türk Hava Yolları","ASELS":"Aselsan","BIMAS":"BİM",
    "EREGL":"Ereğli Demir","KOZAL":"Koza Altın","PGSUS":"Pegasus",
    "SISE":"Şişe Cam","TOASO":"Tofaş","FROTO":"Ford Otosan",
    "KCHOL":"Koç Holding","SAHOL":"Sabancı Holding","TCELL":"Turkcell",
    "TUPRS":"Tüpraş","ARCLK":"Arçelik","KORDS":"Kordsa",
    "MGROS":"Migros","PETKM":"Petkim","SODA":"Soda Sanayii",
    "TTKOM":"Türk Telekom","ULKER":"Ülker","VESTL":"Vestel",
    "ZRGYO":"Ziraat GYO","EKGYO":"Emlak Konut GYO","NETAS":"Netaş",
    "TAVHL":"TAV Havalimanları","AEFES":"Anadolu Efes","DOAS":"Doğuş Otomotiv",
    "ENKAI":"Enka İnşaat","GUBRF":"Gübre Fab.","HEKTS":"Hektaş",
    "KRDMD":"Kardemir D","TKFEN":"Tekfen Holding","ALKIM":"Alkim Kimya",
    "LOGO":"Logo Yazılım","MAVI":"Mavi Giyim","MPARK":"MLP Sağlık",
    "OTKAR":"Otokar","SKBNK":"Şekerbank","TTRAK":"Türk Traktör",
    "AGHOL":"AG Anadolu Grubu","BJKAS":"Beşiktaş JK","FENER":"Fenerbahçe SK",
    "GSRAY":"Galatasaray SK","BRYAT":"Borusan Yatırım","TSKB":"TSKB",
    "DEVA":"Deva Holding","SELEC":"Selçuk Ecza","SOKM":"Şok Marketler",
    "BRISA":"Brisa","KOZAA":"Koza Anadolu Metal","KRDMA":"Kardemir A",
    "KRDMB":"Kardemir B","SASA":"Sasa Polyester","ODAS":"Odaş Elektrik",
    "AKSEN":"Aksa Enerji","AYDEM":"Aydem Enerji","AYEN":"Ayen Enerji",
    "ZOREN":"Zorlu Enerji","CVKMD":"ÇVK Madencilik","TKFEN":"Tekfen",
    "ISCTR":"İş Bankası C","GLYHO":"Global Yatırım","DOHOL":"Doğan Holding",
    "QNBFB":"QNB Finans","ICBCT":"ICBC Turkey","ISGYO":"İş GYO",
    "TRGYO":"Torunlar GYO","OZGYO":"Özderici GYO","ALGYO":"Alarko GYO",
    "ATAGY":"ATA GYO","HLGYO":"Halk GYO","ARENA":"Arena BT",
    "INDES":"İndeks Bilgisayar","ARDYZ":"Ardyz","NUHCM":"Nuh Çimento",
    "CIMSA":"Çimsa","AKCNS":"Akçansa","BSOKE":"Batısöke Çimento",
    "ADEL":"Adel Kalemcilik","ARZUM":"Arzum","ARSAN":"Arsan Tekstil",
    "MNDRS":"Menderes Tekstil","ATEKS":"Altınyıldız Tekstil",
    "BANVT":"Banvit","TATGD":"Tat Gıda","TUKAS":"Tukaş","MERKO":"Merko Gıda",
    "AEFES":"Anadolu Efes","ULKER":"Ülker Bisküvi","PENTA":"Penta Teknoloji",
    "KAREL":"Karel Elektronik","ALBRK":"Albaraka Türk",
    "YMPAS":"Yimpaş Holding", "ANHYT":"Anadolu Hayat Emeklilik",
    "AKGRT":"Aksigorta","ANSGR":"Anadolu Sigorta",
}
STOCK_NAMES: Dict[str,str] = _STATIC_NAMES.copy()

# ── Statik sektör haritası (fallback) ────────────────────────
_STATIC_SECTOR: Dict[str,str] = {
    # Bankacılık
    "AKBNK":"Bankacılık","GARAN":"Bankacılık","ISCTR":"Bankacılık",
    "YKBNK":"Bankacılık","HALKB":"Bankacılık","VAKBN":"Bankacılık",
    "SKBNK":"Bankacılık","ALBRK":"Bankacılık","ICBCT":"Bankacılık",
    "QNBFB":"Bankacılık","QNBFL":"Bankacılık","TSKB":"Bankacılık",
    # Havacılık / Ulaşım
    "THYAO":"Havacılık","PGSUS":"Havacılık","TAVHL":"Havacılık","CLEBI":"Havacılık",
    # Savunma
    "ASELS":"Savunma","RODRG":"Savunma",
    # Perakende / Gıda
    "BIMAS":"Perakende","MGROS":"Perakende","SOKM":"Perakende",
    "CRFSA":"Perakende","MAVI":"Perakende",
    "ULKER":"Gıda/İçecek","AEFES":"Gıda/İçecek","TATGD":"Gıda/İçecek",
    "BANVT":"Gıda/İçecek","MERKO":"Gıda/İçecek","TUKAS":"Gıda/İçecek",
    # Otomotiv / Sanayi
    "TOASO":"Otomotiv","FROTO":"Otomotiv","OTKAR":"Otomotiv",
    "TTRAK":"Otomotiv","DOAS":"Otomotiv","BRISA":"Otomotiv",
    "EREGL":"Demir-Çelik","KRDMD":"Demir-Çelik","KRDMA":"Demir-Çelik","KRDMB":"Demir-Çelik",
    "ARCLK":"Elektronik/Beyaz Eşya","VESTL":"Elektronik/Beyaz Eşya",
    "BOSSA":"Tekstil","ARSAN":"Tekstil","MNDRS":"Tekstil","ATEKS":"Tekstil",
    # Holding
    "KCHOL":"Holding","SAHOL":"Holding","AGHOL":"Holding","TKFEN":"Holding",
    "ENKAI":"Holding","GLYHO":"Holding","DOHOL":"Holding","BRYAT":"Holding",
    # Telecom
    "TCELL":"Telecom","TTKOM":"Telecom","NETAS":"Telecom",
    # Enerji
    "TUPRS":"Enerji","PETKM":"Enerji","AKSEN":"Enerji","ODAS":"Enerji",
    "AYDEM":"Enerji","AYEN":"Enerji","ZOREN":"Enerji","AYGAZ":"Enerji",
    # Cam / Kimya
    "SISE":"Cam/Kimya","SODA":"Cam/Kimya","ALKIM":"Cam/Kimya","GUBRF":"Cam/Kimya",
    "DYOBY":"Cam/Kimya","EPLAS":"Cam/Kimya","BAGFS":"Cam/Kimya",
    # Çimento / İnşaat
    "NUHCM":"Çimento","CIMSA":"Çimento","AKCNS":"Çimento","BSOKE":"Çimento",
    "BTCIM":"Çimento","BUCIM":"Çimento","ADANA":"Çimento",
    # GYO
    "ZRGYO":"GYO","EKGYO":"GYO","TRGYO":"GYO","ISGYO":"GYO",
    "OZGYO":"GYO","ALGYO":"GYO","ATAGY":"GYO","HLGYO":"GYO",
    "KLGYO":"GYO","NUGYO":"GYO","VKGYO":"GYO","RYGYO":"GYO",
    # Madencilik
    "KOZAL":"Madencilik","KOZAA":"Madencilik","CVKMD":"Madencilik",
    "KRDMD":"Madencilik",
    # Yazılım / BT
    "LOGO":"Yazılım/BT","INDES":"Yazılım/BT","ARDYZ":"Yazılım/BT",
    "ARENA":"Yazılım/BT","FONET":"Yazılım/BT","KAREL":"Yazılım/BT",
    # Sağlık
    "MPARK":"Sağlık","SELEC":"Sağlık","DEVA":"Sağlık","ECILC":"Sağlık",
    # Sigortacılık
    "AKGRT":"Sigortacılık","ANSGR":"Sigortacılık","ANHYT":"Sigortacılık",
    "GUSGR":"Sigortacılık","AVHOL":"Sigortacılık",
    # Spor
    "BJKAS":"Spor Kulüpleri","FENER":"Spor Kulüpleri",
    "GSRAY":"Spor Kulüpleri","TSPOR":"Spor Kulüpleri",
}

# ── Sektör haritası (sektör → hisseler) ──────────────────────
SECTOR_MAP: Dict[str, List[str]] = {}
for _sym, _sec in _STATIC_SECTOR.items():
    SECTOR_MAP.setdefault(_sec, []).append(_sym)

# ── INDEX_GROUPS ─────────────────────────────────────────────
INDEX_GROUPS: Dict[str, List[str]] = {
    "BIST 30":  BIST30,
    "BIST 100": _FALLBACK[:100],
    "BIST TÜM": _FALLBACK,
}

# BIST100_TICKERS doldur (sembol → isim)
BIST100_TICKERS = {s: _STATIC_NAMES.get(s, s) for s in _FALLBACK[:100]}

# ══════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ══════════════════════════════════════════════════════════════
def get_name(sym: str) -> str:
    """Sembol için okunabilir isim döner."""
    return STOCK_NAMES.get(sym, sym)

def bist_ticker(sym: str) -> str:
    """BIST sembolünü yfinance formatına çevirir."""
    return sym if sym.endswith(".IS") else f"{sym}.IS"

# ══════════════════════════════════════════════════════════════
# OTOMATİK SEMBOL & SEKTÖR GÜNCELLEME
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_live_symbol_data() -> pd.DataFrame:
    """
    Prodüksiyon ortamında TradingView'dan canlı hisse + sektör + isim çeker.
    Başarısız olursa statik veriye düşer.
    Dönen DF kolonları: symbol, name, sector
    """
    # --- Katman 1: tradingview_screener ---
    try:
        from tradingview_screener import Query
        count, df = (Query()
            .set_markets("turkey")
            .select("name", "description", "sector", "industry", "close",
                    "market_cap_basic", "volume")
            .limit(700)
            .get_scanner_data())
        if df is not None and len(df) > 50:
            df = df.rename(columns={"name": "symbol", "description": "full_name"})
            df["symbol"] = df["symbol"].str.replace("BIST:", "", regex=False).str.strip()
            df = df[df["symbol"].str.match(r"^[A-Z]{2,6}$", na=False)]
            df["name"]   = df.get("full_name", df["symbol"])
            df["sector"] = df.get("sector", "Diğer").fillna("Diğer")
            return df[["symbol", "name", "sector"]].drop_duplicates("symbol").reset_index(drop=True)
    except Exception:
        pass

    # --- Katman 2: isyatirim.com.tr ---
    try:
        from bs4 import BeautifulSoup
        url  = "https://www.isyatirim.com.tr/tr-tr/analiz/hisse/Sayfalar/Temel-Degerler-Ve-Oranlar.aspx"
        resp = requests.get(url, timeout=15,
                            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        soup = BeautifulSoup(resp.text, "lxml")
        for tbl in soup.find_all("table"):
            try:
                df_tbl = pd.read_html(str(tbl), header=0)[0]
                for col in df_tbl.columns[:3]:
                    m = df_tbl[col].astype(str).str.match(r"^[A-Z]{2,6}$", na=False)
                    if m.sum() > 50:
                        symbols = df_tbl[col][m].str.upper().unique().tolist()
                        return pd.DataFrame({
                            "symbol": sorted(symbols),
                            "name":   [_STATIC_NAMES.get(s, s) for s in sorted(symbols)],
                            "sector": [_STATIC_SECTOR.get(s, "Diğer") for s in sorted(symbols)],
                        })
            except Exception:
                continue
    except Exception:
        pass

    # --- Katman 3: Statik fallback ---
    return pd.DataFrame({
        "symbol": _FALLBACK,
        "name":   [_STATIC_NAMES.get(s, s)   for s in _FALLBACK],
        "sector": [_STATIC_SECTOR.get(s, "Diğer") for s in _FALLBACK],
    })


@st.cache_data(ttl=3600, show_spinner=False)
def get_bist_symbols(max_hisse: int = 800) -> List[str]:
    """Güncel BIST sembol listesi."""
    df = fetch_live_symbol_data()
    syms = df["symbol"].tolist()[:max_hisse]
    return syms if len(syms) > 50 else _FALLBACK[:max_hisse]


def get_all_symbols() -> List[str]:
    return _FALLBACK


def enrich_stock_names():
    """
    STOCK_NAMES ve BIST100_TICKERS'ı canlı veriyle günceller.
    app.py başlangıcında bir kez çağrılır.
    """
    global STOCK_NAMES, BIST100_TICKERS
    try:
        df = fetch_live_symbol_data()
        for _, row in df.iterrows():
            sym = row["symbol"]
            nm  = row.get("name", sym)
            if isinstance(nm, str) and nm.strip() and nm != sym:
                STOCK_NAMES[sym] = nm
        BIST100_TICKERS = {s: STOCK_NAMES.get(s, s) for s in _FALLBACK[:100]}
    except Exception:
        pass


def get_sector(sym: str) -> str:
    """Sembol için sektör döner — önce canlı veri, sonra statik."""
    try:
        df = fetch_live_symbol_data()
        row = df[df["symbol"] == sym]
        if not row.empty:
            return str(row.iloc[0]["sector"])
    except Exception:
        pass
    return _STATIC_SECTOR.get(sym, "Diğer")

# ══════════════════════════════════════════════════════════════
# FİYAT VERİSİ
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner=False)
def get_stock_data(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    try:
        t  = yf.Ticker(bist_ticker(symbol))
        df = t.history(period=period, interval=interval, auto_adjust=True)
        if df.empty:
            return pd.DataFrame()
        df.index = pd.to_datetime(df.index).tz_localize(None)
        df = df[["Open","High","Low","Close","Volume"]].dropna()
        df.columns = ["open","high","low","close","volume"]
        return df[df["volume"] > 0]
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=300, show_spinner=False)
def get_multi_stock_close(symbols: list, period: str = "1y") -> pd.DataFrame:
    if not symbols:
        return pd.DataFrame()
    tickers = [bist_ticker(s) for s in symbols]
    try:
        raw = yf.download(tickers, period=period, interval="1d",
                          auto_adjust=True, progress=False, threads=True)
        if raw.empty:
            return pd.DataFrame()
        if len(symbols) == 1:
            closes = raw[["Close"]].copy()
            closes.columns = [symbols[0]]
        else:
            if isinstance(raw.columns, pd.MultiIndex):
                closes = raw["Close"].copy()
                closes.columns = [str(c).replace(".IS","") for c in closes.columns]
            else:
                closes = raw[["Close"]].copy()
                closes.columns = [symbols[0]]
        closes.index = pd.to_datetime(closes.index).tz_localize(None)
        return closes.dropna(how="all")
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=60, show_spinner=False)
def get_market_overview() -> dict:
    results = {}
    tmap = {
        "XU100.IS": "BIST 100",
        "USDTRY=X": "USD/TRY",
        "GC=F":     "Altın (USD)",
        "BZ=F":     "Brent (USD)",
        "EURUSD=X": "EUR/USD",
    }
    try:
        raw = yf.download(list(tmap.keys()), period="5d", interval="1d",
                          auto_adjust=True, progress=False)
        if raw.empty:
            return {}
        closes = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
        for sym, label in tmap.items():
            try:
                if sym in closes.columns:
                    p = closes[sym].dropna()
                    if len(p) >= 2:
                        last = float(p.iloc[-1])
                        prev = float(p.iloc[-2])
                        results[label] = {"value": last, "change": (last-prev)/prev*100}
            except Exception:
                pass
    except Exception:
        pass
    return results


@st.cache_data(ttl=120, show_spinner=False)
def get_bist_snapshot(index_group: str = "BIST 30") -> pd.DataFrame:
    symbols = INDEX_GROUPS.get(index_group, BIST30)[:50]
    try:
        tickers_str = " ".join([bist_ticker(s) for s in symbols])
        raw = yf.download(tickers_str, period="5d", interval="1d",
                          auto_adjust=True, progress=False, threads=True)
        if raw.empty:
            return pd.DataFrame()
        closes  = raw["Close"]  if isinstance(raw.columns, pd.MultiIndex) else raw
        volumes = raw["Volume"] if isinstance(raw.columns, pd.MultiIndex) else pd.DataFrame()
        closes.index = pd.to_datetime(closes.index).tz_localize(None)

        records = []
        for sym in symbols:
            yt  = bist_ticker(sym)
            col = yt if yt in closes.columns else sym
            if col not in closes.columns:
                continue
            prices = closes[col].dropna()
            if len(prices) < 2:
                continue
            last = float(prices.iloc[-1])
            prev = float(prices.iloc[-2])
            chg  = (last - prev) / prev * 100
            vol  = (float(volumes[col].dropna().iloc[-1])
                    if (not volumes.empty and col in volumes.columns) else 0)
            records.append({
                "Sembol": sym,
                "İsim":   STOCK_NAMES.get(sym, sym),
                "Fiyat":  round(last, 2),
                "Değ%":   round(chg, 2),
                "Hacim":  int(vol),
            })
        if not records:
            return pd.DataFrame()
        return (pd.DataFrame(records)
                .sort_values("Değ%", ascending=False)
                .reset_index(drop=True))
    except Exception:
        return pd.DataFrame()

# ══════════════════════════════════════════════════════════════
# BISTDataFetcher — isyatirim + yfinance çift kaynak
# ══════════════════════════════════════════════════════════════
class BISTDataFetcher:
    HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122",
           "Accept-Language": "tr-TR,tr;q=0.9"}

    def __init__(self, workers: int = 6, rate_delay: float = 0.08):
        self.w  = workers
        self.rd = rate_delay
        self._s = requests.Session()
        self._s.headers.update(self.HDR)

    @staticmethod
    def _tf(v):
        if v is None:
            return None
        if isinstance(v, (int, float)):
            f = float(v)
            return None if (f != f or abs(f) > 1e14) else f
        s = re.sub(r"[^\d.\-]", "", str(v).strip().replace(",", "."))
        try:
            f = float(s)
            return None if (f != f or abs(f) > 1e14) else f
        except Exception:
            return None

    def _yf1(self, sembol: str) -> dict:
        r: dict = {k: None for k in [
            "fiyat_yf","fk_yf","pd_dd_yf","fd_favok_yf","eps_yf","hbdd_yf",
            "piyasa_degeri_yf","lot_yf","net_kar_yf","onceki_kar_yf",
            "sermaye_yf","halka_aciklik_yf","sirket_adi_yf","net_satis_yf",
            "sektor_yf","aylik_yf","yillik_yf",
        ]}
        try:
            t = yf.Ticker(bist_ticker(sembol))
            # fast_info
            try:
                fi = t.fast_info
                r["fiyat_yf"] = (getattr(fi, "last_price", None)
                                 or getattr(fi, "previous_close", None))
            except Exception:
                pass
            # full info
            try:
                info = t.info or {}
                def g(*ks):
                    for k in ks:
                        v = info.get(k)
                        if v:
                            try:
                                f = float(v)
                                if f == f and 0 < abs(f) < 1e14:
                                    return f
                            except Exception:
                                pass
                    return None

                r["fiyat_yf"]          = r["fiyat_yf"] or g("currentPrice","regularMarketPrice","previousClose")
                r["fk_yf"]             = g("trailingPE","forwardPE")
                r["pd_dd_yf"]          = g("priceToBook")
                r["fd_favok_yf"]       = g("enterpriseToEbitda")
                r["eps_yf"]            = g("trailingEps")
                r["hbdd_yf"]           = g("bookValue")
                r["sirket_adi_yf"]     = info.get("longName") or info.get("shortName")
                r["sektor_yf"]         = info.get("sector")

                mc = g("marketCap")
                if mc:
                    r["piyasa_degeri_yf"] = round(mc / 1e6, 2)
                lot = g("sharesOutstanding")
                if lot:
                    r["lot_yf"] = int(lot)
                ni = g("netIncomeToCommon")
                if ni:
                    r["net_kar_yf"] = round(ni / 1e6, 2)
                bv = g("bookValue")
                sh = g("sharesOutstanding")
                if bv and sh:
                    r["sermaye_yf"] = round((bv * sh) / 1e6, 2)
                fs  = g("floatShares")
                tot = g("sharesOutstanding")
                if fs and tot and tot > 0:
                    r["halka_aciklik_yf"] = round((fs / tot) * 100, 2)
            except Exception:
                pass
            # history
            try:
                hist = t.history(period="14mo", interval="1d", timeout=10)
                if hist is not None and len(hist) >= 5:
                    cl  = hist["Close"].dropna()
                    son = float(cl.iloc[-1])
                    r["fiyat_yf"] = r["fiyat_yf"] or round(son, 2)
                    if len(cl) >= 23:
                        p = float(cl.iloc[-23])
                        if p > 0:
                            r["aylik_yf"] = round(son / p - 1, 6)
                    if len(cl) >= 253:
                        p = float(cl.iloc[-253])
                        if p > 0:
                            r["yillik_yf"] = round(son / p - 1, 6)
            except Exception:
                pass
            # financials
            try:
                fin = t.financials
                if fin is not None and not fin.empty:
                    for nk in ["Net Income", "netIncome"]:
                        if nk in fin.index:
                            vals = fin.loc[nk].dropna().values
                            if len(vals) >= 1 and not r["net_kar_yf"]:
                                r["net_kar_yf"] = round(float(vals[0]) / 1e6, 2)
                            if len(vals) >= 2:
                                r["onceki_kar_yf"] = round(float(vals[1]) / 1e6, 2)
                            break
                    for rk in ["Total Revenue", "Revenue"]:
                        if rk in fin.index:
                            vals = fin.loc[rk].dropna().values
                            if len(vals) >= 1:
                                r["net_satis_yf"] = round(float(vals[0]) / 1e6, 2)
                            break
            except Exception:
                pass
        except Exception:
            pass
        time.sleep(self.rd)
        return r

    def fetch_all(self, semboller: List[str], prog_cb=None) -> pd.DataFrame:
        # Canlı sektör ve isim verisi
        live_df = fetch_live_symbol_data()
        live_map = {}
        if not live_df.empty:
            for _, row in live_df.iterrows():
                live_map[row["symbol"]] = {
                    "name":   row.get("name", ""),
                    "sector": row.get("sector", "Diğer"),
                }

        yc: dict = {}
        done = 0
        with ThreadPoolExecutor(max_workers=self.w) as ex:
            fs = {ex.submit(self._yf1, s): s for s in semboller}
            for fut in as_completed(fs):
                s = fs[fut]
                try:
                    yc[s] = fut.result(timeout=30)
                except Exception:
                    yc[s] = {}
                done += 1
                if prog_cb:
                    prog_cb(done, len(semboller))

        rows = []
        for sem in semboller:
            y    = yc.get(sem, {})
            live = live_map.get(sem, {})

            def ilk(*vs):
                for v in vs:
                    if v is None:
                        continue
                    if isinstance(v, float) and (v != v or abs(v) > 1e13):
                        continue
                    if isinstance(v, str) and v.strip().lower() in ("","nan","none"):
                        continue
                    if isinstance(v, (int, float)) and v == 0:
                        continue
                    return v
                return None

            fiy = self._tf(ilk(y.get("fiyat_yf"))) or 0.0
            lot = self._tf(ilk(y.get("lot_yf"))) or 0.0
            nk  = self._tf(ilk(y.get("net_kar_yf"))) or 0.0
            ep  = self._tf(ilk(y.get("eps_yf"))) or 0.0
            ser = self._tf(ilk(y.get("sermaye_yf"))) or 0.0
            pdm = self._tf(ilk(y.get("piyasa_degeri_yf"))) or 0.0

            if not pdm and fiy > 0 and lot > 0:
                pdm = round(fiy * lot / 1e6, 2)
            if not ep and nk > 0 and lot > 0:
                ep = round(nk * 1e6 / lot, 4)
            if not nk and ep > 0 and lot > 0:
                nk = round(ep * lot / 1e6, 2)

            # Sektör: yfinance > tradingview > statik
            sektor = (ilk(y.get("sektor_yf"))
                      or live.get("sector")
                      or _STATIC_SECTOR.get(sem, "Diğer"))

            # İsim: yfinance > tradingview > statik
            sirket = (ilk(y.get("sirket_adi_yf"))
                      or live.get("name")
                      or STOCK_NAMES.get(sem, sem))

            rows.append({
                "hisse_kodu":    sem,
                "sirket_adi":    str(sirket),
                "sektor":        str(sektor),
                "fiyat":         fiy or None,
                "piyasa_degeri": pdm or None,
                "lot_sayisi":    int(lot) if lot > 0 else None,
                "halka_aciklik": ilk(y.get("halka_aciklik_yf")),
                "sermaye":       ser or None,
                "fk":            ilk(y.get("fk_yf")),
                "fd_favok":      ilk(y.get("fd_favok_yf")),
                "pd_dd":         ilk(y.get("pd_dd_yf")),
                "guncel_net_kar":nk or None,
                "onceki_net_kar":ilk(y.get("onceki_kar_yf")),
                "net_satis":     ilk(y.get("net_satis_yf")),
                "eps":           ep or None,
                "hbdd":          ilk(y.get("hbdd_yf")),
                "aylik_degisim": ilk(y.get("aylik_yf")),
                "yillik_degisim":ilk(y.get("yillik_yf")),
            })

        df = pd.DataFrame(rows)
        num_cols = ["fiyat","piyasa_degeri","lot_sayisi","halka_aciklik","sermaye",
                    "fk","fd_favok","pd_dd","guncel_net_kar","onceki_net_kar",
                    "eps","hbdd","net_satis","aylik_degisim","yillik_degisim"]
        for c in num_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        valid = df[df["fiyat"].notna() & (df["fiyat"] > 0)].copy()
        return valid.sort_values("hisse_kodu").reset_index(drop=True)
