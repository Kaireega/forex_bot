import pandas as pd
import numpy as np

def BollingerBands(df: pd.DataFrame, n=20, s=2):
    typical_p = ( df.mid_c + df.mid_h + df.mid_l ) / 3
    stddev = typical_p.rolling(window=n).std()
    df['BB_MA'] = typical_p.rolling(window=n).mean()
    df['BB_UP'] = df['BB_MA'] + stddev * s
    df['BB_LW'] = df['BB_MA'] - stddev * s
    df['BB_Signal'] = np.where(typical_p > df['Upper_Band'], 'Sell',
                               np.where(df.mid_c < df['Lower_Band'], 'Buy', None))
    return df


def ATR(df: pd.DataFrame, n=14):
    prev_c = df.mid_c.shift(1)
    tr1 = df.mid_h - df.mid_l
    tr2 = abs(df.mid_h - prev_c)
    tr3 = abs(prev_c - df.mid_l)
    tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
    df[f"ATR_{n}"] = tr.rolling(window=n).mean()
    return df

def KeltnerChannels(df: pd.DataFrame, n_ema=20, n_atr=10):
    df['EMA'] = df.mid_c.ewm(span=n_ema, min_periods=n_ema).mean()
    df = ATR(df, n=n_atr)
    c_atr = f"ATR_{n_atr}"
    df['KeUp'] = df[c_atr] * 2 + df.EMA
    df['KeLo'] = df.EMA - df[c_atr] * 2
    df.drop(c_atr, axis=1, inplace=True)
    return df


def RSI(df: pd.DataFrame, n=14):
    alpha = 1.0 / n
    gains = df.mid_c.diff()
    wins = pd.Series([ x if x >= 0 else 0.0 for x in gains ], name="wins")
    losses = pd.Series([ x * -1 if x < 0 else 0.0 for x in gains ], name="losses")
    wins_rma = wins.ewm(min_periods=n, alpha=alpha).mean()
    losses_rma = losses.ewm(min_periods=n, alpha=alpha).mean()
    rs = wins_rma / losses_rma
    df[f"RSI_{n}"] = 100.0 - (100.0 / (1.0 + rs))
    return df


def MACD(df: pd.DataFrame, n_slow=26, n_fast=12, n_signal=9):
    ema_long = df.mid_c.ewm(min_periods=n_slow, span=n_slow).mean()
    ema_short = df.mid_c.ewm(min_periods=n_fast, span=n_fast).mean()
    df['MACD'] = ema_short - ema_long
    df['SIGNAL_MD'] = df.MACD.ewm(min_periods=n_signal, span=n_signal).mean()
    df['HIST'] = df.MACD - df.SIGNAL_MD

    return df








# 2. Moving Average Crossover
def moving_average_crossover(df: pd.DataFrame, short_window=20, long_window=60):
    df['Short_MA'] = df.mid_c.rolling(window=short_window).mean()
    df['Long_MA'] = df.mid_c.rolling(window=long_window).mean()
    df['MA_Signal'] = np.where(df['Short_MA'] > df['Long_MA'], 'Buy', 'Sell')
    return df


# 5. Heikin-Ashi
def heikin_ashi(df: pd.DataFrame):
    df['HA_Close'] = (df.mid_o + df.mid_h + df.mid_l + df.mid_c) / 4
    df['HA_Open'] = (df.mid_o.shift(1) + df.mid_c.shift(1)) / 2
    df['HA_High'] = df[['mid_h', 'HA_Open', 'HA_Close']].max(axis=1)
    df['HA_Low'] = df[['mid_l', 'HA_Open', 'HA_Close']].min(axis=1)
    return df

# 6. Momentum Reversal
def momentum_reversal(df: pd.DataFrame):
    df['Stochastic'] = (df.mid_c - df.mid_l.rolling(14).min()) / (df.mid_h.rolling(14).max() - df.mid_l.rolling(14).min()) * 100
    df['Momentum_Signal'] = np.where((df['Stochastic'] > 80) & (df.mid_c < df.mid_c.shift(1)), 'Sell',
                                     np.where((df['Stochastic'] < 20) & (df.mid_c > df.mid_c.shift(1)), 'Buy', None))
    return df

# 7. Candlestick Patterns
def candlestick_patterns(df: pd.DataFrame):
    df['Bullish_Engulfing'] = np.where((df.mid_o.shift(1) > df.mid_c.shift(1)) & 
                                       (df.mid_c > df.mid_o) & 
                                       (df.mid_c > df.mid_o.shift(1)) & 
                                       (df.mid_o < df.mid_c.shift(1)), 'Bullish Engulfing', None)
    df['Bearish_Engulfing'] = np.where((df.mid_o.shift(1) < df.mid_c.shift(1)) & 
                                       (df.mid_c < df.mid_o) & 
                                       (df.mid_c < df.mid_o.shift(1)) & 
                                       (df.mid_o > df.mid_c.shift(1)), 'Bearish Engulfing', None)
    return df

# 8. Role Reversal Strategy
def role_reversal(df: pd.DataFrame):
    df['Support'] = df.mid_c.rolling(window=10).min()
    df['Resistance'] = df.mid_c.rolling(window=10).max()
    df['Role_Reversal_Signal'] = np.where(df.mid_c > df['Resistance'], 'Buy',
                                          np.where(df.mid_c < df['Support'], 'Sell', None))
    return df

# 9. 2-Period RSI
def two_period_rsi(df: pd.DataFrame):
    df['RSI'] = RSI(df, n=2)['RSI']
    df['RSI_2_Signal'] = np.where(df['RSI'] > 90, 'Sell',
                                  np.where(df['RSI'] < 10, 'Buy', None))
    return df


