import os
from dotenv import load_dotenv
import requests
import random
from flask import Flask, jsonify, render_template, request

# read .env file if present
load_dotenv()

app = Flask(__name__)

# load API key from environment to avoid committing secrets
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not OPENWEATHER_API_KEY:
    raise RuntimeError("OPENWEATHER_API_KEY environment variable is not set")

SIMULATION_RUNS = 10000

# ─────────────────────────────────────────
# AREA / LOCALITY DATABASE
# ─────────────────────────────────────────
CITY_AREAS = {
    "Pune": [
        {"name": "Shivajinagar",  "lat": 18.5308, "lon": 73.8474, "risk_modifier": 0.05,  "tags": ["low-lying", "dense-traffic"]},
        {"name": "Kothrud",       "lat": 18.5074, "lon": 73.8077, "risk_modifier": -0.05, "tags": ["hilly", "residential"]},
        {"name": "Hadapsar",      "lat": 18.5018, "lon": 73.9260, "risk_modifier": 0.10,  "tags": ["industrial", "flood-prone"]},
        {"name": "Kondhwa",       "lat": 18.4637, "lon": 73.8759, "risk_modifier": 0.08,  "tags": ["low-lying", "residential"]},
        {"name": "Wakad",         "lat": 18.5986, "lon": 73.7608, "risk_modifier": -0.03, "tags": ["elevated", "IT-hub"]},
        {"name": "Pimpri",        "lat": 18.6298, "lon": 73.7997, "risk_modifier": 0.07,  "tags": ["industrial", "dense"]},
    ],
    "Mumbai": [
        {"name": "Kurla",         "lat": 19.0726, "lon": 72.8795, "risk_modifier": 0.20,  "tags": ["flood-prone", "dense"]},
        {"name": "Dharavi",       "lat": 19.0417, "lon": 72.8534, "risk_modifier": 0.25,  "tags": ["extremely-flood-prone", "informal-settlement"]},
        {"name": "Bandra",        "lat": 19.0596, "lon": 72.8295, "risk_modifier": 0.05,  "tags": ["coastal", "elevated"]},
        {"name": "Andheri",       "lat": 19.1136, "lon": 72.8697, "risk_modifier": 0.10,  "tags": ["low-lying", "dense-traffic"]},
        {"name": "Borivali",      "lat": 19.2307, "lon": 72.8567, "risk_modifier": -0.05, "tags": ["hilly", "national-park-adjacent"]},
        {"name": "Colaba",        "lat": 18.9067, "lon": 72.8147, "risk_modifier": 0.12,  "tags": ["coastal", "sea-level"]},
    ],
    "Delhi": [
        {"name": "Connaught Place","lat": 28.6315, "lon": 77.2167, "risk_modifier": 0.05,  "tags": ["central", "commercial"]},
        {"name": "Rohini",        "lat": 28.7041, "lon": 77.1025, "risk_modifier": 0.02,  "tags": ["planned", "residential"]},
        {"name": "Yamuna Vihar",  "lat": 28.7023, "lon": 77.2811, "risk_modifier": 0.18,  "tags": ["flood-plain", "riverbank"]},
        {"name": "Dwarka",        "lat": 28.5921, "lon": 77.0460, "risk_modifier": -0.02, "tags": ["planned", "metro-connected"]},
        {"name": "Okhla",         "lat": 28.5355, "lon": 77.2710, "risk_modifier": 0.12,  "tags": ["industrial", "flood-prone"]},
        {"name": "Saket",         "lat": 28.5245, "lon": 77.2066, "risk_modifier": 0.00,  "tags": ["residential", "elevated"]},
    ],
    "Bengaluru": [
        {"name": "Koramangala",   "lat": 12.9352, "lon": 77.6245, "risk_modifier": -0.05, "tags": ["elevated", "IT-hub"]},
        {"name": "Whitefield",    "lat": 12.9698, "lon": 77.7500, "risk_modifier": 0.05,  "tags": ["IT-corridor", "drainage-issues"]},
        {"name": "Ejipura",       "lat": 12.9445, "lon": 77.6201, "risk_modifier": 0.15,  "tags": ["low-lying", "waterlogging"]},
        {"name": "Yelahanka",     "lat": 13.1007, "lon": 77.5963, "risk_modifier": -0.03, "tags": ["outskirts", "less-dense"]},
        {"name": "HSR Layout",    "lat": 12.9116, "lon": 77.6370, "risk_modifier": 0.08,  "tags": ["lake-adjacent", "residential"]},
        {"name": "Majestic",      "lat": 12.9762, "lon": 77.5713, "risk_modifier": 0.10,  "tags": ["central", "high-traffic"]},
    ],
    "Chennai": [
        {"name": "Adyar",         "lat": 13.0012, "lon": 80.2565, "risk_modifier": 0.20,  "tags": ["coastal", "flood-prone", "riverbank"]},
        {"name": "T. Nagar",      "lat": 13.0418, "lon": 80.2341, "risk_modifier": 0.10,  "tags": ["commercial", "drainage-poor"]},
        {"name": "Velachery",     "lat": 12.9815, "lon": 80.2180, "risk_modifier": 0.22,  "tags": ["lake-bed", "extremely-flood-prone"]},
        {"name": "Anna Nagar",    "lat": 13.0850, "lon": 80.2101, "risk_modifier": -0.05, "tags": ["planned", "elevated"]},
        {"name": "Sholinganallur","lat": 12.9010, "lon": 80.2279, "risk_modifier": 0.08,  "tags": ["IT-corridor", "coastal-adjacent"]},
        {"name": "Royapuram",     "lat": 13.1143, "lon": 80.2962, "risk_modifier": 0.15,  "tags": ["coastal", "fishing-community"]},
    ],
    "Hyderabad": [
        {"name": "Banjara Hills",  "lat": 17.4138, "lon": 78.4486, "risk_modifier": -0.08, "tags": ["hilly", "affluent"]},
        {"name": "LB Nagar",       "lat": 17.3479, "lon": 78.5529, "risk_modifier": 0.12,  "tags": ["low-lying", "flood-prone"]},
        {"name": "Secunderabad",   "lat": 17.4399, "lon": 78.4983, "risk_modifier": 0.05,  "tags": ["cantonment", "mixed"]},
        {"name": "Hitech City",    "lat": 17.4435, "lon": 78.3772, "risk_modifier": -0.03, "tags": ["IT-hub", "planned"]},
        {"name": "Kukatpally",     "lat": 17.4849, "lon": 78.3961, "risk_modifier": 0.08,  "tags": ["dense", "waterlogging"]},
        {"name": "Mehdipatnam",    "lat": 17.3934, "lon": 78.4350, "risk_modifier": 0.10,  "tags": ["low-lying", "dense-traffic"]},
    ],
    "Kolkata": [
        {"name": "Park Street",    "lat": 22.5518, "lon": 88.3523, "risk_modifier": 0.10,  "tags": ["central", "drainage-old"]},
        {"name": "Salt Lake",      "lat": 22.5797, "lon": 88.4137, "risk_modifier": -0.05, "tags": ["planned", "IT-hub"]},
        {"name": "Howrah",         "lat": 22.5958, "lon": 88.2636, "risk_modifier": 0.18,  "tags": ["riverbank", "flood-prone"]},
        {"name": "Topsia",         "lat": 22.5407, "lon": 88.3766, "risk_modifier": 0.15,  "tags": ["low-lying", "industrial"]},
        {"name": "New Town",       "lat": 22.6204, "lon": 88.4598, "risk_modifier": -0.08, "tags": ["planned", "elevated"]},
        {"name": "Behala",         "lat": 22.4990, "lon": 88.3138, "risk_modifier": 0.12,  "tags": ["residential", "drainage-poor"]},
    ],
    "Ahmedabad": [
        {"name": "Navrangpura",    "lat": 23.0395, "lon": 72.5622, "risk_modifier": 0.00,  "tags": ["central", "commercial"]},
        {"name": "Maninagar",      "lat": 22.9917, "lon": 72.6109, "risk_modifier": 0.08,  "tags": ["riverbank", "dense"]},
        {"name": "Bodakdev",       "lat": 23.0545, "lon": 72.5050, "risk_modifier": -0.05, "tags": ["planned", "elevated"]},
        {"name": "Vatva",          "lat": 22.9625, "lon": 72.6520, "risk_modifier": 0.12,  "tags": ["industrial", "drainage-poor"]},
        {"name": "Gota",           "lat": 23.0939, "lon": 72.5410, "risk_modifier": -0.03, "tags": ["outskirts", "less-dense"]},
        {"name": "Bapunagar",      "lat": 23.0312, "lon": 72.6176, "risk_modifier": 0.10,  "tags": ["dense", "old-drainage"]},
    ],
    "Nagpur": [
        {"name": "Sitabuldi",      "lat": 21.1458, "lon": 79.0882, "risk_modifier": 0.05,  "tags": ["central", "commercial"]},
        {"name": "Dharampeth",     "lat": 21.1429, "lon": 79.0619, "risk_modifier": -0.03, "tags": ["residential", "elevated"]},
        {"name": "Nandanvan",      "lat": 21.1278, "lon": 79.1169, "risk_modifier": 0.10,  "tags": ["low-lying", "flood-prone"]},
        {"name": "Hingna",         "lat": 21.1043, "lon": 78.9762, "risk_modifier": 0.08,  "tags": ["industrial", "outskirts"]},
        {"name": "Manewada",       "lat": 21.1056, "lon": 79.0956, "risk_modifier": 0.12,  "tags": ["low-lying", "waterlogging"]},
        {"name": "Pratap Nagar",   "lat": 21.1622, "lon": 79.0718, "risk_modifier": 0.03,  "tags": ["mixed", "residential"]},
    ],
    "Surat": [
        {"name": "Adajan",         "lat": 21.2130, "lon": 72.7967, "risk_modifier": 0.05,  "tags": ["residential", "riverside"]},
        {"name": "Katargam",       "lat": 21.2270, "lon": 72.8540, "risk_modifier": 0.15,  "tags": ["textile-industrial", "dense"]},
        {"name": "Udhna",          "lat": 21.1680, "lon": 72.8460, "risk_modifier": 0.18,  "tags": ["industrial", "flood-prone"]},
        {"name": "Vesu",           "lat": 21.1537, "lon": 72.7620, "risk_modifier": -0.05, "tags": ["planned", "elevated"]},
        {"name": "Piplod",         "lat": 21.1750, "lon": 72.7880, "risk_modifier": -0.03, "tags": ["residential", "planned"]},
        {"name": "Rander",         "lat": 21.2380, "lon": 72.8070, "risk_modifier": 0.10,  "tags": ["riverside", "old-town"]},
    ],
}

