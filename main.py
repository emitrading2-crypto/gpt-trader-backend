from fastapi import FastAPI, UploadFile, File, HTTPException
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
# 🌐 ENDPOINT PRINCIPAL
# ===========================
@app.get("/")
def home():
    return {"message": "✅ GPT Trader backend is running!"}

# ===========================
# 🧠 ANALIZADOR DE IMAGEN (Base64)
# ===========================
@app.post("/api/analyze-image", response_model=SignalResponse)
def analyze_image(req: AnalyzeRequest):
    """
    Analiza una imagen enviada en formato base64 (desde MT5 o ChatGPT).
    """
    try:
        if not req.image_b64 or len(req.image_b64) < 50:
            raise ValueError("La cadena base64 está vacía o incompleta")

        # Intentar decodificar imagen
        image_data = base64.b64decode(req.image_b64.split(",")[-1])
        img = Image.open(io.BytesIO(image_data))

        # Procesar con el analizador de visión
        result = analyze_chart_image(req.image_b64)
        return result

    except Exception as e:
        return {
            "signal": "ERROR",
            "pattern": None,
            "reason": f"Error al analizar imagen: {str(e)}",
            "warnings": [
                "El backend no pudo decodificar la imagen. Asegúrate de que esté en formato PNG o JPG válido."
            ],
        }

# ===========================
# 🧩 ANALIZADOR DE ARCHIVOS (Upload)
# ===========================
@app.post("/api/analyze-file", response_model=SignalResponse)
async def analyze_file(file: UploadFile = File(...)):
    """
    Analiza una imagen enviada como archivo (PNG/JPG).
    """
    try:
        contents = await file.read()

        # Validar tipo
        if file.content_type not in ["image/png", "image/jpeg"]:
            raise HTTPException(status_code=400, detail="Formato no soportado. Usa PNG o JPG.")

        # Validar lectura
        img = Image.open(io.BytesIO(contents))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # Procesar
        result = analyze_chart_image(img_str)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando archivo: {str(e)}")

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
