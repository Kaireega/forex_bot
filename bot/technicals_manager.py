import pandas as pd
import pytz
from models.trade_decision import TradeDecision
from technicals.indicators import BollingerBands, ATR, RSI, MACD ,EMA,ADX,identify_pin_bar# Ensure these are imported
from technicals.patterns import apply_patterns

pd.set_option('display.max_columns', None)
pd.set_option('expand_frame_repr', False)
from api.oanda_api import OandaApi
from models.trade_settings import TradeSettings
import constants.defs as defs

ADDROWS = 20


def apply_signal(row, trade_settings: TradeSettings):
    # Trend Filter
    trend_up = row['EMA_20'] > row['EMA_50']
    trend_strength = row['ADX_14'] > 25
    
    # Price Action Filter
    bullish_pattern = row['ENGULFING'] or row['PIN_BAR_BULL']
    bearish_pattern = row['ENGULFING'] or row['PIN_BAR_BEAR']
    
    # Momentum Confirmation
    rsi_ok = ( (row[f"RSI_{trade_settings.rsi_period}"] < trade_settings.rsi_oversold) or (row[f"RSI_{trade_settings.rsi_period}"] > trade_settings.rsi_overbought))
    
    macd_ok = (row['MACD'] > row['SIGNAL_MD']) if trend_up else (row['MACD'] < row['SIGNAL_MD'])
    
    # Entry Conditions
    if all([
        row.SPREAD <= trade_settings.maxspread,
        row.GAIN >= trade_settings.mingain,
        trend_strength,
        bullish_pattern if trend_up else bearish_pattern,
        rsi_ok,
        macd_ok,
        (trend_up and row.mid_c > row['EMA_20']) or 
        (not trend_up and row.mid_c < row['EMA_20'])
    ]):
        return defs.BUY if trend_up else defs.SELL
    
    return defs.NONE

# ----------------------------------------------------------------------
    # if (
    #     row.SPREAD <= trade_settings.maxspread and
    #     row.GAIN >= trade_settings.mingain and
    #     # row.mid_c < row.BB_LW and row.mid_o > row.BB_LW and  # Bollinger Bands condition for BUY
    #     row[f"RSI_{trade_settings.rsi_period}"] < trade_settings.rsi_oversold and  # RSI condition for oversold
    #     row.MACD > row.SIGNAL_MD and 
    #     row.PREV_SHOOTING_STAR == True and
    #     row.ENGULFING == True 
    # ):
    #     return defs.BUY

    # elif (
    #     row.SPREAD <= trade_settings.maxspread and
    #     row.GAIN >= trade_settings.mingain and
    #     # row.mid_c > row.BB_UP and row.mid_o < row.BB_UP and  # Bollinger Bands condition for SELL
    #     row[f"RSI_{trade_settings.rsi_period}"] > trade_settings.rsi_overbought  and # RSI condition for overbought
    #     row.MACD < row.SIGNAL_MD and
    #     row.PREV_HANGING_MAN == True and 
    #     row.ENGULFING == True
        
    # ):
    #     return defs.SELL

    # return defs.NONE


# def apply_SL(row, trade_settings: TradeSettings):
#     """
#     Calculates the Stop Loss (SL) using ATR for dynamic adjustment based on volatility.
#     """
#     if row.SIGNAL == defs.BUY:
#         return row.mid_c - (row[f"ATR_{trade_settings.atr_period}"] * trade_settings.atr_multiplier)
#     elif row.SIGNAL == defs.SELL:
#         return row.mid_c + (row[f"ATR_{trade_settings.atr_period}"] * trade_settings.atr_multiplier)
#     return 0.0


def apply_SL(row, trade_settings: TradeSettings):
    """
    Adjusts Stop Loss dynamically using a trailing stop (50% of ATR).
    """
    atr_sl = row[f"ATR_{trade_settings.atr_period}"] * trade_settings.atr_multiplier
    trailing_sl = row[f"ATR_{trade_settings.atr_period}"] * 0.5  # 50% ATR trailing stop

    if row.SIGNAL == defs.BUY:
        return max(row.mid_c - atr_sl, row.mid_c - trailing_sl)
    elif row.SIGNAL == defs.SELL:
        return min(row.mid_c + atr_sl, row.mid_c + trailing_sl)

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


    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'], utc=True)
        eastern_tz = pytz.timezone('US/Eastern')
        df['time'] = df['time'].dt.tz_convert(eastern_tz)
        df['time'] = df['time'].dt.strftime('%I:%M %p')
        
    df = apply_patterns(df)
    # Calculate indicators
    df = BollingerBands(df, trade_settings.n_ma, trade_settings.n_std)
    df = ATR(df, trade_settings.atr_period)
    df = RSI(df, trade_settings.rsi_period)
    df = MACD(df)  # Ensure MACD uses default or trade_settings parameters
    df['EMA_20'] = EMA(df, 20)
    df['EMA_50'] = EMA(df, 50)
    df['ADX_14'] = ADX(df)
    df =identify_pin_bar(df)
    


    df['GAIN'] = abs(df.mid_c - df.BB_MA)
    df['SIGNAL'] = df.apply(apply_signal, axis=1, trade_settings=trade_settings)
    df['SL'] = df.apply(apply_SL, axis=1, trade_settings=trade_settings)
    df['TP'] = df.apply(apply_TP, axis=1, trade_settings=trade_settings)
    df['LOSS'] = abs(df.mid_c - df.SL)
    # df['PREV_SHOOTING_STAR'] = df['SHOOTING_STAR'].shift(1)
    # df['PREV_HANGING_MAN'] = df['HANGING_MAN'].shift(1)
   
    # log_cols = ['PAIR', 'time', 'mid_c', 'mid_o', 'SL', 'TP', 'SPREAD', 'GAIN', 'LOSS',
    #              'SIGNAL','MACD','SIGNAL_MD','HIST','RSI_14','BB_MA','BB_UP',
    #              'BB_LW','BB_Signal','ATR_14','PREV_SHOOTING_STAR','ENGULFING',
    #              'SHOOTING_STAR','PREV_HANGING_MAN','HANGING_MAN']



    log_cols = ['PAIR', 'time', 'mid_c', 'EMA_20', 'EMA_50', 'ADX_14', 
                'RSI_14', 'MACD', 'SIGNAL_MD', 'ENGULFING', 'PIN_BAR_BULL', 
                'PIN_BAR_BEAR', 'SL', 'TP', 'SPREAD', 'GAIN', 'LOSS', 'SIGNAL']


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