RAIN_DESCRIPTION_MAP = {
    "light intensity drizzle": "light","drizzle": "light","heavy intensity drizzle": "moderate",
    "light intensity drizzle rain": "light","drizzle rain": "moderate","heavy intensity drizzle rain": "moderate",
    "shower rain and drizzle": "moderate","heavy shower rain and drizzle": "heavy","shower drizzle": "light",
    "light rain": "light","moderate rain": "moderate","heavy intensity rain": "heavy","very heavy rain": "heavy",
    "extreme rain": "extreme","freezing rain": "moderate","light intensity shower rain": "light",
    "shower rain": "moderate","heavy intensity shower rain": "heavy","ragged shower rain": "moderate",
    "thunderstorm with light rain": "moderate","thunderstorm with rain": "heavy","thunderstorm with heavy rain": "extreme",
    "thunderstorm with light drizzle": "light","thunderstorm with drizzle": "moderate",
    "thunderstorm": "heavy","light thunderstorm": "moderate","heavy thunderstorm": "extreme","ragged thunderstorm": "extreme",
}

DRAIN_OVERLOAD_PROB     = {"none": 0.01, "light": 0.08, "moderate": 0.35, "heavy": 0.65, "extreme": 0.85}
ROAD_FLOOD_PROB         = {True: 0.70, False: 0.02}
TRAFFIC_CONGESTION_PROB = {True: 0.75, False: 0.18}
EMERGENCY_DELAY_PROB    = {True: 0.60, False: 0.08}

