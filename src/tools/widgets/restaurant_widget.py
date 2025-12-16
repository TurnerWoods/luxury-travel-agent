"""
Restaurant Widget Tool for Luxury Travel Agent
Searches restaurants via OpenTable-style API
Returns iOS widget-compatible restaurant data
"""

import os
import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CuisineType(str, Enum):
    FRENCH = "french"
    ITALIAN = "italian"
    JAPANESE = "japanese"
    AMERICAN = "american"
    MEDITERRANEAN = "mediterranean"
    SEAFOOD = "seafood"
    STEAKHOUSE = "steakhouse"
    ASIAN_FUSION = "asian_fusion"
    FINE_DINING = "fine_dining"
    ALL = "all"


class PriceRange(str, Enum):
    MODERATE = "$$"
    EXPENSIVE = "$$$"
    VERY_EXPENSIVE = "$$$$"


class AvailabilityStatus(str, Enum):
    AVAILABLE = "available"
    LIMITED = "limited"
    WAITLIST = "waitlist"
    SOLD_OUT = "sold_out"


@dataclass
class RestaurantSearchParams:
    """Parameters for restaurant search"""
    location: str  # City name
    date: str  # YYYY-MM-DD
    time: str  # HH:MM (24hr format)
    party_size: int = 2
    cuisine: CuisineType = CuisineType.ALL
    price_range: Optional[PriceRange] = None


@dataclass
class RestaurantResult:
    """Restaurant result for widget display"""
    id: str
    name: str
    cuisine: str
    cuisine_display: str
    location: str
    city: str
    neighborhood: str
    rating: float
    review_count: int
    price_range: str
    michelin_stars: int
    image_url: str
    thumbnail_url: str
    description: str
    highlights: List[str]
    available_times: List[str]
    availability_status: AvailabilityStatus
    next_available: Optional[str]
    source: str
    deep_link: str
    booking_url: Optional[str]
    coordinates: Optional[Dict[str, float]]

    def to_widget_format(self) -> Dict[str, Any]:
        """Convert to iOS widget JSON format"""
        return {
            "id": self.id,
            "name": self.name,
            "cuisine": self.cuisine,
            "cuisineDisplay": self.cuisine_display,
            "location": self.location,
            "city": self.city,
            "neighborhood": self.neighborhood,
            "rating": self.rating,
            "ratingDisplay": f"{self.rating:.1f}",
            "reviewCount": self.review_count,
            "reviewsDisplay": f"{self.review_count:,} reviews",
            "priceRange": self.price_range,
            "michelinStars": self.michelin_stars,
            "michelinDisplay": "⭐" * self.michelin_stars if self.michelin_stars > 0 else None,
            "imageUrl": self.image_url,
            "thumbnailUrl": self.thumbnail_url,
            "description": self.description,
            "highlights": self.highlights[:3],
            "highlightsDisplay": " · ".join(self.highlights[:2]),
            "availableTimes": self.available_times[:4],
            "availabilityStatus": self.availability_status.value,
            "nextAvailable": self.next_available,
            "source": self.source,
            "deepLink": self.deep_link,
            "bookingUrl": self.booking_url,
            "coordinates": self.coordinates,
            "action": "reserve_now"
        }


