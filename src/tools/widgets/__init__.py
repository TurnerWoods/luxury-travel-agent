"""
Luxury Travel Agent - iOS Widget Tools
MCP-compatible tools for flight, hotel, and restaurant search widgets
"""

from .flight_widget import FlightWidget, FlightSearchParams, FlightDeal
from .hotel_widget import HotelWidget, HotelSearchParams, HotelResult
from .restaurant_widget import RestaurantWidget, RestaurantSearchParams, RestaurantResult

__all__ = [
    'FlightWidget',
    'FlightSearchParams',
    'FlightDeal',
    'HotelWidget',
    'HotelSearchParams',
    'HotelResult',
    'RestaurantWidget',
    'RestaurantSearchParams',
    'RestaurantResult'
]