def risk_label(p):
    if p < 0.20: return "low"
    if p < 0.50: return "moderate"
    if p < 0.75: return "high"
    return "critical"

def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))

def classify_rain(main, description):
    if main not in ["Rain", "Drizzle", "Thunderstorm"]: return "none"
    return RAIN_DESCRIPTION_MAP.get(description.lower(), "moderate")

def get_weather_type(main):
    if main == "Thunderstorm": return "thunderstorm"
    if main in ["Rain", "Drizzle"]: return "rain"
    if main in ["Haze","Smoke","Dust","Sand","Fog","Mist","Ash","Squall"]: return "haze"
    return "clear"

def ai_alert(weather_type, rain_level, probs):
    max_prob = max(probs.values()) if probs else 0
    max_key  = max(probs, key=probs.get) if probs else ""
    key_label = max_key.replace("_", " ").title()
    if weather_type == "thunderstorm":
        if max_prob > 0.70: return f"🚨 CRITICAL: Thunderstorm active. {key_label} at {max_prob*100:.0f}%. Evacuate flood-prone zones."
        return f"⚠️ Thunderstorm detected. Monitor {key_label} ({max_prob*100:.0f}%). Avoid travel."
    if weather_type == "rain":
        if rain_level == "extreme": return "🚨 EXTREME rainfall. Drain overload imminent. Road flooding likely. Stay indoors."
        if rain_level == "heavy":   return f"🔴 Heavy rain alert. {key_label} risk at {max_prob*100:.0f}%. Avoid low-lying areas."
        if rain_level == "moderate":return f"⚠️ Moderate rainfall. Possible waterlogging. {key_label}: {max_prob*100:.0f}%."
        if rain_level == "light":   return f"🌧️ Light rain. Low immediate risk. Monitor {key_label.lower()} zones."
        return "✅ No significant rainfall. All systems nominal."
    if weather_type == "haze": return f"🌫️ Haze detected. Visibility reduced. {key_label} at {max_prob*100:.0f}%. Wear masks."
    return "✅ Weather stable. No significant urban risk detected."

