"""tools.py -- your road-trip tools. Plain Python: no MCP, no AI."""

def fuel_cost(
    distance_km: float,
    km_per_litre: float,
    price_per_litre: float,
) -> dict:
    """Calculate fuel volume and total trip cost based on distance, efficiency, and price. Use when estimating trip fuel expenditure.
    Args:
      distance_km: Total drive distance in kilometers (>= 0).
      km_per_litre: Vehicle fuel efficiency in km per litre (> 0).
      price_per_litre: Fuel price per litre in local currency (>= 0).
    Returns:
      dict with 'litres' and 'cost', or 'error' if input is invalid."""
    # TODO 1: bad input -> return {"error": "..."}
    #         (km_per_litre must be > 0; distance and price must be >= 0)
    if km_per_litre <= 0:
        return {"error": "km_per_litre must be greater than 0"}
    if distance_km < 0 or price_per_litre < 0:
        return {"error": "distance_km and price_per_litre must be >= 0"}
    # TODO 2: litres = distance / km_per_litre ; cost = litres * price
    litres = distance_km / km_per_litre
    cost = litres * price_per_litre
    # TODO 3: return {"litres": .., "cost": ..} rounded to 2 decimals
    return {"litres": round(litres, 2), "cost": round(cost, 2)}

def trip_time(
    distance_km: float,
    speed_kmh: float,
    break_min: float = 0.0,
) -> dict:
    """Calculate drive duration and total travel time including break duration. Use when planning travel schedules and arrival times.
    Args:
      distance_km: Travel distance in kilometers (>= 0).
      speed_kmh: Average driving speed in km/h (> 0).
      break_min: Total break time in minutes (default 0.0, >= 0).
    Returns:
      dict with 'drive_h' and 'total_h', or 'error' if input is invalid."""
    # TODO 1: bad input -> return {"error": "..."}
    #         (speed must be > 0; distance and break_min must be >= 0)
    if speed_kmh <= 0:
        return {"error": "speed_kmh must be greater than 0"}
    if distance_km < 0 or break_min < 0:
        return {"error": "distance_km and break_min must be >= 0"}
    # TODO 2: drive_h = distance / speed ; total_h = drive_h + break_min / 60
    drive_h = distance_km / speed_kmh
    total_h = drive_h + (break_min / 60.0)
    # TODO 3: return {"drive_h": .., "total_h": ..} rounded to 2 decimals
    return {"drive_h": round(drive_h, 2), "total_h": round(total_h, 2)}