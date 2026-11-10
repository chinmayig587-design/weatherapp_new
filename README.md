# Weather App

A Flask weather app that looks up a city and displays current conditions and a
multi-day forecast.

## Run on Windows

Open PowerShell in this folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000> in your browser. Keep the PowerShell window open
while using the app.

The app gets weather and forecast data from Open-Meteo. An internet connection
is required.