def simulate_rain(rain_level, risk_modifier=0.0, runs=SIMULATION_RUNS):
    base_drain_prob = clamp(DRAIN_OVERLOAD_PROB[rain_level] + risk_modifier)
    drain = flood = traffic = delay = 0
    for _ in range(runs):
        d = random.random() < base_drain_prob; drain += d
        f = random.random() < (ROAD_FLOOD_PROB[True] if d else ROAD_FLOOD_PROB[False]); flood += f
        t = random.random() < (TRAFFIC_CONGESTION_PROB[True] if f else TRAFFIC_CONGESTION_PROB[False]); traffic += t
        e = random.random() < (EMERGENCY_DELAY_PROB[True] if t else EMERGENCY_DELAY_PROB[False]); delay += e
    return {"drain_overload": round(drain/runs,4), "road_flooding": round(flood/runs,4), "traffic_congestion": round(traffic/runs,4), "emergency_delay": round(delay/runs,4)}

def simulate_thunderstorm(risk_modifier=0.0, runs=SIMULATION_RUNS):
    base_power = clamp(0.72 + risk_modifier); base_flood = clamp(0.80 + risk_modifier)
    p = f = e = d = 0
    for _ in range(runs):
        po = random.random() < base_power; p += po
        ff = random.random() < base_flood; f += ff
        er = random.random() < (0.75 if ff else 0.20); e += er
        pd = random.random() < (0.65 if (po and ff) else 0.15); d += pd
    return {"power_outage": round(p/runs,4), "flash_flood": round(f/runs,4), "emergency_response": round(e/runs,4), "property_damage": round(d/runs,4)}

def simulate_haze(risk_modifier=0.0, runs=SIMULATION_RUNS):
    base_vis = clamp(0.70 + risk_modifier * 0.5)
    v = a = t = f = 0
    for _ in range(runs):
        vl = random.random() < base_vis; v += vl
        aq = random.random() < 0.65; a += aq
        st = random.random() < (0.55 if vl else 0.15); t += st
        fd = random.random() < (0.40 if (vl and aq) else 0.10); f += fd
    return {"visibility_loss": round(v/runs,4), "air_quality": round(a/runs,4), "slow_traffic": round(t/runs,4), "flight_delays": round(f/runs,4)}

def simulate_clear():
    # All values are RISK probabilities (very low under clear sky)
    return {
        "drain_risk":      round(0.01 + random.random()*0.02, 4),
        "road_disruption": round(0.02 + random.random()*0.03, 4),
        "traffic_delay":   round(0.06 + random.random()*0.07, 4),
        "service_impact":  round(0.01 + random.random()*0.02, 4),
    }

