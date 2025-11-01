# data_analyzer.py
# Módulo de análisis técnico con conexión a MetaTrader 5
# Requiere: pip install MetaTrader5 pandas ta numpy

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from datetime import datetime

def connect_mt5():
    if not mt5.initialize():
        raise Exception("❌ No se pudo conectar con MetaTrader 5")
    print("✅ Conectado a MetaTrader 5")

def fetch_data(symbol: str = "EURUSD", timeframe: str = "H1", bars: int = 500):
    tf_map = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
    }
    tf = tf_map.get(timeframe, mt5.TIMEFRAME_H1)

    rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
    if rates is None or len(rates) == 0:
        raise Exception(f"No se pudieron obtener velas para {symbol}")

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)
    return df

def analyze(symbol: str = "EURUSD", timeframe: str = "H1"):
    connect_mt5()
    df = fetch_data(symbol, timeframe)

    df["ema20"] = EMAIndicator(df["close"], window=20).ema_indicator()
    df["ema200"] = EMAIndicator(df["close"], window=200).ema_indicator()
    df["rsi"] = RSIIndicator(df["close"], window=14).rsi()
    macd = MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    latest = df.iloc[-1]

    trend_up = latest["ema20"] > latest["ema200"]
    rsi_val = latest["rsi"]
    macd_up = latest["macd"] > latest["macd_signal"]

    if trend_up and macd_up and rsi_val < 70:
        signal = "LONG"
        reason = "Cruce EMA + MACD alcista"
    elif not trend_up and not macd_up and rsi_val > 30:
        signal = "SHORT"
        reason = "Cruce EMA bajista + MACD negativo"
    else:
        signal = "NEUTRAL"
        reason = "Condiciones mixtas"

    confidence = float(np.clip(abs(rsi_val - 50) / 50, 0, 1))

    result = {
        "symbol": symbol,
        "timeframe": timeframe,
        "signal": signal,
        "confidence": round(confidence, 2),
        "reason": reason,
        "rsi": round(rsi_val, 2),
        "ema20": round(latest["ema20"], 5),
        "ema200": round(latest["ema200"], 5),
    }

    mt5.shutdown()
    return result

if __name__ == "__main__":
    print(analyze("EURUSD", "H1"))
