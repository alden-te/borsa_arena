"""
Backtest Motoru
---------------
Strateji sinyallerini tarihsel veri üzerinde simüle eder.
Çıktılar: Toplam getiri, Sharpe, Max Drawdown, Win Rate, Equity Curve.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class BacktestResult:
    equity_curve:     pd.Series
    trades:           pd.DataFrame
    total_return_pct: float
    annual_return_pct:float
    max_drawdown_pct: float
    sharpe_ratio:     float
    win_rate_pct:     float
    total_trades:     int
    winning_trades:   int
    losing_trades:    int
    avg_win_pct:      float
    avg_loss_pct:     float
    profit_factor:    float
    buy_hold_return:  float
    start_date:       str
    end_date:         str

def run_backtest(
    df: pd.DataFrame,
    signal_col: str = "signal",
    initial_capital: float = 100_000,
    commission_pct: float = 0.001,
    stop_loss_pct: Optional[float] = None,
    take_profit_pct: Optional[float] = None,
) -> BacktestResult:
    """
    Sinyal serisine göre backtest çalıştırır.
    
    Args:
        df: OHLCV + signal_col içeren DataFrame
            signal_col: 1 = AL, -1 = SAT, 0 = BEKLE
        initial_capital: Başlangıç sermayesi (TL)
        commission_pct: İşlem komisyonu (her alım/satım için)
        stop_loss_pct: Stop-loss seviyesi (örn: 0.05 = %5)
        take_profit_pct: Take-profit seviyesi (örn: 0.10 = %10)
    
    Returns:
        BacktestResult dataclass
    """
    if df.empty or signal_col not in df.columns:
        return _empty_result()
    
    df = df.copy().dropna(subset=["close", signal_col])
    
    capital      = initial_capital
    position     = 0.0      # Sahip olunan hisse miktarı
    entry_price  = 0.0
    in_position  = False
    
    equity       = []
    trade_log    = []
    
    for i, (idx, row) in enumerate(df.iterrows()):
        price  = row["close"]
        signal = int(row[signal_col])
        
        # ─── Stop Loss / Take Profit ───
        if in_position and entry_price > 0:
            change = (price - entry_price) / entry_price
            if stop_loss_pct and change <= -stop_loss_pct:
                # Stop-loss tetiklendi
                proceeds = position * price * (1 - commission_pct)
                pnl_pct  = (price - entry_price) / entry_price * 100
                trade_log.append({
                    "exit_date": idx, "entry_price": entry_price,
                    "exit_price": price, "pnl_pct": pnl_pct, "exit_reason": "SL",
                })
                capital    += proceeds
                position    = 0.0
                in_position = False
                signal      = 0
            elif take_profit_pct and change >= take_profit_pct:
                # Take-profit tetiklendi
                proceeds = position * price * (1 - commission_pct)
                pnl_pct  = (price - entry_price) / entry_price * 100
                trade_log.append({
                    "exit_date": idx, "entry_price": entry_price,
                    "exit_price": price, "pnl_pct": pnl_pct, "exit_reason": "TP",
                })
                capital    += proceeds
                position    = 0.0
                in_position = False
                signal      = 0
        
        # ─── Alım ───
        if signal == 1 and not in_position and capital > 0:
            cost    = capital * (1 - commission_pct)
            position     = cost / price
            entry_price  = price
            capital      = 0.0
            in_position  = True
        
        # ─── Satım ───
        elif signal == -1 and in_position:
            proceeds = position * price * (1 - commission_pct)
            pnl_pct  = (price - entry_price) / entry_price * 100
            trade_log.append({
                "exit_date": idx, "entry_price": entry_price,
                "exit_price": price, "pnl_pct": pnl_pct, "exit_reason": "Signal",
            })
            capital     = proceeds
            position    = 0.0
            in_position = False
        
        # ─── Anlık Portföy Değeri ───
        portfolio_value = capital + (position * price if in_position else 0)
        equity.append({"date": idx, "value": portfolio_value})
    
    # ─── Açık Pozisyonu Kapat ───
    if in_position and len(df) > 0:
        last_price = float(df["close"].iloc[-1])
        proceeds   = position * last_price * (1 - commission_pct)
        pnl_pct    = (last_price - entry_price) / entry_price * 100
        trade_log.append({
            "exit_date": df.index[-1], "entry_price": entry_price,
            "exit_price": last_price, "pnl_pct": pnl_pct, "exit_reason": "End",
        })
        capital = proceeds
        equity[-1]["value"] = capital
    
    # ─── Sonuç Hesapla ───
    equity_df = pd.DataFrame(equity).set_index("date")["value"]
    trades_df = pd.DataFrame(trade_log) if trade_log else pd.DataFrame(
        columns=["exit_date","entry_price","exit_price","pnl_pct","exit_reason"]
    )
    
    # Metrikler
    total_return = (equity_df.iloc[-1] / initial_capital - 1) * 100 if len(equity_df) > 0 else 0
    
    # Yıllık Getiri (CAGR)
    try:
        n_days = (df.index[-1] - df.index[0]).days if len(df) > 1 else 252
    except (AttributeError, TypeError):
        n_days = len(df)  # Datetime index yoksa bar sayısını kullan
    n_years  = max(n_days / 252, 1/252)
    annual   = ((1 + total_return/100) ** (1/n_years) - 1) * 100
    
    # Max Drawdown
    rolling_max = equity_df.cummax()
    drawdown    = (equity_df - rolling_max) / rolling_max * 100
    max_dd      = float(drawdown.min())
    
    # Sharpe Ratio
    returns = equity_df.pct_change().dropna()
    sharpe  = 0.0
    if len(returns) > 1 and returns.std() > 0:
        sharpe = float(returns.mean() / returns.std() * np.sqrt(252))
    
    # Trade İstatistikleri
    if not trades_df.empty and "pnl_pct" in trades_df.columns:
        wins   = trades_df[trades_df["pnl_pct"] > 0]
        losses = trades_df[trades_df["pnl_pct"] <= 0]
        win_rate   = len(wins) / len(trades_df) * 100
        avg_win    = float(wins["pnl_pct"].mean())  if len(wins) > 0  else 0
        avg_loss   = float(losses["pnl_pct"].mean()) if len(losses) > 0 else 0
        gross_win  = wins["pnl_pct"].sum()   if len(wins) > 0  else 0
        gross_loss = abs(losses["pnl_pct"].sum()) if len(losses) > 0 else 1
        profit_f   = gross_win / gross_loss if gross_loss > 0 else 0
    else:
        win_rate = avg_win = avg_loss = profit_f = 0
    
    # Buy & Hold karşılaştırma
    bh = (float(df["close"].iloc[-1]) / float(df["close"].iloc[0]) - 1) * 100
    
    return BacktestResult(
        equity_curve      = equity_df,
        trades            = trades_df,
        total_return_pct  = round(total_return, 2),
        annual_return_pct = round(annual, 2),
        max_drawdown_pct  = round(max_dd, 2),
        sharpe_ratio      = round(sharpe, 2),
        win_rate_pct      = round(win_rate, 2),
        total_trades      = len(trades_df),
        winning_trades    = len(trades_df[trades_df["pnl_pct"] > 0]) if not trades_df.empty else 0,
        losing_trades     = len(trades_df[trades_df["pnl_pct"] <= 0]) if not trades_df.empty else 0,
        avg_win_pct       = round(avg_win, 2),
        avg_loss_pct      = round(avg_loss, 2),
        profit_factor     = round(profit_f, 2),
        buy_hold_return   = round(bh, 2),
        start_date        = str(df.index[0].date()) if len(df) > 0 and hasattr(df.index[0], 'date') else str(df.index[0]) if len(df) > 0 else "",
        end_date          = str(df.index[-1].date()) if len(df) > 0 and hasattr(df.index[-1], 'date') else str(df.index[-1]) if len(df) > 0 else "",
    )

def signal_from_crossover(df: pd.DataFrame, fast_col: str, slow_col: str) -> pd.Series:
    """
    İki çizginin kesişiminden AL/SAT sinyali üretir.
    Fast > Slow → 1 (AL), Fast < Slow → -1 (SAT)
    """
    if fast_col not in df.columns or slow_col not in df.columns:
        return pd.Series(0, index=df.index)
    
    fast = df[fast_col]
    slow = df[slow_col]
    
    signal = pd.Series(0, index=df.index)
    signal[fast > slow] = 1
    signal[fast < slow] = -1
    return signal

def signal_from_threshold(df: pd.DataFrame, col: str,
                           buy_below: float = None, sell_above: float = None,
                           buy_above: float = None, sell_below: float = None) -> pd.Series:
    """
    Tek indikatör eşik değerlerine göre sinyal üretir.
    Örnek: RSI < 30 → AL, RSI > 70 → SAT
    """
    if col not in df.columns:
        return pd.Series(0, index=df.index)
    
    series = df[col]
    signal = pd.Series(0, index=df.index)
    
    in_trade = False
    for i in range(len(signal)):
        val = series.iloc[i]
        if pd.isna(val):
            continue
        
        if not in_trade:
            if   buy_below is not None and val < buy_below:
                signal.iloc[i] = 1; in_trade = True
            elif buy_above is not None and val > buy_above:
                signal.iloc[i] = 1; in_trade = True
        else:
            if   sell_above is not None and val > sell_above:
                signal.iloc[i] = -1; in_trade = False
            elif sell_below is not None and val < sell_below:
                signal.iloc[i] = -1; in_trade = False
    
    return signal

def _empty_result() -> BacktestResult:
    return BacktestResult(
        equity_curve=pd.Series(dtype=float), trades=pd.DataFrame(),
        total_return_pct=0, annual_return_pct=0, max_drawdown_pct=0,
        sharpe_ratio=0, win_rate_pct=0, total_trades=0,
        winning_trades=0, losing_trades=0, avg_win_pct=0, avg_loss_pct=0,
        profit_factor=0, buy_hold_return=0, start_date="", end_date="",
    )