def _run_simulation(wtype, rain_level, risk_modifier=0.0):
    if wtype == "rain":          return simulate_rain(rain_level, risk_modifier)
    elif wtype == "thunderstorm": return simulate_thunderstorm(risk_modifier)
    elif wtype == "haze":        return simulate_haze(risk_modifier)
    else:                        return simulate_clear()

FALLBACK = {
    "Pune":      {"main":"Rain","description":"moderate rain","temp":27,"humidity":80,"wind_speed":3.2},
    "Mumbai":    {"main":"Rain","description":"heavy intensity rain","temp":29,"humidity":88,"wind_speed":5.1},
    "Delhi":     {"main":"Haze","description":"haze","temp":32,"humidity":55,"wind_speed":2.0},
    "Bengaluru": {"main":"Rain","description":"light intensity shower rain","temp":23,"humidity":72,"wind_speed":2.8},
    "Chennai":   {"main":"Thunderstorm","description":"thunderstorm with heavy rain","temp":31,"humidity":90,"wind_speed":6.0},
    "Hyderabad": {"main":"Rain","description":"moderate rain","temp":28,"humidity":75,"wind_speed":3.5},
    "Kolkata":   {"main":"Thunderstorm","description":"thunderstorm with rain","temp":30,"humidity":85,"wind_speed":4.8},
    "Ahmedabad": {"main":"Clear","description":"clear sky","temp":34,"humidity":40,"wind_speed":2.5},
    "Nagpur":    {"main":"Rain","description":"moderate rain","temp":29,"humidity":78,"wind_speed":3.0},
    "Surat":     {"main":"Rain","description":"heavy intensity rain","temp":30,"humidity":82,"wind_speed":4.2},
}

def _parse_weather(d):
    return {"main": d["weather"][0]["main"], "description": d["weather"][0]["description"],
            "temp": round(d["main"]["temp"],1), "feels_like": round(d["main"]["feels_like"],1),
            "humidity": d["main"]["humidity"], "wind_speed": d["wind"]["speed"],
            "icon": d["weather"][0]["icon"], "city": d["name"], "country": d["sys"]["country"]}

def fetch_weather_by_city(city):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city},IN&appid={OPENWEATHER_API_KEY}&units=metric"
        r = requests.get(url, timeout=6); r.raise_for_status()
        return _parse_weather(r.json()), None
    except Exception as e:
        return None, str(e)

def fetch_weather_by_coords(lat, lon):
    """Precise area-level weather using lat/lon coordinates."""
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        r = requests.get(url, timeout=6); r.raise_for_status()
        return _parse_weather(r.json()), None
    except Exception as e:
        return None, str(e)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/risk")
def risk():
    city = request.args.get("city", "Pune").strip()
    weather, err = fetch_weather_by_city(city)
    api_live = True
    if not weather:
        weather = FALLBACK.get(city, FALLBACK["Pune"]).copy()
        weather.update({"city": city, "country": "IN", "icon": "01d", "feels_like": weather["temp"]})
        api_live = False
    main = weather["main"]; description = weather.get("description","")
    rain_level = classify_rain(main, description); wtype = get_weather_type(main)
    probs = _run_simulation(wtype, rain_level)
    risks = {k: risk_label(v) for k,v in probs.items()}
    return jsonify({"city": city, "api_live": api_live,
        "weather": {"main": main,"description": description,"rain_level": rain_level,
            "temp": weather.get("temp"),"feels_like": weather.get("feels_like"),
            "humidity": weather.get("humidity"),"wind_speed": weather.get("wind_speed"),
            "icon": weather.get("icon","01d"),"country": weather.get("country","IN")},
        "weather_type": wtype,"probabilities": probs,"risk_levels": risks,
        "ai_alert": ai_alert(wtype,rain_level,probs),"simulation_runs": SIMULATION_RUNS})

