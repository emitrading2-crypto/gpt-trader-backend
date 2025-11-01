# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
import importlib

app = FastAPI(title="GPT Trader Backend")

# ===========================
# 📦 MODELOS DE DATOS
# ===========================
class AnalyzeRequest(BaseModel):
    image_b64: str
    fallback_symbol: Optional[str] = None
    fallback_timeframe: Optional[str] = None

class SignalResponse(BaseModel):
    signal: str
    pattern: Optional[str] = None
    entry: Optional[float] = None
    stop: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    confidence: Optional[int] = None
    reason: Optional[str] = None
    risk_percent: Optional[float] = None
    rr: Optional[float] = None
    warnings: Optional[List[str]] = []

# ===========================
# 🌐 ENDPOINTS PRINCIPALES
# ===========================

@app.get("/")
def home():
    return {"message": "✅ GPT Trader backend is running!"}

@app.post("/api/analyze-image", response_model=SignalResponse)
def analyze_image(req: AnalyzeRequest):
    # Simulación temporal
    return {
        "signal": "LONG",
        "pattern": "Double Bottom",
        "entry": 1.2345,
        "stop": 1.2300,
        "tp1": 1.2400,
        "tp2": 1.2450,
        "confidence": 85,
        "reason": "EMA200 up, RSI 55, strong bullish reversal pattern",
        "risk_percent": 0.75,
        "rr": 2.0,
        "warnings": []
    }

@app.get("/api/position-size")
def position_size(account_balance: float, risk_percent: float, entry: float, stop: float):
    risk_amount = account_balance * (risk_percent / 100.0)
    risk_per_unit = abs(entry - stop)
    size = risk_amount / risk_per_unit if risk_per_unit else 0
    return {"size": round(size, 4), "risk_amount": round(risk_amount, 2)}

@app.get("/api/news-scan")
def news_scan():
    return {
        "ranked": [
            {
                "symbol": "XAUUSD",
                "score": 0.82,
                "drivers": ["Tensiones geopolíticas"],
                "risk_flags": []
            },
            {
                "symbol": "EURUSD",
                "score": 0.67,
                "drivers": ["Datos PMI Europa"],
                "risk_flags": ["Reunión del BCE en 1h"]
            },
            {
                "symbol": "BTCUSDT",
                "score": 0.55,
                "drivers": ["Flujos ETF"],
                "risk_flags": []
            }
        ]
    }

# ===========================
# ⚙️ ANALIZADOR DE MERCADO
# ===========================

@app.get("/api/market-signal")
def market_signal(symbol: str = "EURUSD", timeframe: str = "H1"):
    """
    Endpoint que devuelve una señal de trading simulada o real según el analizador.
    """
    try:
        analyzer = importlib.import_module("data_analyzer")
        result = analyzer.analyze(symbol, timeframe)
        return {"ok": True, "data": result}
    except ModuleNotFoundError:
        # Si no encuentra el archivo data_analyzer.py
        return {
            "ok": True,
            "data": {
                "symbol": symbol,
                "timeframe": timeframe,
                "signal": "LONG",
                "confidence": 0.8,
                "reason": "Simulación: EMA200 y RSI alcistas",
            },
            "warning": "⚠️ Módulo data_analyzer no encontrado; usando simulación."
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ===========================
# 🚀 AUTOEJECUCIÓN LOCAL
# ===========================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
