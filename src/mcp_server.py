#!/usr/bin/env python3
"""
Luxury Travel Agent MCP Server
Exposes flight and hotel search tools to Claude Desktop
"""

import asyncio
import json
import sys
from typing import Any

# MCP Protocol Implementation
class MCPServer:
    def __init__(self):
        self.tools = {
            "search_flights": {
                "description": "Search for flights between airports",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "origin": {
                            "type": "string",
                            "description": "Origin airport IATA code (e.g., JFK)"
                        },
                        "destination": {
                            "type": "string",
                            "description": "Destination airport IATA code (e.g., CDG)"
                        },
                        "departure_date": {
                            "type": "string",
                            "description": "Departure date (YYYY-MM-DD)"
                        },
                        "return_date": {
                            "type": "string",
                            "description": "Return date (YYYY-MM-DD, optional)"
                        },
                        "cabin_class": {
                            "type": "string",
                            "enum": ["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"],
                            "description": "Cabin class (default: BUSINESS)"
                        },
                        "adults": {
                            "type": "integer",
                            "description": "Number of adult passengers (default: 1)"
                        }
                    },
                    "required": ["origin", "destination", "departure_date"]
                }
            },
            "search_hotels": {
                "description": "Search for luxury hotels in a destination",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name or IATA code (e.g., Paris, PAR)"
                        },
                        "check_in": {
                            "type": "string",
                            "description": "Check-in date (YYYY-MM-DD)"
                        },
                        "check_out": {
                            "type": "string",
                            "description": "Check-out date (YYYY-MM-DD)"
                        },
                        "guests": {
                            "type": "integer",
                            "description": "Number of guests (default: 2)"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["luxury", "boutique", "resort", "business"],
                            "description": "Hotel category (default: luxury)"
                        }
                    },
                    "required": ["location", "check_in", "check_out"]
                }
            },
            "get_flight_deals": {
                "description": "Get current flight deals for iOS widget display",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "max_deals": {
                            "type": "integer",
                            "description": "Maximum number of deals to return (default: 3)"
                        }
                    }
                }
            },
            "get_hotel_recommendations": {
                "description": "Get luxury hotel recommendations for iOS widget display",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "max_hotels": {
                            "type": "integer",
                            "description": "Maximum number of hotels to return (default: 3)"
                        }
                    }
                }
            },
            "search_restaurants": {
                "description": "Search for fine dining restaurants",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name (e.g., Paris, Tokyo, Miami)"
                        },
                        "date": {
                            "type": "string",
                            "description": "Reservation date (YYYY-MM-DD)"
                        },
                        "time": {
                            "type": "string",
                            "description": "Preferred time (HH:MM, default: 19:00)"
                        },
                        "party_size": {
                            "type": "integer",
                            "description": "Number of guests (default: 2)"
                        },
                        "cuisine": {
                            "type": "string",
                            "enum": ["french", "italian", "japanese", "american", "seafood", "steakhouse", "all"],
                            "description": "Cuisine type (default: all)"
                        }
                    },
                    "required": ["location", "date"]
                }
            },
            "get_restaurant_recommendations": {
                "description": "Get fine dining restaurant recommendations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City name (default: Paris)"
                        },
                        "max_restaurants": {
                            "type": "integer",
                            "description": "Maximum number of restaurants to return (default: 3)"
                        }
                    }
                }
            },
            "send_to_whatsapp": {
                "description": "Send travel options (flights, hotels, restaurants) as interactive cards to WhatsApp",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "phone": {
                            "type": "string",
                            "description": "Recipient phone number with country code (e.g., +1234567890)"
                        },
                        "item_type": {
                            "type": "string",
                            "enum": ["flight", "hotel", "restaurant"],
                            "description": "Type of item to send"
                        },
                        "item": {
                            "type": "object",
                            "description": "The travel item data to send"
                        }
                    },
                    "required": ["phone", "item_type", "item"]
                }
            }
        }

    async def handle_request(self, request: dict) -> dict:
        """Handle incoming MCP request."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        if method == "initialize":
            return self._response(request_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "luxury-travel-agent",
                    "version": "1.0.0"
                }
            })

        elif method == "tools/list":
            tools_list = [
                {
                    "name": name,
                    "description": info["description"],
                    "inputSchema": info["inputSchema"]
                }
                for name, info in self.tools.items()
            ]
            return self._response(request_id, {"tools": tools_list})

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            result = await self._call_tool(tool_name, arguments)

            # Build content with images for travel searches
            content = []

            # Add images if available in results
            images = result.get("images", [])
            for img in images[:3]:  # Limit to 3 images
                content.append({
                    "type": "image",
                    "data": img.get("url", ""),
                    "mimeType": "image/jpeg"
                })

            # Add text result
            content.append({
                "type": "text",
                "text": json.dumps(result, indent=2)
            })

            return self._response(request_id, {"content": content})

        elif method == "notifications/initialized":
            return None  # No response needed for notifications

        else:
            return self._error(request_id, -32601, f"Method not found: {method}")

    async def _call_tool(self, tool_name: str, arguments: dict) -> Any:
        """Execute a tool and return results."""

        # Import tools
        sys.path.insert(0, '/Users/mac2/luxury-travel-agent/src')

        if tool_name == "search_flights":
            from tools.widgets.flight_widget import search_flights_tool
            result = await search_flights_tool(
                origin=arguments.get("origin", "JFK"),
                destination=arguments.get("destination", "CDG"),
                departure_date=arguments.get("departure_date"),
                return_date=arguments.get("return_date"),
                adults=arguments.get("adults", 1),
                cabin_class=arguments.get("cabin_class", "BUSINESS"),
                max_results=10
            )
            return self._format_flights(result)

        elif tool_name == "search_hotels":
            from tools.widgets.hotel_widget import search_hotels_tool
            result = await search_hotels_tool(
                location=arguments.get("location"),
                check_in=arguments.get("check_in"),
                check_out=arguments.get("check_out"),
                guests=arguments.get("guests", 2),
                rooms=1,
                category=arguments.get("category", "luxury")
            )
            return self._format_hotels(result)

        elif tool_name == "get_flight_deals":
            from tools.widgets.flight_widget import get_flight_widget_data_tool
            result = await get_flight_widget_data_tool(
                max_deals=arguments.get("max_deals", 3)
            )
            return self._format_flights({"deals": result.get("allDeals", []), "count": len(result.get("allDeals", []))})

        elif tool_name == "get_hotel_recommendations":
            from tools.widgets.hotel_widget import get_hotel_widget_data_tool
            result = await get_hotel_widget_data_tool(
                max_hotels=arguments.get("max_hotels", 3)
            )
            return self._format_hotels({"hotels": result.get("allHotels", []), "count": len(result.get("allHotels", []))})

        elif tool_name == "search_restaurants":
            from tools.widgets.restaurant_widget import search_restaurants_tool
            result = await search_restaurants_tool(
                location=arguments.get("location", "Paris"),
                date=arguments.get("date"),
                time=arguments.get("time", "19:00"),
                party_size=arguments.get("party_size", 2),
                cuisine=arguments.get("cuisine", "all")
            )
            return self._format_restaurants(result)

        elif tool_name == "get_restaurant_recommendations":
            from tools.widgets.restaurant_widget import get_restaurant_widget_data_tool
            result = await get_restaurant_widget_data_tool(
                location=arguments.get("location", "Paris"),
                max_restaurants=arguments.get("max_restaurants", 3)
            )
            return self._format_restaurants({"restaurants": result.get("allRestaurants", []), "count": len(result.get("allRestaurants", []))})

        elif tool_name == "send_to_whatsapp":
            from tools.whatsapp_sender import (
                send_flight_to_whatsapp,
                send_hotel_to_whatsapp,
                send_restaurant_to_whatsapp
            )
            phone = arguments.get("phone")
            item_type = arguments.get("item_type")
            item = arguments.get("item")

            if item_type == "flight":
                result = await send_flight_to_whatsapp(phone, item)
            elif item_type == "hotel":
                result = await send_hotel_to_whatsapp(phone, item)
            elif item_type == "restaurant":
                result = await send_restaurant_to_whatsapp(phone, item)
            else:
                result = {"error": f"Unknown item type: {item_type}"}

            return result

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    def _format_flights(self, result: dict) -> dict:
        """Format flight results as structured data for display."""
        deals = result.get("deals", [])
        if not deals:
            return {"formatted": "No flights found.", "raw": result, "images": []}

        flights = []
        images = []
        for deal in deals:
            flight = {
                "airline": deal.get("airlineName", ""),
                "route": deal.get("route", ""),
                "cabin": deal.get("cabin", ""),
                "departure": f"{deal.get('departureDate', '')} at {deal.get('departureTime', '')}",
                "arrival": deal.get('arrivalTime', ''),
                "duration": deal.get("duration", ""),
                "stops": deal.get("stopsDisplay", ""),
                "price": deal.get("price", ""),
                "original_price": deal.get("originalPrice", ""),
                "savings": deal.get("savings", ""),
                "deal_score": deal.get("dealScore", 0),
                "urgency": deal.get("urgency", ""),
                "image_url": deal.get("imageUrl", "")
            }
            flights.append(flight)
            if deal.get("imageUrl"):
                images.append({"url": deal.get("imageUrl"), "caption": f"{flight['airline']} - {flight['route']}"})

        return {
            "type": "flight_results",
            "count": len(flights),
            "flights": flights,
            "images": images[:3]
        }

    def _format_hotels(self, result: dict) -> dict:
        """Format hotel results as structured data for display."""
        hotels_data = result.get("hotels", [])
        if not hotels_data:
            return {"formatted": "No hotels found.", "raw": result, "images": []}

        hotels = []
        images = []
        for h in hotels_data:
            hotel = {
                "name": h.get("name", ""),
                "brand": h.get("brand", ""),
                "location": h.get("city", ""),
                "rating": h.get("ratingDisplay", ""),
                "reviews": h.get("reviewsDisplay", ""),
                "stars": h.get("starsDisplay", ""),
                "price_per_night": h.get("pricePerNight", ""),
                "original_price": h.get("originalPrice", ""),
                "total_price": h.get("totalPrice", ""),
                "savings": h.get("savings", ""),
                "amenities": h.get("amenitiesDisplay", ""),
                "room_type": h.get("roomType", ""),
                "image_url": h.get("imageUrl", "")
            }
            hotels.append(hotel)
            if h.get("imageUrl"):
                images.append({"url": h.get("imageUrl"), "caption": f"{hotel['name']} - {hotel['location']}"})

        return {
            "type": "hotel_results",
            "count": len(hotels),
            "hotels": hotels,
            "images": images[:3]
        }

    def _format_restaurants(self, result: dict) -> dict:
        """Format restaurant results as structured data for display."""
        restaurants_data = result.get("restaurants", [])
        if not restaurants_data:
            return {"formatted": "No restaurants found.", "raw": result, "images": []}

        restaurants = []
        images = []
        for r in restaurants_data:
            restaurant = {
                "name": r.get("name", ""),
                "cuisine": r.get("cuisineDisplay", ""),
                "location": r.get("neighborhood", ""),
                "city": r.get("city", ""),
                "rating": r.get("ratingDisplay", ""),
                "reviews": r.get("reviewsDisplay", ""),
                "price_range": r.get("priceRange", ""),
                "michelin_stars": r.get("michelinStars", 0),
                "michelin_display": r.get("michelinDisplay", ""),
                "description": r.get("description", ""),
                "highlights": r.get("highlightsDisplay", ""),
                "available_times": r.get("availableTimes", []),
                "image_url": r.get("imageUrl", "")
            }
            restaurants.append(restaurant)
            if r.get("imageUrl"):
                michelin = f" ({r.get('michelinStars', 0)}★ Michelin)" if r.get("michelinStars", 0) > 0 else ""
                images.append({"url": r.get("imageUrl"), "caption": f"{restaurant['name']}{michelin}"})

        return {
            "type": "restaurant_results",
            "count": len(restaurants),
            "restaurants": restaurants,
            "images": images[:3]
        }

    def _response(self, request_id: Any, result: dict) -> dict:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }

    def _error(self, request_id: Any, code: int, message: str) -> dict:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }


async def main():
    """Main entry point - reads from stdin, writes to stdout."""
    server = MCPServer()

    # Read from stdin line by line
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

    while True:
        try:
            line = await reader.readline()
            if not line:
                break

            line = line.decode().strip()
            if not line:
                continue

            request = json.loads(line)
            response = await server.handle_request(request)

            if response:
                print(json.dumps(response), flush=True)

        except json.JSONDecodeError as e:
            sys.stderr.write(f"JSON decode error: {e}\n")
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())