@app.route("/risk/areas")
def risk_areas():
    """
    NEW: Per-area/locality risk breakdown for a city.
    Uses lat/lon API calls for each area + risk_modifier for local factors.
    """
    city = request.args.get("city", "Pune").strip()
    areas = CITY_AREAS.get(city, [])
    if not areas:
        return jsonify({"error": f"No area data for city: {city}"}), 404

    city_weather, _ = fetch_weather_by_city(city)
    if not city_weather:
        city_weather = FALLBACK.get(city, FALLBACK["Pune"]).copy()
        city_weather.update({"city": city, "country": "IN", "icon": "01d", "feels_like": city_weather["temp"]})

    results = []
    for area in areas:
        area_weather, err = fetch_weather_by_coords(area["lat"], area["lon"])
        api_live = True
        if not area_weather:
            area_weather = city_weather.copy()
            api_live = False

        main        = area_weather["main"]
        description = area_weather.get("description","")
        rain_level  = classify_rain(main, description)
        wtype       = get_weather_type(main)
        modifier    = area.get("risk_modifier", 0.0)

        probs = _run_simulation(wtype, rain_level, modifier)
        risks = {k: risk_label(v) for k,v in probs.items()}

        # Compute risk_score using only NEGATIVE outcome probabilities
        # (exclude inverted metrics like "roads_clear" that were previously in simulate_clear)
        # All simulators now return pure risk probabilities, so average is correct
        # But clamp to realistic range based on weather type
        raw_avg = sum(probs.values()) / len(probs)
        # For thunderstorm/heavy rain, probabilities are inherently high
        # For clear weather, they are inherently very low
        # Apply weather-type ceiling so clear never shows as critical
        WTYPE_MAX = {"clear": 0.18, "haze": 0.65, "rain": 1.0, "thunderstorm": 1.0}
        effective = min(raw_avg, WTYPE_MAX.get(wtype, 1.0))
        risk_score = round(effective * 100, 1)

        results.append({
            "area": area["name"], "lat": area["lat"], "lon": area["lon"],
            "tags": area.get("tags",[]), "risk_modifier": modifier, "api_live": api_live,
            "weather": {"main": main,"description": description,"rain_level": rain_level,
                "temp": area_weather.get("temp"),"humidity": area_weather.get("humidity"),
                "wind_speed": area_weather.get("wind_speed"),"icon": area_weather.get("icon","01d")},
            "weather_type": wtype,"probabilities": probs,"risk_levels": risks,
            "risk_score": risk_score,"ai_alert": ai_alert(wtype, rain_level, probs),
        })

    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return jsonify({
        "city": city, "areas": results,
        "summary": {
            "total_areas":     len(results),
            "critical_areas":  sum(1 for a in results if a["risk_score"] > 60),
            "high_risk_areas": sum(1 for a in results if 40 <= a["risk_score"] <= 60),
            "safe_areas":      sum(1 for a in results if a["risk_score"] < 20),
            "highest_risk":    results[0]["area"] if results else None,
            "safest_area":     results[-1]["area"] if results else None,
        }
    })

@app.route("/areas")
def list_areas():
    city = request.args.get("city","Pune").strip()
    areas = CITY_AREAS.get(city,[])
    return jsonify({"city": city, "areas": [{"name":a["name"],"lat":a["lat"],"lon":a["lon"],"tags":a.get("tags",[])} for a in areas]})

@app.route("/risk/all")
def risk_all():
    results = {}
    for city in FALLBACK.keys():
        weather, _ = fetch_weather_by_city(city)
        if not weather: weather = FALLBACK.get(city, FALLBACK["Pune"]).copy()
        main = weather["main"]; desc = weather.get("description","")
        rl = classify_rain(main,desc); wtype = get_weather_type(main)
        probs = _run_simulation(wtype, rl)
        results[city] = {"weather_type":wtype,"rain_level":rl,"temp":weather.get("temp"),
            "probabilities":probs,"risk_levels":{k:risk_label(v) for k,v in probs.items()},
            "ai_alert":ai_alert(wtype,rl,probs)}
    return jsonify(results)

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  CityPulse AI — Urban Risk Intelligence System")
    print("  Dashboard:  http://localhost:5000")
    print("  City Risk:  http://localhost:5000/risk?city=Pune")
    print("  Area Risk:  http://localhost:5000/risk/areas?city=Pune")
    print("  Area List:  http://localhost:5000/areas?city=Mumbai")
    print("="*55 + "\n")
    app.run(debug=True, port=5000)
