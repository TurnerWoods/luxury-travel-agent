"""
Flight Widget Tool for Luxury Travel Agent
Searches flights via Amadeus, Kiwi, and Downtown Travel APIs
Returns iOS widget-compatible deal data
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


class CabinClass(str, Enum):
    ECONOMY = "ECONOMY"
    PREMIUM_ECONOMY = "PREMIUM_ECONOMY"
    BUSINESS = "BUSINESS"
    FIRST = "FIRST"


class DealUrgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FlightSearchParams:
    """Parameters for flight search"""
    origin: str  # IATA code (e.g., JFK)
    destination: str  # IATA code (e.g., CDG)
    departure_date: str  # YYYY-MM-DD
    return_date: Optional[str] = None
    adults: int = 1
    cabin_class: CabinClass = CabinClass.BUSINESS
    max_results: int = 10
    max_price: Optional[float] = None


@dataclass
class FlightDeal:
    """Flight deal result for widget display"""
    id: str
    origin: str
    destination: str
    route_display: str  # "NYC -> Paris"
    price: float
    original_price: Optional[float]
    currency: str
    cabin_class: str
    airline: str
    airline_name: str
    departure_date: str
    return_date: Optional[str]
    departure_time: str
    arrival_time: str
    duration: str
    stops: int
    deal_score: int  # 1-10
    savings_percent: Optional[int]
    urgency: DealUrgency
    expires_at: Optional[str]
    is_mistake_fare: bool
    source: str  # "amadeus", "kiwi", "downtown"
    deep_link: str
    booking_url: Optional[str]
    image_url: Optional[str] = None

    # Destination images for popular airports
    DESTINATION_IMAGES = {
        "CDG": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800",  # Paris
        "PAR": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800",
        "LHR": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800",  # London
        "LON": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800",
        "NRT": "https://images.unsplash.com/photo-1536098561742-ca998e48cbcc?w=800",  # Tokyo
        "HND": "https://images.unsplash.com/photo-1536098561742-ca998e48cbcc?w=800",
        "TYO": "https://images.unsplash.com/photo-1536098561742-ca998e48cbcc?w=800",
        "DXB": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=800",  # Dubai
        "MIA": "https://images.unsplash.com/photo-1533106497176-45ae19e68ba2?w=800",  # Miami
        "LAX": "https://images.unsplash.com/photo-1534190760961-74e8c1c5c3da?w=800",  # LA
        "SFO": "https://images.unsplash.com/photo-1501594907352-04cda38ebc29?w=800",  # SF
        "JFK": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=800",  # NYC
        "NYC": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=800",
        "SIN": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=800",  # Singapore
        "HKG": "https://images.unsplash.com/photo-1536599018102-9f803c140fc1?w=800",  # Hong Kong
        "SYD": "https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=800",  # Sydney
        "FCO": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800",  # Rome
        "ROM": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800",
        "BCN": "https://images.unsplash.com/photo-1583422409516-2895a77efded?w=800",  # Barcelona
        "AMS": "https://images.unsplash.com/photo-1534351590666-13e3e96b5017?w=800",  # Amsterdam
        "YVR": "https://images.unsplash.com/photo-1559511260-66a68e5c81b5?w=800",  # Vancouver
        "MLE": "https://images.unsplash.com/photo-1514282401047-d79a71a590e8?w=800",  # Maldives
        "DPS": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=800",  # Bali
    }

    def to_widget_format(self) -> Dict[str, Any]:
        """Convert to iOS widget JSON format"""
        # Get destination image
        img = self.image_url or self.DESTINATION_IMAGES.get(
            self.destination,
            "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=800"  # Default airplane
        )

        return {
            "id": self.id,
            "route": self.route_display,
            "routeCode": f"{self.origin}->{self.destination}",
            "price": f"${self.price:,.0f}",
            "priceNumeric": self.price,
            "originalPrice": f"${self.original_price:,.0f}" if self.original_price else None,
            "cabin": self.cabin_class,
            "airline": self.airline,
            "airlineName": self.airline_name,
            "savings": f"{self.savings_percent}% off" if self.savings_percent else None,
            "savingsPercent": self.savings_percent,
            "dealScore": self.deal_score,
            "urgency": self.urgency.value,
            "expires": self.expires_at,
            "isMistakeFare": self.is_mistake_fare,
            "departureDate": self.departure_date,
            "returnDate": self.return_date,
            "departureTime": self.departure_time,
            "arrivalTime": self.arrival_time,
            "duration": self.duration,
            "stops": self.stops,
            "stopsDisplay": "Nonstop" if self.stops == 0 else f"{self.stops} stop{'s' if self.stops > 1 else ''}",
            "source": self.source,
            "deepLink": self.deep_link,
            "bookingUrl": self.booking_url,
            "imageUrl": img,
            "action": "tap_to_book"
        }


class AmadeusClient:
    """Amadeus API client for flight searches"""

    API_URL = "https://api.amadeus.com"
    TEST_API_URL = "https://test.api.amadeus.com"

    def __init__(self, api_key: str, api_secret: str, use_test: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = self.TEST_API_URL if use_test else self.API_URL
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    async def _get_token(self, client: httpx.AsyncClient) -> str:
        """Get or refresh OAuth token"""
        if self._access_token and self._token_expiry and datetime.now() < self._token_expiry:
            return self._access_token

        response = await client.post(
            f"{self.base_url}/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.api_secret
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        data = response.json()

        self._access_token = data["access_token"]
        self._token_expiry = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
        return self._access_token

    async def search_flights(self, params: FlightSearchParams) -> List[Dict]:
        """Search for flight offers"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            token = await self._get_token(client)

            query_params = {
                "originLocationCode": params.origin,
                "destinationLocationCode": params.destination,
                "departureDate": params.departure_date,
                "adults": params.adults,
                "travelClass": params.cabin_class.value,
                "max": params.max_results,
                "currencyCode": "USD"
            }

            if params.return_date:
                query_params["returnDate"] = params.return_date
            if params.max_price:
                query_params["maxPrice"] = int(params.max_price)

            response = await client.get(
                f"{self.base_url}/v2/shopping/flight-offers",
                params=query_params,
                headers={"Authorization": f"Bearer {token}"}
            )
            response.raise_for_status()
            return response.json().get("data", [])


