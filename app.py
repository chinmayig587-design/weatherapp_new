from flask import Flask, render_template, request
import requests
import urllib.parse

app = Flask(__name__)

def get_weather(city_name):
    # Geocode the city name
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city_name)}&count=1&language=en&format=json"
    try:
        geo_resp = requests.get(geo_url, timeout=5).json()
        if 'results' not in geo_resp or len(geo_resp['results']) == 0:
            return None
        
        lat = geo_resp['results'][0]['latitude']
        lon = geo_resp['results'][0]['longitude']
        country = geo_resp['results'][0].get('country', '')
        name = geo_resp['results'][0]['name']
        
        # Get Weather data
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m,surface_pressure,visibility&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=auto"
        weather_resp = requests.get(weather_url, timeout=5).json()
        
        # Weather Codes mapping (WMO code)
        code = weather_resp['current']['weather_code']
        description = get_weather_description(code)
        
        daily_data = []
        if 'daily' in weather_resp:
            daily_times = weather_resp['daily'].get('time', [])
            daily_maxs = weather_resp['daily'].get('temperature_2m_max', [])
            daily_mins = weather_resp['daily'].get('temperature_2m_min', [])
            daily_codes = weather_resp['daily'].get('weather_code', [])
            for i in range(1, min(6, len(daily_times))): # Skip today (index 0) for forecast
                daily_data.append({
                    'date': daily_times[i],
                    'max': daily_maxs[i],
                    'min': daily_mins[i],
                    'code': daily_codes[i],
                    'description': get_weather_description(daily_codes[i])
                })

        return {
            'name': name,
            'country': country,
            'temp': weather_resp['current']['temperature_2m'],
            'feels_like': weather_resp['current']['apparent_temperature'],
            'humidity': weather_resp['current']['relative_humidity_2m'],
            'wind_speed': weather_resp['current']['wind_speed_10m'],
            'pressure': weather_resp['current'].get('surface_pressure', 0),
            'visibility': round(weather_resp['current'].get('visibility', 0) / 1000, 1),
            'description': description,
            'is_day': weather_resp['current']['is_day'],
            'forecast': daily_data
        }
    except Exception as e:
        print("Error fetching weather:", e)
        return None

def get_weather_description(code):
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow fall",
        73: "Moderate snow fall",
        75: "Heavy snow fall",
        95: "Thunderstorm"
    }
    return weather_codes.get(code, "Unknown weather")

def get_city_image(city_name):
    # Teleport API (Urban areas images) - Often provides great quality images
    teleport_url = f"https://api.teleport.org/api/urban_areas/slug:{city_name.lower().replace(' ', '-')}/images/"
    try:
        resp = requests.get(teleport_url, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            return data['photos'][0]['image']['web']
    except Exception:
        pass

    # Fallback to Wikipedia API
    wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&format=json&piprop=original&titles={urllib.parse.quote(city_name)}"
    try:
        resp = requests.get(wiki_url, timeout=3).json()
        pages = resp.get('query', {}).get('pages', {})
        for page_id, page_data in pages.items():
            if 'original' in page_data and 'source' in page_data['original']:
                source = page_data['original']['source']
                if not source.endswith('.svg') and 'map' not in source.lower():
                    return source
    except Exception:
        pass
    
    # Ultimate fallback to a nice generic landscape
    return "https://images.unsplash.com/photo-1504608524841-42fe6f032b4b?auto=format&fit=crop&w=1600&q=80"

@app.route('/', methods=['GET', 'POST'])
def index():
    weather_data = None
    bg_image = "https://images.unsplash.com/photo-1504608524841-42fe6f032b4b?auto=format&fit=crop&w=1600&q=80"
    error = None
    
    if request.method == 'POST':
        city = request.form.get('city')
        if city:
            weather_data = get_weather(city)
            if weather_data:
                bg_image = get_city_image(weather_data['name'])
            else:
                error = "City not found or weather data unavailable."
    
    return render_template('index.html', weather=weather_data, bg_image=bg_image, error=error)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
