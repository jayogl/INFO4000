import httpx2  # MCP 2.x now uses httpx2 internally under the hood
from mcp.server.mcpserver import MCPServer


# Initialize FastMCP server
app = MCPServer("Open-Meteo Weather Server")

BASE_URL = "https://api.open-meteo.com/v1/forecast"

@app.tool()
async def get_current_weather(latitude: float, longitude: float) -> str:
    """Get the absolute live, current weather for a specific latitude and longitude."""
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
            data = response.json()  # Single call, returns dict
    except Exception as e:
        return f"Failed to retrieve current weather: {e}"

    # Safely extract the 'current' dictionary block
    curr = data.get("current") or {}
    if not curr:
        return "Current weather conditions unavailable for this location."

    temp = curr.get("temperature_2m", "N/A")
    humidity = curr.get("relative_humidity_2m", "N/A")
    code = curr.get("weather_code", "N/A")

    return (
        f"Current Conditions:\n"
        f"Temperature: {temp}°F\n"
        f"Humidity: {humidity}%\n"
        f"WMO Weather Code: {code}"
    )

@app.tool()
async def get_tomorrow_weather(latitude: float, longitude: float) -> str:
    """
    Get tomorrow's weather forecast including max/min temperatures.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "temperature_unit": "fahrenheit",
        "forecast_days": 2 # Pulling today & tomorrow
    }
    
    async with httpx2.AsyncClient() as client:
        response = await client.get(BASE_URL, params=params)
        data = response.json()
        
    daily = data.get("daily", {})
    # Index 1 corresponds to tomorrow
    return (
        f"Tomorrow's Forecast:\n"
        f"High: {daily.get('temperature_2m_max')[1]}°F\n"
        f"Low: {daily.get('temperature_2m_min')[1]}°F\n"
        f"Max Rain/Snow Probability: {daily.get('precipitation_probability_max')[1]}%"
    )

@app.tool()
async def get_weekly_weather(latitude: float, longitude: float) -> str:
    """
    Get a summary of the 7-day weather forecast.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min",
        "temperature_unit": "fahrenheit"
    }
    
    async with httpx2.AsyncClient() as client:
        response = await client.get(BASE_URL, params=params)
        data = response.json()
        
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    
    summary = "7-Day Weather Outlook:\n"
    for i in range(len(dates)):
        summary += f"- {dates[i]}: High {max_temps[i]}°F / Low {min_temps[i]}°F\n"
        
    return summary

if __name__ == "__main__":
    # FastMCP defaults to running over stdio for local AI clients
    app.run()