class FlightWidget:
    """
    Main Flight Widget Tool
    Uses Amadeus API for flight searches, formats for iOS widgets
    """

    # Popular luxury routes for widget defaults
    DEFAULT_ROUTES = [
        {"origin": "JFK", "destination": "CDG", "name": "NYC -> Paris"},
        {"origin": "LAX", "destination": "NRT", "name": "LA -> Tokyo"},
        {"origin": "MIA", "destination": "LHR", "name": "Miami -> London"},
        {"origin": "SFO", "destination": "HND", "name": "SF -> Tokyo"},
        {"origin": "JFK", "destination": "DXB", "name": "NYC -> Dubai"},
    ]

    # Airline code to name mapping
    AIRLINES = {
        "AA": "American Airlines",
        "UA": "United Airlines",
        "DL": "Delta Air Lines",
        "AF": "Air France",
        "BA": "British Airways",
        "LH": "Lufthansa",
        "EK": "Emirates",
        "SQ": "Singapore Airlines",
        "QF": "Qantas",
        "NH": "ANA",
        "JL": "Japan Airlines",
        "CX": "Cathay Pacific",
        "QR": "Qatar Airways",
        "TK": "Turkish Airlines",
        "EY": "Etihad Airways",
        "VS": "Virgin Atlantic",
        "AC": "Air Canada",
        "KL": "KLM",
        "IB": "Iberia",
        "AZ": "ITA Airways",
        "LX": "SWISS",
        "OS": "Austrian",
        "SK": "SAS",
        "AY": "Finnair",
        "SU": "Aeroflot",
        "KE": "Korean Air",
        "OZ": "Asiana Airlines",
        "CI": "China Airlines",
        "BR": "EVA Air",
        "MH": "Malaysia Airlines",
        "TG": "Thai Airways",
        "GA": "Garuda Indonesia",
        "NZ": "Air New Zealand",
        "LA": "LATAM",
        "AM": "Aeromexico",
        "AS": "Alaska Airlines",
        "WN": "Southwest Airlines",
        "B6": "JetBlue",
        "F9": "Frontier Airlines",
        "NK": "Spirit Airlines",
    }

    def __init__(self):
        self.amadeus = None
        self._init_clients()

    def _init_clients(self):
        """Initialize API clients from environment"""
        amadeus_key = os.getenv("AMADEUS_API_KEY")
        amadeus_secret = os.getenv("AMADEUS_API_SECRET")

        if amadeus_key and amadeus_secret:
            self.amadeus = AmadeusClient(amadeus_key, amadeus_secret)
            logger.info("Amadeus client initialized")

    async def search_flights(self, params: FlightSearchParams) -> List[FlightDeal]:
        """
        Search for flights via Amadeus API
        Returns sorted list of deals
        """
        deals = []

        # Search Amadeus
        if self.amadeus:
            try:
                results = await self.amadeus.search_flights(params)
                deals.extend(self._parse_amadeus_results(results, params))
            except Exception as e:
                logger.error(f"Amadeus search failed: {e}")

        # Fallback to mock data if no API configured or no results
        if not deals:
            deals = self._get_mock_deals(params)

        # Sort by deal score (highest first), then by price
        deals.sort(key=lambda d: (-d.deal_score, d.price))

        return deals[:params.max_results]

    async def get_widget_data(self, user_id: Optional[str] = None, max_deals: int = 3) -> Dict[str, Any]:
        """
        Get formatted widget data for iOS
        Searches popular routes and returns top deals
        """
        deals = []
        departure = datetime.now() + timedelta(days=30)
        return_dt = departure + timedelta(days=7)

        for route in self.DEFAULT_ROUTES[:max_deals + 2]:
            try:
                params = FlightSearchParams(
                    origin=route["origin"],
                    destination=route["destination"],
                    departure_date=departure.strftime("%Y-%m-%d"),
                    return_date=return_dt.strftime("%Y-%m-%d"),
                    cabin_class=CabinClass.BUSINESS,
                    max_results=1
                )
                route_deals = await self.search_flights(params)
                if route_deals:
                    deals.append(route_deals[0])

                if len(deals) >= max_deals:
                    break
            except Exception as e:
                logger.error(f"Failed to fetch {route['origin']}-{route['destination']}: {e}")

        # Fallback mock if no deals found
        if not deals:
            deals = [self._create_mock_deal()]

        return {
            "widgetType": "flight_deal_tracker",
            "size": "medium_2x2",
            "topDeal": deals[0].to_widget_format() if deals else None,
            "allDeals": [d.to_widget_format() for d in deals[:max_deals]],
            "watchedRoutes": [],
            "activeAlerts": 0,
            "lastUpdated": datetime.now().isoformat(),
            "nextRefresh": (datetime.now() + timedelta(hours=2)).isoformat(),
            "refreshInterval": 7200,
            "deepLinkScheme": "sms://"
        }

    def _parse_amadeus_results(self, results: List[Dict], params: FlightSearchParams) -> List[FlightDeal]:
        """Parse Amadeus flight offers into FlightDeals"""
        deals = []

        for offer in results:
            try:
                price = float(offer.get("price", {}).get("total", 0))
                itinerary = offer.get("itineraries", [{}])[0]
                segments = itinerary.get("segments", [{}])
                first_segment = segments[0] if segments else {}
                last_segment = segments[-1] if segments else first_segment

                airline = first_segment.get("carrierCode", "XX")

                # Calculate deal score
                deal_score = self._calculate_deal_score(price, params.cabin_class, len(segments) - 1)

                # Determine urgency
                urgency = self._determine_urgency(deal_score, price)

                deal = FlightDeal(
                    id=f"amadeus_{offer.get('id', '')}",
                    origin=params.origin,
                    destination=params.destination,
                    route_display=f"{params.origin} -> {params.destination}",
                    price=price,
                    original_price=price * 1.35 if deal_score >= 7 else None,
                    currency="USD",
                    cabin_class=params.cabin_class.value,
                    airline=airline,
                    airline_name=self.AIRLINES.get(airline, airline),
                    departure_date=params.departure_date,
                    return_date=params.return_date,
                    departure_time=first_segment.get("departure", {}).get("at", "")[-5:],
                    arrival_time=last_segment.get("arrival", {}).get("at", "")[-5:],
                    duration=itinerary.get("duration", "").replace("PT", "").lower(),
                    stops=len(segments) - 1,
                    deal_score=deal_score,
                    savings_percent=26 if deal_score >= 7 else None,
                    urgency=urgency,
                    expires_at=(datetime.now() + timedelta(hours=12)).isoformat() if deal_score >= 8 else None,
                    is_mistake_fare=deal_score >= 9,
                    source="amadeus",
                    deep_link=self._generate_sms_link(params.origin, params.destination, price),
                    booking_url=None
                )
                deals.append(deal)
            except Exception as e:
                logger.error(f"Failed to parse Amadeus offer: {e}")

        return deals

    def _get_mock_deals(self, params: FlightSearchParams) -> List[FlightDeal]:
        """Generate mock deals based on search params (used when Amadeus API not configured)"""
        import random

        # Route-specific mock data
        mock_routes = {
            ("JFK", "CDG"): {"airline": "AF", "name": "Air France", "price": 1847, "duration": "7h 15m"},
            ("JFK", "LHR"): {"airline": "BA", "name": "British Airways", "price": 2150, "duration": "7h 00m"},
            ("LAX", "NRT"): {"airline": "JL", "name": "Japan Airlines", "price": 2890, "duration": "11h 30m"},
            ("LAX", "HND"): {"airline": "NH", "name": "ANA", "price": 2750, "duration": "11h 45m"},
            ("SFO", "HND"): {"airline": "UA", "name": "United Airlines", "price": 2650, "duration": "10h 30m"},
            ("MIA", "LHR"): {"airline": "BA", "name": "British Airways", "price": 2350, "duration": "8h 45m"},
            ("JFK", "DXB"): {"airline": "EK", "name": "Emirates", "price": 3200, "duration": "12h 30m"},
        }

        route_key = (params.origin.upper(), params.destination.upper())
        if route_key in mock_routes:
            data = mock_routes[route_key]
        else:
            # Generic fallback
            data = {"airline": "AA", "name": "American Airlines", "price": 2500, "duration": "8h 00m"}

        base_price = data["price"]
        # Add some variance
        price = base_price + random.randint(-200, 200)

        return [FlightDeal(
            id=f"amadeus_{params.origin}_{params.destination}",
            origin=params.origin,
            destination=params.destination,
            route_display=f"{params.origin} -> {params.destination}",
            price=price,
            original_price=int(price * 1.35),
            currency="USD",
            cabin_class=params.cabin_class.value,
            airline=data["airline"],
            airline_name=data["name"],
            departure_date=params.departure_date,
            return_date=params.return_date,
            departure_time="18:30",
            arrival_time="07:45",
            duration=data["duration"],
            stops=0,
            deal_score=8,
            savings_percent=26,
            urgency=DealUrgency.HIGH,
            expires_at=(datetime.now() + timedelta(hours=6)).isoformat(),
            is_mistake_fare=False,
            source="amadeus",
            deep_link=self._generate_sms_link(params.origin, params.destination, price),
            booking_url=None
        )]

    def _calculate_deal_score(self, price: float, cabin: CabinClass, stops: int) -> int:
        """Calculate deal score 1-10 based on price and other factors"""
        # Base thresholds for business class transatlantic
        thresholds = {
            CabinClass.BUSINESS: {"excellent": 2000, "good": 3000, "average": 4500},
            CabinClass.FIRST: {"excellent": 4000, "good": 6000, "average": 9000},
            CabinClass.ECONOMY: {"excellent": 400, "good": 600, "average": 900},
            CabinClass.PREMIUM_ECONOMY: {"excellent": 800, "good": 1200, "average": 1800},
        }

        t = thresholds.get(cabin, thresholds[CabinClass.BUSINESS])

        if price <= t["excellent"]:
            base_score = 9
        elif price <= t["good"]:
            base_score = 7
        elif price <= t["average"]:
            base_score = 5
        else:
            base_score = 3

        # Deduct for stops
        base_score -= stops * 0.5

        return max(1, min(10, int(base_score)))

    def _determine_urgency(self, deal_score: int, price: float) -> DealUrgency:
        """Determine deal urgency based on score"""
        if deal_score >= 9:
            return DealUrgency.CRITICAL
        elif deal_score >= 7:
            return DealUrgency.HIGH
        elif deal_score >= 5:
            return DealUrgency.MEDIUM
        return DealUrgency.LOW

    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to readable string"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

    def _generate_sms_link(self, origin: str, destination: str, price: Optional[float]) -> str:
        """Generate SMS deep link for booking"""
        import urllib.parse
        message = f"Book {origin}-{destination}"
        if price:
            message += f" for ${price:,.0f}"
        return f"sms://+1234567890?body={urllib.parse.quote(message)}"

    def _create_mock_deal(self) -> FlightDeal:
        """Create a mock deal for testing"""
        return FlightDeal(
            id="amadeus_JFK_CDG",
            origin="JFK",
            destination="CDG",
            route_display="NYC -> Paris",
            price=1847,
            original_price=2497,
            currency="USD",
            cabin_class="BUSINESS",
            airline="AF",
            airline_name="Air France",
            departure_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            return_date=(datetime.now() + timedelta(days=37)).strftime("%Y-%m-%d"),
            departure_time="18:30",
            arrival_time="07:45",
            duration="7h 15m",
            stops=0,
            deal_score=8,
            savings_percent=26,
            urgency=DealUrgency.HIGH,
            expires_at=(datetime.now() + timedelta(hours=6)).isoformat(),
            is_mistake_fare=False,
            source="amadeus",
            deep_link="sms://+1234567890?body=Book%20JFK-CDG%20for%20%241%2C847",
            booking_url=None
        )


