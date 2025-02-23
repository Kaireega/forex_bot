import pandas as pd
import pytz
from models.trade_decision import TradeDecision
from technicals.indicators import BollingerBands, ATR, RSI, MACD ,EMA,ADX,heikin_ashi ,identify_pin_bar# Ensure these are imported
from technicals.patterns import apply_patterns

pd.set_option('display.max_columns', None)
pd.set_option('expand_frame_repr', False)
from api.oanda_api import OandaApi
from models.trade_settings import TradeSettings
import constants.defs as defs

ADDROWS = 20


def apply_signal(row, trade_settings: TradeSettings):
    # Multi-Timeframe Trend Confirmation
    primary_trend_up = row['EMA_20'] > row['EMA_50']
    secondary_trend_up = row['EMA_20'] > row['EMA_200']
    trend_strength = row['ADX_14'] > 25
    
    # Volatility Filter
    normalized_volatility = row[f"ATR_{trade_settings.atr_period}"] / row['mid_c']
    
    # Enhanced Price Action Patterns
    bullish_pattern = (row['ENGULFING'] and row['PIN_BAR_BULL']) or row['MORNING_STAR']
    bearish_pattern = (row['ENGULFING'] and row['PIN_BAR_BEAR']) or row['EVENING_STAR']
    
    # Momentum Cluster
    rsi_ok = (row[f"RSI_{trade_settings.rsi_period}"] < trade_settings.rsi_oversold) if primary_trend_up else \
             (row[f"RSI_{trade_settings.rsi_period}"] > trade_settings.rsi_overbought)
    
    macd_ok = (row['MACD'] > row['SIGNAL_MD']) if primary_trend_up else (row['MACD'] < row['SIGNAL_MD'])
    
    # Session Timing Filter (NY/London Overlap 13:00-16:00 GMT)
    session_ok = row['session_ny_london']
    
    # Entry Conditions
    long_conditions = all([
        row.SPREAD <= trade_settings.maxspread,
        row.GAIN >= trade_settings.mingain,
        trend_strength,
        primary_trend_up,
        secondary_trend_up,
        bullish_pattern,
        rsi_ok,
        macd_ok,
        session_ok,
        normalized_volatility < 0.002,
        row.mid_c > row['EMA_20'],
        row['HA_Close'] > row['HA_Open']
    ])
    
    short_conditions = all([
        row.SPREAD <= trade_settings.maxspread,
        row.GAIN >= trade_settings.mingain,
        trend_strength,
        not primary_trend_up,
        not secondary_trend_up,
        bearish_pattern,
        rsi_ok,
        macd_ok,
        session_ok,
        normalized_volatility < 0.002,
        row.mid_c < row['EMA_20'],
        row['HA_Close'] < row['HA_Open']
    ])
    
    if long_conditions:
        return defs.BUY
    elif short_conditions:
        return defs.SELL
    
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
    """Adaptive trailing stop with volatility bands"""
    base_atr = row[f"ATR_{trade_settings.atr_period}"]
    if row.SIGNAL == defs.BUY:
        initial_sl = row.mid_c - (base_atr * 1.5)
        trailing_sl = row.mid_h - (base_atr * 0.5)
        return max(initial_sl, trailing_sl)
    elif row.SIGNAL == defs.SELL:
        initial_sl = row.mid_c + (base_atr * 1.5)
        trailing_sl = row.mid_l + (base_atr * 0.5)
        return min(initial_sl, trailing_sl)
    return 0.0

def apply_TP(row, trade_settings: TradeSettings):
    """Dynamic TP based on price structure"""
    if row.SIGNAL == defs.BUY:
        recent_high = row['mid_h'].rolling(10).max()
        return recent_high + (row[f"ATR_{trade_settings.atr_period}"] * 0.5)
    elif row.SIGNAL == defs.SELL:
        recent_low = row['mid_l'].rolling(10).min()
        return recent_low - (row[f"ATR_{trade_settings.atr_period}"] * 0.5)
    return 0.0


def process_candles(df: pd.DataFrame, pair, trade_settings: TradeSettings, log_message):
  
    df.reset_index(drop=True, inplace=True)
    df['PAIR'] = pair
    df['SPREAD'] = df.ask_c - df.bid_c


    if 'time' in df.columns:
        df['time'] = pd.to_datetime(df['time'], utc=True)
        eastern_tz = pytz.timezone('US/Eastern')
        df['time'] = df['time'].dt.tz_convert(eastern_tz)
        df['hour'] = df['time'].dt.hour
        df['session_ny_london'] = df['hour'].between(8, 11)  # 8-11 AM EST
        df['time'] = df['time'].dt.strftime('%I:%M %p')
        
    df = apply_patterns(df)
    # Calculate indicators
    df = BollingerBands(df, trade_settings.n_ma, trade_settings.n_std)
    df = ATR(df, trade_settings.atr_period)
    df = RSI(df, trade_settings.rsi_period)
    df = MACD(df) 
    df = heikin_ashi(df)
    df['EMA_20'] = EMA(df, 20)
    df['EMA_50'] = EMA(df, 50)
    df['EMA_200'] = EMA(df, 200)
    df['ADX_14'] = ADX(df)
    df =identify_pin_bar(df)
    df['average_atr'] = df[f"ATR_{trade_settings.atr_period}"].rolling(50).mean()
   


    df['GAIN'] = abs(df.mid_c - df.BB_MA)
    df['SIGNAL'] = df.apply(apply_signal, axis=1, trade_settings=trade_settings)
    df['SL'] = df.apply(apply_SL, axis=1, trade_settings=trade_settings)
    df['TP'] = df.apply(apply_TP, axis=1, trade_settings=trade_settings)
    df['LOSS'] = abs(df.mid_c - df.SL)

   
    log_cols = [
        'PAIR', 'time', 'mid_c', 'EMA_20', 'EMA_50', 'EMA_200', 'ADX_14',
        'RSI_14', 'MACD', 'SIGNAL_MD', 'HA_Close', 'HA_Open', 'session_ny_london',
        'ENGULFING', 'PIN_BAR_BULL', 'PIN_BAR_BEAR', 'SL', 'TP', 'SPREAD', 
        'GAIN', 'LOSS', 'SIGNAL'
    ]

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
