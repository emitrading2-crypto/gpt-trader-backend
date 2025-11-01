from fastapi import FastAPI, UploadFile, File, Form, Body
from pydantic import BaseModel
from typing import Optional, List
import importlib, base64, io
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
# 🧠 ANALIZADOR DE IMAGEN (VISION)
# ===========================
def _decode_b64_image(image_b64: str) -> bytes:
    if "," in image_b64 and ";base64" in image_b64:
        image_b64 = image_b64.split(",", 1)[1]
    return base64.b64decode(image_b64)

def _ensure_pillow_image(img_bytes: bytes) -> Image.Image:
    im = Image.open(io.BytesIO(img_bytes))
    if im.mode not in ("RGB", "RGBA", "L"):
        im = im.convert("RGB")
    elif im.mode == "RGBA":
        im = im.convert("RGB")
    return im


@app.post("/api/analyze-image", response_model=SignalResponse)
async def analyze_image(
    # Soporte para multipart/form-data
    file: UploadFile | None = File(default=None),
    fallback_symbol_form: Optional[str] = Form(default=None),
    fallback_timeframe_form: Optional[str] = Form(default=None),

    # Soporte para JSON directo
    image_b64_json: Optional[str] = Body(default=None, embed=True),
    fallback_symbol_json: Optional[str] = Body(default=None, embed=True),
    fallback_timeframe_json: Optional[str] = Body(default=None, embed=True),
):
    """
    Acepta:
    - multipart/form-data: file (PNG/JPG) + fallbacks opcionales
    - application/json: { image_b64, fallback_symbol, fallback_timeframe }
    """
    try:
        img_bytes = None
        symbol = fallback_symbol_form or fallback_symbol_json
        timeframe = fallback_timeframe_form or fallback_timeframe_json

        if file is not None:
            img_bytes = await file.read()
        elif image_b64_json:
            img_bytes = _decode_b64_image(image_b64_json)

        if not img_bytes:
            return {
                "signal": "NEUTRAL",
                "pattern": None,
                "confidence": 0,
                "reason": "No se recibió archivo ni image_b64.",
                "warnings": ["missing_image"]
            }

        # Convertir imagen a formato correcto
        pil_img = _ensure_pillow_image(img_bytes)

        # Intentar usar vision_analyzer
        try:
            result = analyze_chart_image(pil_img)
            return result
        except Exception as inner_e:
            return {
                "signal": "ERROR",
                "pattern": None,
                "reason": f"Error interno en vision_analyzer: {inner_e}",
                "warnings": ["vision_analyzer falló"]
            }

    except Exception as e:
        return {
            "signal": "NEUTRAL",
            "pattern": None,
            "confidence": 0,
            "reason": f"Error al procesar la imagen: {e}",
            "warnings": ["image_decode_error"]
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
    """
    Endpoint que devuelve una señal de trading simulada o real según el analizador.
    """
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
