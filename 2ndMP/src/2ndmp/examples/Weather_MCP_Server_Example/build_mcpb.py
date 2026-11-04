import zipfile
from pathlib import Path

# Replace with the path from `which python`
VENV_PYTHON = "/Users/raoj/.venv/bin/python3"

SERVER_CODE = """import httpx2
from mcp.server.mcpserver import MCPServer

app = MCPServer("Open-Meteo Weather Server")
BASE_URL = "https://api.open-meteo.com/v1/forecast"

@app.tool()
async def get_current_weather(latitude: float, longitude: float) -> str:
    \"\"\"Get the absolute live, current weather for a specific latitude and longitude.\"\"\"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,weather_code",
        "temperature_unit": "fahrenheit",
    }
    try:
        async with httpx2.AsyncClient(timeout=10.0) as client:
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        return f"Failed to retrieve current weather: {e}"

    curr = data.get("current") or {}
    if not curr:
        return "Current weather conditions unavailable for this location."

    temp = curr.get("temperature_2m", "N/A")
    humidity = curr.get("relative_humidity_2m", "N/A")
    code = curr.get("weather_code", "N/A")

    return (
        f"Current Conditions:\\n"
        f"Temperature: {temp}°F\\n"
        f"Humidity: {humidity}%\\n"
        f"WMO Weather Code: {code}"
    )

@app.tool()
async def get_tomorrow_weather(latitude: float, longitude: float) -> str:
    \"\"\"Get tomorrow's weather forecast including max/min temperatures.\"\"\"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "temperature_unit": "fahrenheit",
        "forecast_days": 2,
        "timezone": "auto"
    }
    try:
        async with httpx2.AsyncClient(timeout=10.0) as client:
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        return f"Failed to retrieve tomorrow's forecast: {e}"

    daily = data.get("daily") or {}
    temps_max = daily.get("temperature_2m_max") or []
    temps_min = daily.get("temperature_2m_min") or []
    precip_prob = daily.get("precipitation_probability_max") or []

    if len(temps_max) < 2 or len(temps_min) < 2:
        return "Weather data unavailable for tomorrow."

    return (
        f"Tomorrow's Forecast:\\n"
        f"High: {temps_max[1]}°F\\n"
        f"Low: {temps_min[1]}°F\\n"
        f"Max Rain/Snow Probability: {precip_prob[1] if len(precip_prob) > 1 else 'N/A'}%"
    )

@app.tool()
async def get_weekly_weather(latitude: float, longitude: float) -> str:
    \"\"\"Get a summary of the 7-day weather forecast.\"\"\"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min",
        "temperature_unit": "fahrenheit",
        "timezone": "auto"
    }
    try:
        async with httpx2.AsyncClient(timeout=10.0) as client:
            response = await client.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        return f"Failed to retrieve weekly forecast: {e}"

    daily = data.get("daily") or {}
    dates = daily.get("time") or []
    max_temps = daily.get("temperature_2m_max") or []
    min_temps = daily.get("temperature_2m_min") or []

    if not dates:
        return "7-day weather outlook unavailable."

    summary = "7-Day Weather Outlook:\\n"
    for i in range(min(len(dates), len(max_temps), len(min_temps))):
        summary += f"- {dates[i]}: High {max_temps[i]}°F / Low {min_temps[i]}°F\\n"

    return summary

if __name__ == "__main__":
    app.run()
"""

# Manifest adhering to the exact enum 'python'
MANIFEST_JSON = f"""{{
  "manifest_version": "0.3",
  "name": "weather-server",
  "version": "1.0.0",
  "display_name": "Open-Meteo Weather Server",
  "description": "Fetches current weather and forecasts via Open-Meteo.",
  "author": {{
    "name": "Developer"
  }},
  "server": {{
    "type": "python",
    "entry_point": "server/main.py",
    "mcp_config": {{
      "command": "{VENV_PYTHON}",
      "args": ["${{__dirname}}/server/main.py"]
    }}
  }}
}}
"""

mcpb_path = Path("weather-server.mcpb")
with zipfile.ZipFile(mcpb_path, "w", zipfile.ZIP_DEFLATED) as archive:
  archive.writestr("manifest.json", MANIFEST_JSON)
  archive.writestr("server/main.py", SERVER_CODE)

print(f"Built valid bundle: {mcpb_path.resolve()}")