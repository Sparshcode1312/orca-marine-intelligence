from math import asin, cos, radians, sin, sqrt

from app.schemas.trip import GeoPoint


def calculate_distance_km(
    start: GeoPoint,
    end: GeoPoint,
) -> float:
    """
    Calculate great-circle distance using the Haversine formula.
    """

    earth_radius_km = 6371.0

    start_latitude = radians(start.latitude)
    end_latitude = radians(end.latitude)

    latitude_difference = radians(
        end.latitude - start.latitude
    )

    longitude_difference = radians(
        end.longitude - start.longitude
    )

    haversine_value = (
        sin(latitude_difference / 2) ** 2
        + cos(start_latitude)
        * cos(end_latitude)
        * sin(longitude_difference / 2) ** 2
    )

    angular_distance = 2 * asin(
        sqrt(haversine_value)
    )

    return round(
        earth_radius_km * angular_distance,
        2,
    )