class RestaurantWidget:
    """
    Main Restaurant Widget Tool
    Searches restaurants and formats for iOS widgets
    """

    # Featured restaurant destinations
    FEATURED_CITIES = [
        {"city": "Paris", "country": "France"},
        {"city": "Tokyo", "country": "Japan"},
        {"city": "New York", "country": "USA"},
        {"city": "London", "country": "UK"},
        {"city": "Miami", "country": "USA"},
    ]

    # Restaurant images by cuisine
    CUISINE_IMAGES = {
        "french": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800",
        "italian": "https://images.unsplash.com/photo-1551183053-bf91a1d81141?w=800",
        "japanese": "https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=800",
        "american": "https://images.unsplash.com/photo-1544025162-d76694265947?w=800",
        "seafood": "https://images.unsplash.com/photo-1559339352-11d035aa65de?w=800",
        "steakhouse": "https://images.unsplash.com/photo-1600891964092-4316c288032e?w=800",
        "fine_dining": "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?w=800",
        "mediterranean": "https://images.unsplash.com/photo-1544124499-58912cbddaad?w=800",
        "default": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=800"
    }

    def __init__(self):
        self.opentable_key = os.getenv("OPENTABLE_API_KEY")

    async def search_restaurants(self, params: RestaurantSearchParams) -> List[RestaurantResult]:
        """
        Search for restaurants
        Returns sorted list of results
        """
        # For now, return curated mock data
        # Can be replaced with OpenTable API integration
        results = self._get_mock_restaurants(params)

        # Sort by rating then michelin stars
        results.sort(key=lambda r: (-r.michelin_stars, -r.rating))

        return results[:10]

    async def get_widget_data(self, location: Optional[str] = None, max_restaurants: int = 3) -> Dict[str, Any]:
        """
        Get formatted widget data for iOS
        Shows featured restaurants for a location
        """
        target_location = location or "Paris"
        date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        params = RestaurantSearchParams(
            location=target_location,
            date=date,
            time="19:00",
            party_size=2
        )

        restaurants = await self.search_restaurants(params)

        return {
            "widgetType": "restaurant_discovery",
            "size": "medium_2x2",
            "featuredRestaurant": restaurants[0].to_widget_format() if restaurants else None,
            "allRestaurants": [r.to_widget_format() for r in restaurants[:max_restaurants]],
            "searchLocation": target_location,
            "searchDate": date,
            "lastUpdated": datetime.now().isoformat(),
            "nextRefresh": (datetime.now() + timedelta(hours=1)).isoformat(),
            "refreshInterval": 3600,
            "deepLinkScheme": "opentable://"
        }

    def _get_mock_restaurants(self, params: RestaurantSearchParams) -> List[RestaurantResult]:
        """Generate mock restaurant data based on location"""

        mock_data = {
            "paris": [
                {
                    "name": "Le Cinq",
                    "cuisine": "french",
                    "cuisine_display": "French Fine Dining",
                    "neighborhood": "8th arrondissement",
                    "rating": 4.9,
                    "reviews": 2847,
                    "price": "$$$$",
                    "michelin": 3,
                    "description": "Three Michelin star restaurant at Four Seasons George V",
                    "highlights": ["Michelin 3-Star", "Tasting Menu", "Wine Pairing"]
                },
                {
                    "name": "L'Ambroisie",
                    "cuisine": "french",
                    "cuisine_display": "Classic French",
                    "neighborhood": "Place des Vosges",
                    "rating": 4.9,
                    "reviews": 1923,
                    "price": "$$$$",
                    "michelin": 3,
                    "description": "Legendary three-star in historic Place des Vosges",
                    "highlights": ["Michelin 3-Star", "Historic Setting", "Classic Cuisine"]
                },
                {
                    "name": "Septime",
                    "cuisine": "french",
                    "cuisine_display": "Modern French",
                    "neighborhood": "11th arrondissement",
                    "rating": 4.7,
                    "reviews": 3421,
                    "price": "$$$",
                    "michelin": 1,
                    "description": "Innovative tasting menus in a minimalist setting",
                    "highlights": ["Michelin 1-Star", "Seasonal Menu", "Natural Wine"]
                },
            ],
            "tokyo": [
                {
                    "name": "Sukiyabashi Jiro",
                    "cuisine": "japanese",
                    "cuisine_display": "Omakase Sushi",
                    "neighborhood": "Ginza",
                    "rating": 4.9,
                    "reviews": 1256,
                    "price": "$$$$",
                    "michelin": 3,
                    "description": "World-famous sushi by Jiro Ono",
                    "highlights": ["Michelin 3-Star", "Omakase Only", "Reservation Required"]
                },
                {
                    "name": "Narisawa",
                    "cuisine": "japanese",
                    "cuisine_display": "Innovative Japanese",
                    "neighborhood": "Minami-Aoyama",
                    "rating": 4.8,
                    "reviews": 2134,
                    "price": "$$$$",
                    "michelin": 2,
                    "description": "Avant-garde cuisine celebrating nature",
                    "highlights": ["Michelin 2-Star", "Sustainability", "World's 50 Best"]
                },
                {
                    "name": "Den",
                    "cuisine": "japanese",
                    "cuisine_display": "Creative Japanese",
                    "neighborhood": "Jingumae",
                    "rating": 4.8,
                    "reviews": 1876,
                    "price": "$$$",
                    "michelin": 2,
                    "description": "Playful fine dining with Japanese soul",
                    "highlights": ["Michelin 2-Star", "Inventive", "Asia's 50 Best"]
                },
            ],
            "new york": [
                {
                    "name": "Eleven Madison Park",
                    "cuisine": "american",
                    "cuisine_display": "Contemporary American",
                    "neighborhood": "Flatiron",
                    "rating": 4.8,
                    "reviews": 4521,
                    "price": "$$$$",
                    "michelin": 3,
                    "description": "Plant-based tasting menu in Art Deco landmark",
                    "highlights": ["Michelin 3-Star", "Plant-Based", "World's Best"]
                },
                {
                    "name": "Le Bernardin",
                    "cuisine": "seafood",
                    "cuisine_display": "French Seafood",
                    "neighborhood": "Midtown",
                    "rating": 4.9,
                    "reviews": 5234,
                    "price": "$$$$",
                    "michelin": 3,
                    "description": "Eric Ripert's legendary seafood temple",
                    "highlights": ["Michelin 3-Star", "Seafood", "40 Years"]
                },
                {
                    "name": "Carbone",
                    "cuisine": "italian",
                    "cuisine_display": "Italian-American",
                    "neighborhood": "Greenwich Village",
                    "rating": 4.6,
                    "reviews": 6789,
                    "price": "$$$",
                    "michelin": 0,
                    "description": "Classic Italian-American in retro glamour",
                    "highlights": ["Celebrity Favorite", "Spicy Rigatoni", "Tableside Service"]
                },
            ],
            "miami": [
                {
                    "name": "Fiola Miami",
                    "cuisine": "italian",
                    "cuisine_display": "Modern Italian",
                    "neighborhood": "Coral Gables",
                    "rating": 4.7,
                    "reviews": 1823,
                    "price": "$$$$",
                    "michelin": 0,
                    "description": "Fabio Trabocchi's Italian excellence",
                    "highlights": ["James Beard Award", "Pasta", "Wine List"]
                },
                {
                    "name": "Ariete",
                    "cuisine": "american",
                    "cuisine_display": "New American",
                    "neighborhood": "Coconut Grove",
                    "rating": 4.6,
                    "reviews": 2134,
                    "price": "$$$",
                    "michelin": 0,
                    "description": "Farm-to-table with Latin influences",
                    "highlights": ["Local Sourcing", "Cocktails", "Brunch"]
                },
                {
                    "name": "Stubborn Seed",
                    "cuisine": "american",
                    "cuisine_display": "Creative American",
                    "neighborhood": "South Beach",
                    "rating": 4.7,
                    "reviews": 1567,
                    "price": "$$$$",
                    "michelin": 0,
                    "description": "Top Chef winner Jeremy Ford's flagship",
                    "highlights": ["Top Chef Winner", "Tasting Menu", "South Beach"]
                },
            ],
            "london": [
                {
                    "name": "Restaurant Gordon Ramsay",
                    "cuisine": "french",
                    "cuisine_display": "French Fine Dining",
                    "neighborhood": "Chelsea",
                    "rating": 4.8,
                    "reviews": 2345,
                    "price": "$$$$",
                    "michelin": 3,
                    "description": "Gordon Ramsay's flagship three-star",
                    "highlights": ["Michelin 3-Star", "Classic French", "Intimate"]
                },
                {
                    "name": "The Ledbury",
                    "cuisine": "french",
                    "cuisine_display": "Modern European",
                    "neighborhood": "Notting Hill",
                    "rating": 4.8,
                    "reviews": 1987,
                    "price": "$$$$",
                    "michelin": 2,
                    "description": "Brett Graham's innovative cuisine",
                    "highlights": ["Michelin 2-Star", "Game Dishes", "Tasting Menu"]
                },
                {
                    "name": "Dishoom",
                    "cuisine": "indian",
                    "cuisine_display": "Bombay Cafe",
                    "neighborhood": "Covent Garden",
                    "rating": 4.6,
                    "reviews": 8765,
                    "price": "$$",
                    "michelin": 0,
                    "description": "Beloved Bombay-style cafe and bar",
                    "highlights": ["Iconic Breakfast", "Black Daal", "No Reservations"]
                },
            ],
        }

        location_lower = params.location.lower()
        restaurants_data = mock_data.get(location_lower, mock_data["paris"])

        # Generate available times
        base_times = ["18:00", "18:30", "19:00", "19:30", "20:00", "20:30", "21:00"]

        results = []
        for idx, data in enumerate(restaurants_data):
            cuisine = data["cuisine"]
            image = self.CUISINE_IMAGES.get(cuisine, self.CUISINE_IMAGES["default"])

            # Simulate availability
            import random
            available_times = random.sample(base_times, min(4, len(base_times)))
            available_times.sort()

            results.append(RestaurantResult(
                id=f"opentable_{location_lower}_{idx}",
                name=data["name"],
                cuisine=cuisine,
                cuisine_display=data["cuisine_display"],
                location=f"{data['neighborhood']}, {params.location.title()}",
                city=params.location.title(),
                neighborhood=data["neighborhood"],
                rating=data["rating"],
                review_count=data["reviews"],
                price_range=data["price"],
                michelin_stars=data["michelin"],
                image_url=image,
                thumbnail_url=image.replace("w=800", "w=200"),
                description=data["description"],
                highlights=data["highlights"],
                available_times=available_times,
                availability_status=AvailabilityStatus.AVAILABLE if available_times else AvailabilityStatus.LIMITED,
                next_available=available_times[0] if available_times else None,
                source="opentable",
                deep_link=f"opentable://reserve?restaurant={data['name'].lower().replace(' ', '-')}",
                booking_url=f"https://opentable.com/r/{data['name'].lower().replace(' ', '-')}",
                coordinates=None
            ))

        return results


