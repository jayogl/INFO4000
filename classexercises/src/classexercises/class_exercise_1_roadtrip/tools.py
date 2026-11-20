"""tools.py -- your road-trip tools. Plain Python: no MCP, no AI."""


def fuel_cost(
    distance_km: float,
    km_per_litre: float,
    price_per_litre: float,
) -> dict:
    """TODO: write the docstring the MODEL will read.

    Say what the tool does, when to use it, and each argument with units.
    """
    # TODO 1: bad input -> return {"error": "..."}
    #         (km_per_litre must be > 0; distance and price must be >= 0)
    # TODO 2: litres = distance / km_per_litre ; cost = litres * price
    # TODO 3: return {"litres": .., "cost": ..} rounded to 2 decimals
    raise NotImplementedError


def trip_time(
    distance_km: float,
    speed_kmh: float,
    break_min: float = 0.0,
) -> dict:
    """TODO: write the docstring the MODEL will read."""
    # TODO 1: bad input -> return {"error": "..."}
    #         (speed must be > 0; distance and break_min must be >= 0)
    # TODO 2: drive_h = distance / speed ; total_h = drive_h + break_min / 60
    # TODO 3: return {"drive_h": .., "total_h": ..} rounded to 2 decimals
    raise NotImplementedError