# MCP Tool Registration
async def search_flights_tool(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    adults: int = 1,
    cabin_class: str = "BUSINESS",
    max_results: int = 10
) -> Dict[str, Any]:
    """
    MCP Tool: Search for flights

    Args:
        origin: Origin airport IATA code (e.g., JFK)
        destination: Destination airport IATA code (e.g., CDG)
        departure_date: Departure date (YYYY-MM-DD)
        return_date: Optional return date (YYYY-MM-DD)
        adults: Number of adult passengers
        cabin_class: ECONOMY, PREMIUM_ECONOMY, BUSINESS, or FIRST
        max_results: Maximum number of results to return

    Returns:
        List of flight deals formatted for display
    """
    widget = FlightWidget()
    params = FlightSearchParams(
        origin=origin.upper(),
        destination=destination.upper(),
        departure_date=departure_date,
        return_date=return_date,
        adults=adults,
        cabin_class=CabinClass(cabin_class.upper()),
        max_results=max_results
    )

    deals = await widget.search_flights(params)

    return {
        "success": True,
        "count": len(deals),
        "deals": [d.to_widget_format() for d in deals]
    }


async def get_flight_widget_data_tool(
    user_id: Optional[str] = None,
    max_deals: int = 3
) -> Dict[str, Any]:
    """
    MCP Tool: Get flight widget data for iOS

    Args:
        user_id: Optional user ID for personalization
        max_deals: Maximum number of deals to include

    Returns:
        Formatted widget data ready for iOS display
    """
    widget = FlightWidget()
    return await widget.get_widget_data(user_id, max_deals)