# MCP Tool Registration
async def search_restaurants_tool(
    location: str,
    date: str,
    time: str = "19:00",
    party_size: int = 2,
    cuisine: str = "all"
) -> Dict[str, Any]:
    """
    MCP Tool: Search for restaurants

    Args:
        location: City name (e.g., Paris, Tokyo, Miami)
        date: Reservation date (YYYY-MM-DD)
        time: Preferred time (HH:MM, 24hr format)
        party_size: Number of guests
        cuisine: Cuisine type - french, italian, japanese, american, seafood, steakhouse, all

    Returns:
        List of restaurant results formatted for display
    """
    widget = RestaurantWidget()
    params = RestaurantSearchParams(
        location=location,
        date=date,
        time=time,
        party_size=party_size,
        cuisine=CuisineType(cuisine.lower()) if cuisine.lower() != "all" else CuisineType.ALL
    )

    restaurants = await widget.search_restaurants(params)

    return {
        "success": True,
        "count": len(restaurants),
        "restaurants": [r.to_widget_format() for r in restaurants]
    }


async def get_restaurant_widget_data_tool(
    location: Optional[str] = None,
    max_restaurants: int = 3
) -> Dict[str, Any]:
    """
    MCP Tool: Get restaurant widget data for iOS

    Args:
        location: City to search (default: Paris)
        max_restaurants: Maximum number of restaurants to include

    Returns:
        Formatted widget data ready for iOS display
    """
    widget = RestaurantWidget()
    return await widget.get_widget_data(location, max_restaurants)
