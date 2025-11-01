from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
import importlib
import base64
import io
from PIL import Image

# Importa tu analizador de visión
from vision_analyzer import analyze_chart_image

app = FastAPI(title="GPT Trader Backend")

# ===========================
# 📦 MODELOS DE DATOS
# ===========================
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
# 🌐 ENDPOINT PRINCIPAL
# ===========================
@app.get("/")
def home():
    return {"message": "✅ GPT Trader backend is running!"}

# ===========================
# 🧠 ANALIZADOR DE IMAGEN (MULTIPART o BASE64)
# ===========================
@app.post("/api/analyze-image", response_model=SignalResponse)
async def analyze_image(
    file: Optional[UploadFile] = File(None),
    image_b64: Optional[str] = Form(None),
    fallback_symbol: Optional[str] = Form(None),
    fallback_timeframe: Optional[str] = Form(None)
):
    """
    Analiza una imagen enviada por archivo o en base64.
    Compatible con GPTs personalizados y llamadas directas.
    """
    try:
        # Si viene un archivo, lo convertimos a base64
        if file:
            content = await file.read()
            image_b64 = base64.b64encode(content).decode("utf-8")

        if not image_b64:
            raise ValueError("No se recibió imagen ni base64 válido")

        # Validar que sea una imagen real
        try:
            image_data = base64.b64decode(image_b64.split(",")[-1])
            Image.open(io.BytesIO(image_data))
        except Exception:
            raise ValueError("No se pudo decodificar la imagen. Usa formato .png o .jpg")

        # Ejecutar análisis de visión
        result = analyze_chart_image(image_b64)

        # Devolver el resultado del analizador
        return result

    except Exception as e:
        return {
            "signal": "ERROR",
            "pattern": None,
            "reason": str(e),
            "warnings": ["Error al analizar la imagen con vision_analyzer.py"]
        }

# ===========================
# 💰 CÁLCULO DE TAMAÑO DE POSICIÓN
# ===========================
@app.get("/api/position-size")
def position_size(account_balance: float, risk_percent: float, entry: float, stop: float):
    risk_amount = account_balance * (risk_percent / 100.0)
    risk_per_unit = abs(entry - stop)
    size = risk_amount / risk_per_unit if risk_per_unit else 0
    return {"size": round(size, 4), "risk_amount": round(risk_amount, 2)}

# ===========================
# 🗞️ ESCÁNER DE NOTICIAS
# ===========================
@app.get("/api/news-scan")
def news_scan():
    return {
        "ranked": [
            {"symbol": "XAUUSD", "score": 0.82, "drivers": ["Tensiones geopolíticas"], "risk_flags": []},
            {"symbol": "EURUSD", "score": 0.67, "drivers": ["Datos PMI Europa"], "risk_flags": ["Reunión del BCE en 1h"]},
            {"symbol": "BTCUSDT", "score": 0.55, "drivers": ["Flujos ETF"], "risk_flags": []}
        ]
    }

# ===========================
# ⚙️ ANALIZADOR DE MERCADO
# ===========================
@app.get("/api/market-signal")
def market_signal(symbol: str = "EURUSD", timeframe: str = "H1"):
    try:
        analyzer = importlib.import_module("data_analyzer")
        result = analyzer.analyze(symbol, timeframe)
        return {"ok": True, "data": result}
    except ModuleNotFoundError:
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
