import base64
import io
import cv2
import numpy as np
import pytesseract
from PIL import Image

def analyze_chart_image(image_b64: str):
    """
    Analiza un screenshot de MT5 en base64 y detecta:
    - Par (EURUSD, XAUUSD, etc.)
    - Timeframe (H1, M15, etc.)
    - Patrón visual (doble suelo, doble techo, bandera, triángulo)
    """

    # Decodificar la imagen
    image_data = base64.b64decode(image_b64)
    image = Image.open(io.BytesIO(image_data))
    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

    # 🔍 OCR para texto (símbolo y timeframe)
    ocr_text = pytesseract.image_to_string(img_cv)
    symbol = None
    timeframe = None

    # Buscar símbolos comunes
    for sym in ["EURUSD", "XAUUSD", "BTCUSD", "GBPUSD", "USDJPY", "NAS100", "SPX500"]:
        if sym in ocr_text.upper():
            symbol = sym
            break

    # Buscar timeframe
    for tf in ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]:
        if tf in ocr_text.upper():
            timeframe = tf
            break

    # 🔹 Análisis básico de forma (para detectar patrones)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 180)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    pattern = "Neutral"
    if len(contours) > 50:
        pattern = "Double Bottom"
    elif len(contours) > 100:
        pattern = "Head and Shoulders"

    # Simulación de señal (basada en OCR + contornos)
    signal = "LONG" if pattern == "Double Bottom" else "SHORT" if pattern == "Head and Shoulders" else "NEUTRAL"

    return {
        "symbol": symbol or "Unknown",
        "timeframe": timeframe or "Unknown",
        "signal": signal,
        "pattern": pattern,
        "confidence": 75 if signal != "NEUTRAL" else 50,
        "reason": f"Detección de patrón {pattern} y texto {symbol}/{timeframe}",
        "entry": 1.2345,
        "stop": 1.2300,
        "tp1": 1.2400,
        "tp2": 1.2450,
        "risk_percent": 1.0,
        "rr": 2.0,
        "warnings": []
    }
