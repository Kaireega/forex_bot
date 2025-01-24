import pandas as pd
from models.trade_decision import TradeDecision
from technicals.indicators import BollingerBands, ATR, RSI, MACD  # Ensure these are imported

pd.set_option('display.max_columns', None)
pd.set_option('expand_frame_repr', False)
from api.oanda_api import OandaApi
from models.trade_settings import TradeSettings
import constants.defs as defs

ADDROWS = 20


def apply_signal(row, trade_settings: TradeSettings):
    """
    Determines the BUY or SELL signal based on Bollinger Bands, RSI, and MACD conditions.
    """
    if (
        row.SPREAD <= trade_settings.maxspread and
        row.GAIN >= trade_settings.mingain and
        row.mid_c < row.BB_LW and row.mid_o > row.BB_LW and  # Bollinger Bands condition for BUY
        row[f"RSI_{trade_settings.rsi_period}"] < trade_settings.rsi_oversold and  # RSI condition for oversold
        row.MACD > row.SIGNAL 
       
    ):
        return defs.BUY

    elif (
        row.SPREAD <= trade_settings.maxspread and
        row.GAIN >= trade_settings.mingain and
        row.mid_c > row.BB_UP and row.mid_o < row.BB_UP and  # Bollinger Bands condition for SELL
        row[f"RSI_{trade_settings.rsi_period}"] > trade_settings.rsi_overbought  and # RSI condition for overbought
       row.MACD < row.SIGNAL 
    ):
        return defs.SELL

    return defs.NONE


def apply_SL(row, trade_settings: TradeSettings):
    """
    Calculates the Stop Loss (SL) using ATR for dynamic adjustment based on volatility.
    """
    if row.SIGNAL == defs.BUY:
        return row.mid_c - (row[f"ATR_{trade_settings.atr_period}"] * trade_settings.atr_multiplier)
    elif row.SIGNAL == defs.SELL:
        return row.mid_c + (row[f"ATR_{trade_settings.atr_period}"] * trade_settings.atr_multiplier)
    return 0.0


def apply_TP(row, trade_settings: TradeSettings):
    """
    Calculates the Take Profit (TP) using ATR and risk-reward ratio.
    """
    if row.SIGNAL == defs.BUY:
        return row.mid_c + (row[f"ATR_{trade_settings.atr_period}"] * trade_settings.atr_multiplier * trade_settings.riskreward)
    elif row.SIGNAL == defs.SELL:
        return row.mid_c - (row[f"ATR_{trade_settings.atr_period}"] * trade_settings.atr_multiplier * trade_settings.riskreward)
    return 0.0


def process_candles(df: pd.DataFrame, pair, trade_settings: TradeSettings, log_message):
    """
    Processes the candle data and calculates trading signals, SL, TP, and other metrics.
    """
    df.reset_index(drop=True, inplace=True)
    df['PAIR'] = pair
    df['SPREAD'] = df.ask_c - df.bid_c

    # Calculate indicators
    df = BollingerBands(df, trade_settings.n_ma, trade_settings.n_std)
    df = ATR(df, trade_settings.atr_period)
    df = RSI(df, trade_settings.rsi_period)
    df = MACD(df)  # Ensure MACD uses default or trade_settings parameters

    df['GAIN'] = abs(df.mid_c - df.BB_MA)
    df['SIGNAL'] = df.apply(apply_signal, axis=1, trade_settings=trade_settings)
    df['SL'] = df.apply(apply_SL, axis=1, trade_settings=trade_settings)
    df['TP'] = df.apply(apply_TP, axis=1, trade_settings=trade_settings)
    df['LOSS'] = abs(df.mid_c - df.SL)

    log_cols = ['PAIR', 'time', 'mid_c', 'mid_o', 'SL', 'TP', 'SPREAD', 'GAIN', 'LOSS', 'SIGNAL']
    log_message(f"process_candles:\n{df[log_cols].tail()}", pair)
  
    return df[log_cols].iloc[-1]


def fetch_candles(pair, row_count, candle_time, granularity, api: OandaApi, log_message):
    """
    Fetches the required number of candles for the specified pair and granularity.
    """
    df = api.get_candles_df(pair, count=row_count, granularity=granularity)

    if df is None or df.shape[0] == 0:
        log_message("tech_manager fetch_candles failed to get candles", pair)
        return None
    
    if df.iloc[-1].time != candle_time:
        log_message(f"tech_manager fetch_candles {df.iloc[-1].time} not correct", pair)
        return None

    return df


def get_trade_decision(candle_time, pair, granularity, api: OandaApi, trade_settings: TradeSettings, log_message):
    """
    Determines the trade decision based on the latest market data and trade settings.
    """
    max_rows = trade_settings.n_ma + ADDROWS

    log_message(f"tech_manager: max_rows:{max_rows} candle_time:{candle_time} granularity:{granularity}", pair)

    df = fetch_candles(pair, max_rows, candle_time, granularity, api, log_message)

    if df is not None:
        last_row = process_candles(df, pair, trade_settings, log_message)
        return TradeDecision(last_row)

    return None
