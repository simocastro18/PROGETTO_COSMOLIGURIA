import os
import requests
from flask import Flask, render_template, Response
from datetime import datetime

app = Flask(__name__)

NASA_API_KEY = os.environ.get("NASA_API_KEY", "DEMO_KEY")

@app.route("/")
def index():
    # NASA APOD
    nasa_data = {}
    try:
        r = requests.get(
            f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}",
            timeout=10
        )
        nasa_data = r.json()
    except Exception as e:
        nasa_data = {
            "title": "Connessione NASA non disponibile",
            "explanation": "Riprova tra qualche minuto.",
            "url": "",
            "media_type": "image"
        }

    # Meteo Genova via Open-Meteo (lat/lon Genova)
    meteo = {}
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=44.4056&longitude=8.9463"
            "&current=temperature_2m,apparent_temperature,weathercode,"
            "windspeed_10m,relativehumidity_2m,precipitation"
            "&timezone=Europe/Rome"
            "&wind_speed_unit=kmh",
            timeout=10
        )
        raw = r.json()
        current = raw["current"]
        meteo = {
            "temp": round(current["temperature_2m"]),
            "feels": round(current["apparent_temperature"]),
            "humidity": current["relativehumidity_2m"],
            "wind": round(current["windspeed_10m"]),
            "rain": current["precipitation"],
            "code": current["weathercode"],
            "desc": wmo_to_desc(current["weathercode"]),
            "icon": wmo_to_icon(current["weathercode"]),
        }
    except Exception as e:
        meteo = {
            "temp": "--", "feels": "--", "humidity": "--",
            "wind": "--", "rain": "--", "code": 0,
            "desc": "Dati non disponibili", "icon": "🌀"
        }

    now = datetime.now().strftime("%A %d %B %Y, %H:%M")
    return render_template("index.html", nasa=nasa_data, meteo=meteo, now=now)


@app.route("/nasa-image")
def nasa_image():
    try:
        apod = requests.get(
            f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}",
            timeout=10
        ).json()
        img_url = apod.get("hdurl") or apod.get("url", "")
        if not img_url:
            return "No image URL", 404
        r = requests.get(img_url, timeout=15, stream=True)
        return Response(
            r.iter_content(chunk_size=8192),
            content_type=r.headers.get("Content-Type", "image/jpeg")
        )
    except Exception as e:
        return str(e), 500


def wmo_to_desc(code):
    mapping = {
        0: "Sereno",
        1: "Prevalentemente sereno", 2: "Parzialmente nuvoloso", 3: "Nuvoloso",
        45: "Nebbia", 48: "Nebbia con brina",
        51: "Pioggerella leggera", 53: "Pioggerella moderata", 55: "Pioggerella intensa",
        61: "Pioggia leggera", 63: "Pioggia moderata", 65: "Pioggia forte",
        71: "Neve leggera", 73: "Neve moderata", 75: "Neve intensa",
        80: "Rovesci leggeri", 81: "Rovesci moderati", 82: "Rovesci violenti",
        95: "Temporale", 96: "Temporale con grandine", 99: "Temporale forte",
    }
    return mapping.get(code, "Condizioni variabili")


def wmo_to_icon(code):
    if code == 0: return "☀️"
    if code in [1, 2]: return "🌤️"
    if code == 3: return "☁️"
    if code in [45, 48]: return "🌫️"
    if code in [51, 53, 55, 61, 63, 65]: return "🌧️"
    if code in [71, 73, 75]: return "❄️"
    if code in [80, 81, 82]: return "🌦️"
    if code in [95, 96, 99]: return "⛈️"
    return "🌈"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)