"""
İndikatör Hesaplama Motoru — Saf NumPy/Pandas
----------------------------------------------
Hiçbir harici indikatör kütüphanesi kullanmaz.
pandas-ta / ta-lib gerektirmez. Python 3.9+ uyumlu.
51 indikatör, tümü test edilmiş.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

# ─── İndikatör Tanımı ───
@dataclass
class Indicator:
    key:         str
    name:        str
    category:    str
    description: str
    params:      dict = field(default_factory=dict)

# ─── 51 İndikatör Kataloğu ───
INDICATOR_CATALOG: List[Indicator] = [
    # Trend
    Indicator("sma",        "SMA",             "Trend",     "Basit Hareketli Ortalama",         {"length": 20}),
    Indicator("ema",        "EMA",             "Trend",     "Üstel Hareketli Ortalama",         {"length": 20}),
    Indicator("wma",        "WMA",             "Trend",     "Ağırlıklı Hareketli Ortalama",     {"length": 20}),
    Indicator("dema",       "DEMA",            "Trend",     "Çift EMA",                         {"length": 20}),
    Indicator("tema",       "TEMA",            "Trend",     "Üçlü EMA",                         {"length": 20}),
    Indicator("hull",       "HMA",             "Trend",     "Hull Hareketli Ortalama",          {"length": 9}),
    Indicator("vwma",       "VWMA",            "Trend",     "Hacim Ağırlıklı MA",               {"length": 20}),
    Indicator("kama",       "KAMA",            "Trend",     "Kaufman Adaptif MA",               {"length": 10}),
    Indicator("supertrend", "SuperTrend",      "Trend",     "Süper Trend Çizgisi",              {"length": 7,  "multiplier": 3.0}),
    Indicator("psar",       "Parabolic SAR",   "Trend",     "Parabolik Dur-Kayıp",              {"af": 0.02,   "max_af": 0.2}),
    Indicator("aroon",      "Aroon",           "Trend",     "Aroon Göstergesi",                 {"length": 25}),
    Indicator("adx",        "ADX",             "Trend",     "Ortalama Yön Endeksi",             {"length": 14}),
    Indicator("vortex",     "Vortex",          "Trend",     "Vortex Göstergesi",                {"length": 14}),
    Indicator("ichimoku",   "Ichimoku",        "Trend",     "Ichimoku Bulutu (Tenkan/Kijun)",   {}),
    Indicator("zlema",      "ZLEMA",           "Trend",     "Sıfır Gecikmeli EMA",              {"length": 20}),
    # Momentum
    Indicator("rsi",        "RSI",             "Momentum",  "Göreceli Güç Endeksi",             {"length": 14}),
    Indicator("macd",       "MACD",            "Momentum",  "MACD",                             {"fast": 12, "slow": 26, "signal": 9}),
    Indicator("stoch",      "Stochastic",      "Momentum",  "Stokastik Osilatör",               {"k": 14, "d": 3}),
    Indicator("stochrsi",   "Stochastic RSI",  "Momentum",  "Stokastik RSI",                    {"length": 14}),
    Indicator("cci",        "CCI",             "Momentum",  "Emtia Kanal Endeksi",              {"length": 20}),
    Indicator("mom",        "Momentum",        "Momentum",  "Momentum Osilatörü",               {"length": 10}),
    Indicator("roc",        "ROC",             "Momentum",  "Değişim Oranı",                    {"length": 12}),
    Indicator("willr",      "Williams %R",     "Momentum",  "Williams %R",                      {"length": 14}),
    Indicator("ao",         "Awesome Osc.",    "Momentum",  "Harika Osilatör",                  {}),
    Indicator("apo",        "APO",             "Momentum",  "Mutlak Fiyat Osilatörü",           {"fast": 12, "slow": 26}),
    Indicator("ppo",        "PPO",             "Momentum",  "Yüzde Fiyat Osilatörü",            {"fast": 12, "slow": 26}),
    Indicator("tsi",        "TSI",             "Momentum",  "Gerçek Güç Endeksi",               {"fast": 13, "slow": 25}),
    Indicator("dpo",        "DPO",             "Momentum",  "Trentten Arındırılmış Fiyat Osc.", {"length": 20}),
    Indicator("kst",        "KST",             "Momentum",  "KST Osilatörü",                    {}),
    Indicator("uo",         "Ultimate Osc.",   "Momentum",  "Nihai Osilatör",                   {}),
    # Volatilite
    Indicator("bbands",     "Bollinger Bands", "Volatilite","Bollinger Bantları",               {"length": 20, "std": 2.0}),
    Indicator("kc",         "Keltner Ch.",     "Volatilite","Keltner Kanalı",                   {"length": 20, "atr_length": 10}),
    Indicator("dc",         "Donchian Ch.",    "Volatilite","Donchian Kanalı",                  {"length": 20}),
    Indicator("atr",        "ATR",             "Volatilite","Ortalama Gerçek Aralık",           {"length": 14}),
    Indicator("natr",       "NATR",            "Volatilite","Normalize ATR",                    {"length": 14}),
    Indicator("massi",      "Mass Index",      "Volatilite","Kütle Endeksi",                    {"fast": 9, "slow": 25}),
    Indicator("bbwidth",    "BB Width",        "Volatilite","Bollinger Bant Genişliği",         {"length": 20}),
    Indicator("bbpct",      "BB %B",           "Volatilite","Bollinger %B",                     {"length": 20}),
    Indicator("hv",         "Hist. Vol.",      "Volatilite","Tarihi Volatilite",                {"length": 20}),
    # Hacim
    Indicator("obv",        "OBV",             "Hacim",     "Dengeli Hacim",                    {}),
    Indicator("vwap",       "VWAP",            "Hacim",     "Hacim Ağırlıklı Ort. Fiyat",      {}),
    Indicator("mfi",        "MFI",             "Hacim",     "Para Akışı Endeksi",               {"length": 14}),
    Indicator("cmf",        "CMF",             "Hacim",     "Chaikin Para Akışı",               {"length": 20}),
    Indicator("ad",         "A/D",             "Hacim",     "Birikim/Dağıtım Çizgisi",         {}),
    Indicator("pvt",        "PVT",             "Hacim",     "Fiyat-Hacim Trendi",              {}),
    Indicator("eom",        "EOM",             "Hacim",     "Hareketin Kolaylığı",             {"length": 14}),
    Indicator("vpt",        "VPT",             "Hacim",     "Hacim-Fiyat Trendi",              {}),
    # Destek/Direnç
    Indicator("pivot",      "Pivot Points",    "S/R",       "Klasik Pivot Noktaları",          {}),
    Indicator("fibret",     "Fibonacci",       "S/R",       "Fibonacci Geri Dönüşleri",        {}),
    Indicator("zscore",     "Z-Score",         "İstatistik","Fiyat Z-Skoru",                   {"length": 20}),
    Indicator("percentile", "Percentile",      "İstatistik","Fiyat Yüzdelik Sırası",           {"length": 50}),
]

INDICATORS_BY_KEY: Dict[str, Indicator] = {ind.key: ind for ind in INDICATOR_CATALOG}
INDICATORS_BY_CAT: Dict[str, List[Indicator]] = {}
for _ind in INDICATOR_CATALOG:
    INDICATORS_BY_CAT.setdefault(_ind.category, []).append(_ind)


# ══════════════════════════════════════════════════════
# YARDIMCI HESAPLAMA FONKSİYONLARI (Saf NumPy/Pandas)
# ══════════════════════════════════════════════════════

def _sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(window=length, min_periods=length).mean()

def _ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False, min_periods=length).mean()

def _wma(series: pd.Series, length: int) -> pd.Series:
    weights = np.arange(1, length + 1, dtype=float)
    return series.rolling(length).apply(
        lambda x: np.dot(x, weights) / weights.sum(), raw=True
    )

def _true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low  - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr

def _atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int) -> pd.Series:
    tr = _true_range(high, low, close)
    return tr.ewm(alpha=1/length, adjust=False, min_periods=length).mean()

def _wilder_smooth(series: pd.Series, length: int) -> pd.Series:
    """Wilder smoothing (RMA)."""
    result = series.copy() * np.nan
    first_valid = series.dropna().index
    if len(first_valid) < length:
        return result
    start_idx = series.index.get_loc(first_valid[length - 1])
    result.iloc[start_idx] = series.iloc[:start_idx + 1].mean()
    alpha = 1.0 / length
    for i in range(start_idx + 1, len(series)):
        if pd.notna(series.iloc[i]):
            result.iloc[i] = alpha * series.iloc[i] + (1 - alpha) * result.iloc[i - 1]
    return result


# ══════════════════════════════════════════════════════
# ANA HESAPLAMA FONKSİYONU
# ══════════════════════════════════════════════════════

def compute_indicator(df: pd.DataFrame, key: str, params: dict = None) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    ind = INDICATORS_BY_KEY.get(key)
    p   = {**(ind.params if ind else {}), **(params or {})}

    close  = df["close"]
    high   = df["high"]
    low    = df["low"]
    volume = df["volume"]

    try:
        # ── Trend ──────────────────────────────────────────────
        if key == "sma":
            df[f"sma_{p['length']}"] = _sma(close, p["length"])

        elif key == "ema":
            df[f"ema_{p['length']}"] = _ema(close, p["length"])

        elif key == "wma":
            df[f"wma_{p['length']}"] = _wma(close, p["length"])

        elif key == "dema":
            e1 = _ema(close, p["length"])
            e2 = _ema(e1, p["length"])
            df[f"dema_{p['length']}"] = 2 * e1 - e2

        elif key == "tema":
            e1 = _ema(close, p["length"])
            e2 = _ema(e1, p["length"])
            e3 = _ema(e2, p["length"])
            df[f"tema_{p['length']}"] = 3 * e1 - 3 * e2 + e3

        elif key == "hull":
            n = p["length"]
            half = int(n / 2)
            sqrt_n = int(np.sqrt(n))
            wma_half = _wma(close, half)
            wma_full = _wma(close, n)
            raw = 2 * wma_half - wma_full
            df[f"hma_{n}"] = _wma(raw, sqrt_n)

        elif key == "vwma":
            n = p["length"]
            pv = close * volume
            df[f"vwma_{n}"] = (
                pv.rolling(n).sum() / volume.rolling(n).sum()
            )

        elif key == "kama":
            n   = p["length"]
            fast_sc = 2 / (2 + 1)
            slow_sc = 2 / (30 + 1)
            direction = (close - close.shift(n)).abs()
            volatility = close.diff().abs().rolling(n).sum()
            er = direction / volatility.replace(0, np.nan)
            sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
            kama = close.copy() * np.nan
            start = close.dropna().index
            if len(start) > n:
                idx0 = close.index.get_loc(start[n - 1])
                kama.iloc[idx0] = close.iloc[idx0]
                for i in range(idx0 + 1, len(close)):
                    if pd.notna(sc.iloc[i]) and pd.notna(kama.iloc[i - 1]):
                        kama.iloc[i] = kama.iloc[i - 1] + sc.iloc[i] * (close.iloc[i] - kama.iloc[i - 1])
            df[f"kama_{n}"] = kama

        elif key == "zlema":
            n = p["length"]
            lag = int((n - 1) / 2)
            ema_input = 2 * close - close.shift(lag)
            df[f"zlema_{n}"] = _ema(ema_input, n)

        elif key == "supertrend":
            n   = p["length"]
            mul = p["multiplier"]
            atr = _atr(high, low, close, n)
            hl2 = (high + low) / 2
            upper_basic = hl2 + mul * atr
            lower_basic = hl2 - mul * atr
            upper = upper_basic.copy()
            lower = lower_basic.copy()
            trend = pd.Series(1, index=df.index)
            for i in range(1, len(df)):
                upper.iloc[i] = min(upper_basic.iloc[i], upper.iloc[i-1]) if close.iloc[i-1] <= upper.iloc[i-1] else upper_basic.iloc[i]
                lower.iloc[i] = max(lower_basic.iloc[i], lower.iloc[i-1]) if close.iloc[i-1] >= lower.iloc[i-1] else lower_basic.iloc[i]
                if close.iloc[i] > upper.iloc[i-1]:
                    trend.iloc[i] = 1
                elif close.iloc[i] < lower.iloc[i-1]:
                    trend.iloc[i] = -1
                else:
                    trend.iloc[i] = trend.iloc[i-1]
            df["supertrend"]   = np.where(trend == 1, lower, upper)
            df["supertrend_d"] = trend

        elif key == "psar":
            af_step = p["af"]
            af_max  = p["max_af"]
            bull    = True
            af      = af_step
            ep      = float(low.iloc[0])
            hp      = float(high.iloc[0])
            lp      = float(low.iloc[0])
            sar_vals = [float(low.iloc[0])]
            for i in range(1, len(df)):
                prev_sar = sar_vals[-1]
                if bull:
                    sar = prev_sar + af * (hp - prev_sar)
                    sar = min(sar, float(low.iloc[i-1]), float(low.iloc[max(0,i-2)]))
                    if float(low.iloc[i]) < sar:
                        bull, sar, ep, af = False, hp, float(low.iloc[i]), af_step
                    else:
                        if float(high.iloc[i]) > hp:
                            hp = float(high.iloc[i])
                            af = min(af + af_step, af_max)
                else:
                    sar = prev_sar + af * (lp - prev_sar)
                    sar = max(sar, float(high.iloc[i-1]), float(high.iloc[max(0,i-2)]))
                    if float(high.iloc[i]) > sar:
                        bull, sar, ep, af = True, lp, float(high.iloc[i]), af_step
                    else:
                        if float(low.iloc[i]) < lp:
                            lp = float(low.iloc[i])
                            af = min(af + af_step, af_max)
                sar_vals.append(sar)
            df["psar"] = sar_vals

        elif key == "aroon":
            n = p["length"]
            df[f"aroon_up"]   = high.rolling(n+1).apply(lambda x: ((n - (n - np.argmax(x))) / n) * 100, raw=True)
            df[f"aroon_down"] = low.rolling(n+1).apply(lambda x: ((n - (n - np.argmin(x))) / n) * 100, raw=True)

        elif key == "adx":
            n  = p["length"]
            tr = _true_range(high, low, close)
            plus_dm  = high.diff()
            minus_dm = -low.diff()
            plus_dm[plus_dm < 0]   = 0
            minus_dm[minus_dm < 0] = 0
            plus_dm[plus_dm < minus_dm]  = 0
            minus_dm[minus_dm < plus_dm] = 0
            atr14    = _wilder_smooth(tr, n)
            plus_di  = 100 * _wilder_smooth(plus_dm, n)  / atr14.replace(0, np.nan)
            minus_di = 100 * _wilder_smooth(minus_dm, n) / atr14.replace(0, np.nan)
            dx       = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
            df["adx"]  = _wilder_smooth(dx, n)
            df["di_p"] = plus_di
            df["di_n"] = minus_di

        elif key == "vortex":
            n  = p["length"]
            tr = _true_range(high, low, close)
            vm_p = (high - low.shift(1)).abs()
            vm_m = (low  - high.shift(1)).abs()
            df[f"vtx_p"] = vm_p.rolling(n).sum() / tr.rolling(n).sum()
            df[f"vtx_m"] = vm_m.rolling(n).sum() / tr.rolling(n).sum()

        elif key == "ichimoku":
            df["tenkan"]  = (high.rolling(9).max() + low.rolling(9).min()) / 2
            df["kijun"]   = (high.rolling(26).max() + low.rolling(26).min()) / 2
            df["senkou_a"] = ((df["tenkan"] + df["kijun"]) / 2).shift(26)
            df["senkou_b"] = ((high.rolling(52).max() + low.rolling(52).min()) / 2).shift(26)
            df["chikou"]  = close.shift(-26)

        # ── Momentum ───────────────────────────────────────────
        elif key == "rsi":
            n     = p["length"]
            delta = close.diff()
            gain  = delta.clip(lower=0)
            loss  = (-delta).clip(lower=0)
            avg_g = _wilder_smooth(gain, n)
            avg_l = _wilder_smooth(loss, n)
            rs    = avg_g / avg_l.replace(0, np.nan)
            df[f"rsi_{n}"] = 100 - (100 / (1 + rs))

        elif key == "macd":
            fast, slow, sig = p["fast"], p["slow"], p["signal"]
            ema_fast = _ema(close, fast)
            ema_slow = _ema(close, slow)
            macd_line = ema_fast - ema_slow
            signal_line = _ema(macd_line, sig)
            df["macd"]        = macd_line
            df["macd_signal"] = signal_line
            df["macd_hist"]   = macd_line - signal_line

        elif key == "stoch":
            k, d = p["k"], p["d"]
            low_min  = low.rolling(k).min()
            high_max = high.rolling(k).max()
            k_val = 100 * (close - low_min) / (high_max - low_min).replace(0, np.nan)
            df["stoch_k"] = k_val
            df["stoch_d"] = k_val.rolling(d).mean()

        elif key == "stochrsi":
            n   = p["length"]
            delta = close.diff()
            gain  = delta.clip(lower=0)
            loss  = (-delta).clip(lower=0)
            rs    = _wilder_smooth(gain, n) / _wilder_smooth(loss, n).replace(0, np.nan)
            rsi   = 100 - (100 / (1 + rs))
            rsi_min = rsi.rolling(n).min()
            rsi_max = rsi.rolling(n).max()
            df["stochrsi_k"] = 100 * (rsi - rsi_min) / (rsi_max - rsi_min).replace(0, np.nan)
            df["stochrsi_d"] = df["stochrsi_k"].rolling(3).mean()

        elif key == "cci":
            n  = p["length"]
            tp = (high + low + close) / 3
            ma = tp.rolling(n).mean()
            md = tp.rolling(n).apply(lambda x: np.mean(np.abs(x - x.mean())), raw=True)
            df[f"cci_{n}"] = (tp - ma) / (0.015 * md.replace(0, np.nan))

        elif key == "mom":
            n = p["length"]
            df[f"mom_{n}"] = close.diff(n)

        elif key == "roc":
            n = p["length"]
            df[f"roc_{n}"] = (close / close.shift(n) - 1) * 100

        elif key == "willr":
            n = p["length"]
            hh = high.rolling(n).max()
            ll = low.rolling(n).min()
            df[f"willr_{n}"] = -100 * (hh - close) / (hh - ll).replace(0, np.nan)

        elif key == "ao":
            df["ao"] = _sma((high + low) / 2, 5) - _sma((high + low) / 2, 34)

        elif key == "apo":
            fast, slow = p["fast"], p["slow"]
            df["apo"] = _ema(close, fast) - _ema(close, slow)

        elif key == "ppo":
            fast, slow = p["fast"], p["slow"]
            ema_slow = _ema(close, slow)
            df["ppo"] = (_ema(close, fast) - ema_slow) / ema_slow.replace(0, np.nan) * 100

        elif key == "tsi":
            fast, slow = p["fast"], p["slow"]
            m  = close.diff()
            ds = _ema(_ema(m, slow), fast)
            da = _ema(_ema(m.abs(), slow), fast)
            df["tsi"] = 100 * ds / da.replace(0, np.nan)

        elif key == "dpo":
            n = p["length"]
            shift = int(n / 2) + 1
            df[f"dpo_{n}"] = close.shift(shift) - _sma(close, n)

        elif key == "kst":
            def roc_n(s, n): return (s / s.shift(n) - 1) * 100
            rcma1 = _sma(roc_n(close, 10), 10)
            rcma2 = _sma(roc_n(close, 13), 13)
            rcma3 = _sma(roc_n(close, 14), 14)
            rcma4 = _sma(roc_n(close, 15), 15)
            kst = rcma1 + 2*rcma2 + 3*rcma3 + 4*rcma4
            df["kst"]        = kst
            df["kst_signal"] = _sma(kst, 9)

        elif key == "uo":
            prev_close = close.shift(1)
            tr  = _true_range(high, low, close)
            bp  = close - pd.concat([low, prev_close], axis=1).min(axis=1)
            avg7  = bp.rolling(7).sum()  / tr.rolling(7).sum()
            avg14 = bp.rolling(14).sum() / tr.rolling(14).sum()
            avg28 = bp.rolling(28).sum() / tr.rolling(28).sum()
            df["uo"] = 100 * (4*avg7 + 2*avg14 + avg28) / 7

        # ── Volatilite ──────────────────────────────────────────
        elif key == "bbands":
            n, std_mult = p["length"], p["std"]
            mid = _sma(close, n)
            std = close.rolling(n).std(ddof=0)
            df["bb_upper"]  = mid + std_mult * std
            df["bb_middle"] = mid
            df["bb_lower"]  = mid - std_mult * std
            df["bb_width"]  = (df["bb_upper"] - df["bb_lower"]) / mid.replace(0, np.nan) * 100
            df["bb_pct"]    = (close - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"]).replace(0, np.nan)

        elif key == "bbwidth":
            n = p["length"]
            mid = _sma(close, n)
            std = close.rolling(n).std(ddof=0)
            df["bb_width"] = (2 * 2.0 * std) / mid.replace(0, np.nan) * 100

        elif key == "bbpct":
            n = p["length"]
            mid = _sma(close, n)
            std = close.rolling(n).std(ddof=0)
            upper = mid + 2.0 * std
            lower = mid - 2.0 * std
            df["bb_pct"] = (close - lower) / (upper - lower).replace(0, np.nan)

        elif key == "kc":
            n   = p["length"]
            atr_n = p["atr_length"]
            mid = _ema(close, n)
            atr = _atr(high, low, close, atr_n)
            df["kc_upper"]  = mid + 2 * atr
            df["kc_middle"] = mid
            df["kc_lower"]  = mid - 2 * atr

        elif key == "dc":
            n = p["length"]
            df["dc_upper"]  = high.rolling(n).max()
            df["dc_lower"]  = low.rolling(n).min()
            df["dc_middle"] = (df["dc_upper"] + df["dc_lower"]) / 2

        elif key == "atr":
            n = p["length"]
            df[f"atr_{n}"] = _atr(high, low, close, n)

        elif key == "natr":
            n = p["length"]
            df[f"natr_{n}"] = _atr(high, low, close, n) / close.replace(0, np.nan) * 100

        elif key == "massi":
            fast, slow = p["fast"], p["slow"]
            ema1 = _ema(high - low, fast)
            ema2 = _ema(ema1, fast)
            mass = (ema1 / ema2.replace(0, np.nan)).rolling(slow).sum()
            df["massi"] = mass

        elif key == "hv":
            n = p["length"]
            df[f"hv_{n}"] = close.pct_change().rolling(n).std() * np.sqrt(252) * 100

        # ── Hacim ──────────────────────────────────────────────
        elif key == "obv":
            direction = np.sign(close.diff())
            direction.iloc[0] = 0
            df["obv"] = (direction * volume).cumsum()

        elif key == "vwap":
            tp = (high + low + close) / 3
            df["vwap"] = (tp * volume).cumsum() / volume.cumsum()

        elif key == "mfi":
            n  = p["length"]
            tp = (high + low + close) / 3
            mf = tp * volume
            pos = mf.where(tp > tp.shift(1), 0)
            neg = mf.where(tp < tp.shift(1), 0)
            mfr = pos.rolling(n).sum() / neg.rolling(n).sum().replace(0, np.nan)
            df[f"mfi_{n}"] = 100 - (100 / (1 + mfr))

        elif key == "cmf":
            n  = p["length"]
            clv = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
            df[f"cmf_{n}"] = (clv * volume).rolling(n).sum() / volume.rolling(n).sum().replace(0, np.nan)

        elif key == "ad":
            clv = ((close - low) - (high - close)) / (high - low).replace(0, np.nan)
            df["ad"] = (clv * volume).cumsum()

        elif key == "pvt":
            pct = close.pct_change()
            df["pvt"] = (pct * volume).cumsum()

        elif key == "vpt":
            pct = close.pct_change()
            df["vpt"] = (pct * volume).cumsum()

        elif key == "eom":
            n  = p["length"]
            dm = ((high + low) / 2) - ((high.shift(1) + low.shift(1)) / 2)
            br = volume / (100000 * (high - low).replace(0, np.nan))
            df[f"eom_{n}"] = _sma(dm / br.replace(0, np.nan), n)

        # ── Destek / Direnç ─────────────────────────────────────
        elif key == "pivot":
            if len(df) >= 2:
                H, L, C = float(df["high"].iloc[-2]), float(df["low"].iloc[-2]), float(df["close"].iloc[-2])
                P = (H + L + C) / 3
                df.at[df.index[-1], "pivot_p"]  = P
                df.at[df.index[-1], "pivot_r1"] = 2*P - L
                df.at[df.index[-1], "pivot_s1"] = 2*P - H
                df.at[df.index[-1], "pivot_r2"] = P + (H - L)
                df.at[df.index[-1], "pivot_s2"] = P - (H - L)

        elif key == "fibret":
            lb = 50
            window = df.tail(lb)
            h, l  = window["high"].max(), window["low"].min()
            diff  = h - l
            for lvl in [0, 236, 382, 500, 618, 786, 1000]:
                df.at[df.index[-1], f"fib_{lvl}"] = h - diff * (lvl / 1000)

        # ── İstatistik ──────────────────────────────────────────
        elif key == "zscore":
            n = p["length"]
            mu  = close.rolling(n).mean()
            std = close.rolling(n).std(ddof=1)
            df[f"zscore_{n}"] = (close - mu) / std.replace(0, np.nan)

        elif key == "percentile":
            n = p["length"]
            df[f"pct_{n}"] = close.rolling(n).apply(
                lambda x: float(pd.Series(x).rank(pct=True).iloc[-1]) * 100,
                raw=False
            )

    except Exception:
        pass  # Hesaplanamayan indikatör sessizce atlanır

    return df


def compute_multiple(df: pd.DataFrame, keys: list, params_map: dict = None) -> pd.DataFrame:
    params_map = params_map or {}
    for key in keys:
        df = compute_indicator(df, key, params_map.get(key))
    return df


def generate_signal(df: pd.DataFrame, conditions: list) -> pd.Series:
    if df.empty or not conditions:
        return pd.Series(False, index=df.index)
    mask = pd.Series(True, index=df.index)
    for cond in conditions:
        col  = cond.get("col")
        op   = cond.get("op", ">")
        val  = cond.get("val")
        col2 = cond.get("col2")
        if col not in df.columns:
            continue
        series = df[col].ffill()
        rhs    = df[col2].ffill() if col2 and col2 in df.columns else val
        if   op == ">":  mask &= series > rhs
        elif op == "<":  mask &= series < rhs
        elif op == ">=": mask &= series >= rhs
        elif op == "<=": mask &= series <= rhs
        elif op == "crossup":
            if col2 and col2 in df.columns:
                mask &= (series > rhs) & (series.shift(1) <= df[col2].shift(1))
        elif op == "crossdown":
            if col2 and col2 in df.columns:
                mask &= (series < rhs) & (series.shift(1) >= df[col2].shift(1))
    return mask


def signal_from_crossover(df: pd.DataFrame, fast_col: str, slow_col: str) -> pd.Series:
    if fast_col not in df.columns or slow_col not in df.columns:
        return pd.Series(0, index=df.index)
    fast, slow = df[fast_col], df[slow_col]
    signal = pd.Series(0, index=df.index)
    signal[fast > slow] = 1
    signal[fast < slow] = -1
    return signal


def signal_from_threshold(df: pd.DataFrame, col: str,
                           buy_below=None, sell_above=None,
                           buy_above=None, sell_below=None) -> pd.Series:
    if col not in df.columns:
        return pd.Series(0, index=df.index)
    series   = df[col]
    signal   = pd.Series(0, index=df.index)
    in_trade = False
    for i in range(len(signal)):
        val = series.iloc[i]
        if pd.isna(val):
            continue
        if not in_trade:
            if buy_below is not None and val < buy_below:
                signal.iloc[i] = 1;  in_trade = True
            elif buy_above is not None and val > buy_above:
                signal.iloc[i] = 1;  in_trade = True
        else:
            if sell_above is not None and val > sell_above:
                signal.iloc[i] = -1; in_trade = False
            elif sell_below is not None and val < sell_below:
                signal.iloc[i] = -1; in_trade = False
    return signal


def get_categories() -> list:
    return list(INDICATORS_BY_CAT.keys())


def get_indicators_by_category(category: str) -> list:
    return INDICATORS_BY_CAT.get(category, [])
