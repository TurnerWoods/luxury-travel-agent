"""
WhatsApp Business API Integration for Luxury Travel Agent
Sends travel options as interactive cards with booking buttons
"""

import os
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """
    WhatsApp Cloud API client for sending interactive travel messages

    Message Types:
    - Interactive buttons (up to 3 buttons per message)
    - Interactive lists (up to 10 sections)
    - Image messages with captions
    - Template messages for booking confirmations
    """

    API_URL = "https://graph.facebook.com/v18.0"

    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.business_account_id = os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID")

    @property
    def is_configured(self) -> bool:
        return bool(self.access_token and self.phone_number_id)

    async def send_flight_card(
        self,
        to: str,
        flight: Dict[str, Any],
        booking_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a flight deal as an interactive WhatsApp message

        Args:
            to: Recipient phone number (with country code, e.g., +1234567890)
            flight: Flight data from flight widget
            booking_url: URL for booking button
        """
        # Format the message body
        body = f"""✈️ *{flight.get('route', 'Flight Deal')}*

💺 {flight.get('cabin', 'Business Class')}
🛫 {flight.get('airlineName', flight.get('airline', ''))}
📅 {flight.get('departureDate', '')} at {flight.get('departureTime', '')}
⏱️ {flight.get('duration', '')} · {flight.get('stopsDisplay', 'Nonstop')}

💰 *{flight.get('price', '')}* per person"""

        if flight.get('savings'):
            body += f"\n🏷️ {flight.get('savings')}"

        # Create interactive message with buttons
        message = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to.replace("+", "").replace(" ", ""),
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {
                    "type": "image",
                    "image": {
                        "link": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=800"
                    }
                },
                "body": {
                    "text": body
                },
                "footer": {
                    "text": "LuxuryTravel.AI"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"book_flight_{flight.get('id', 'unknown')}",
                                "title": "Book Now"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"details_flight_{flight.get('id', 'unknown')}",
                                "title": "More Details"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"cart_flight_{flight.get('id', 'unknown')}",
                                "title": "Add to Cart"
                            }
                        }
                    ]
                }
            }
        }

        return await self._send_message(message)

    async def send_hotel_card(
        self,
        to: str,
        hotel: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send a hotel as an interactive WhatsApp message"""

        body = f"""🏨 *{hotel.get('name', 'Luxury Hotel')}*

📍 {hotel.get('city', '')}
⭐ {hotel.get('ratingDisplay', hotel.get('rating', '4.9'))}/5 · {hotel.get('reviewsDisplay', '')}
{'⭐' * hotel.get('stars', 5)} {hotel.get('stars', 5)}-Star

💰 *{hotel.get('pricePerNight', hotel.get('price_per_night', ''))}* per night"""

        if hotel.get('savings'):
            body += f"\n🏷️ {hotel.get('savings')}"

        if hotel.get('amenitiesDisplay'):
            body += f"\n\n✨ {hotel.get('amenitiesDisplay')}"

        message = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to.replace("+", "").replace(" ", ""),
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {
                    "type": "image",
                    "image": {
                        "link": hotel.get('imageUrl', hotel.get('image_url', 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800'))
                    }
                },
                "body": {
                    "text": body
                },
                "footer": {
                    "text": "LuxuryTravel.AI"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"book_hotel_{hotel.get('id', 'unknown')}",
                                "title": "Book Now"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"details_hotel_{hotel.get('id', 'unknown')}",
                                "title": "View Rooms"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"cart_hotel_{hotel.get('id', 'unknown')}",
                                "title": "Add to Cart"
                            }
                        }
                    ]
                }
            }
        }

        return await self._send_message(message)

    async def send_restaurant_card(
        self,
        to: str,
        restaurant: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send a restaurant as an interactive WhatsApp message"""

        michelin = restaurant.get('michelinStars', restaurant.get('michelin_stars', 0))
        michelin_text = f"{'⭐' * michelin} Michelin" if michelin > 0 else ""

        body = f"""🍽️ *{restaurant.get('name', 'Restaurant')}*

🍴 {restaurant.get('cuisineDisplay', restaurant.get('cuisine_display', ''))}
📍 {restaurant.get('neighborhood', '')}
⭐ {restaurant.get('ratingDisplay', restaurant.get('rating', '4.8'))}/5
{michelin_text}

💰 {restaurant.get('priceRange', restaurant.get('price_range', '$$$'))}"""

        times = restaurant.get('availableTimes', restaurant.get('available_times', []))
        if times:
            body += f"\n\n🕐 Available: {', '.join(times[:3])}"

        message = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to.replace("+", "").replace(" ", ""),
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {
                    "type": "image",
                    "image": {
                        "link": restaurant.get('imageUrl', restaurant.get('image_url', 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800'))
                    }
                },
                "body": {
                    "text": body
                },
                "footer": {
                    "text": "LuxuryTravel.AI"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"reserve_{restaurant.get('id', 'unknown')}",
                                "title": "Reserve Now"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"menu_{restaurant.get('id', 'unknown')}",
                                "title": "View Menu"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": f"cart_restaurant_{restaurant.get('id', 'unknown')}",
                                "title": "Add to Trip"
                            }
                        }
                    ]
                }
            }
        }

        return await self._send_message(message)

    async def send_travel_list(
        self,
        to: str,
        title: str,
        items: List[Dict[str, Any]],
        item_type: str = "flight"
    ) -> Dict[str, Any]:
        """
        Send multiple options as a WhatsApp list message
        Good for showing multiple flights, hotels, or restaurants at once
        """

        rows = []
        for item in items[:10]:  # WhatsApp limit is 10 rows
            if item_type == "flight":
                rows.append({
                    "id": f"select_{item.get('id', '')}",
                    "title": f"{item.get('route', '')} - {item.get('price', '')}",
                    "description": f"{item.get('airlineName', '')} · {item.get('duration', '')}"
                })
            elif item_type == "hotel":
                rows.append({
                    "id": f"select_{item.get('id', '')}",
                    "title": item.get('name', '')[:24],
                    "description": f"{item.get('pricePerNight', '')} · {item.get('ratingDisplay', '')}⭐"
                })
            elif item_type == "restaurant":
                rows.append({
                    "id": f"select_{item.get('id', '')}",
                    "title": item.get('name', '')[:24],
                    "description": f"{item.get('cuisineDisplay', '')} · {item.get('priceRange', '')}"
                })

        message = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to.replace("+", "").replace(" ", ""),
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {
                    "type": "text",
                    "text": title
                },
                "body": {
                    "text": f"Found {len(items)} options. Tap to view details."
                },
                "footer": {
                    "text": "LuxuryTravel.AI"
                },
                "action": {
                    "button": "View Options",
                    "sections": [
                        {
                            "title": f"{item_type.title()}s",
                            "rows": rows
                        }
                    ]
                }
            }
        }

        return await self._send_message(message)

    async def send_cart_summary(
        self,
        to: str,
        cart_items: List[Dict[str, Any]],
        total: float
    ) -> Dict[str, Any]:
        """Send a cart summary with checkout button"""

        body = "🛒 *Your Travel Cart*\n\n"

        for item in cart_items:
            item_type = item.get('type', 'item')
            if item_type == 'flight':
                body += f"✈️ {item.get('route', '')} - {item.get('price', '')}\n"
            elif item_type == 'hotel':
                body += f"🏨 {item.get('name', '')} - {item.get('totalPrice', '')}\n"
            elif item_type == 'restaurant':
                body += f"🍽️ {item.get('name', '')} - Reservation\n"

        body += f"\n💰 *Total: ${total:,.2f}*"

        message = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to.replace("+", "").replace(" ", ""),
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": body
                },
                "footer": {
                    "text": "Ready to complete your booking?"
                },
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {
                                "id": "checkout_now",
                                "title": "Checkout"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "modify_cart",
                                "title": "Modify Cart"
                            }
                        },
                        {
                            "type": "reply",
                            "reply": {
                                "id": "clear_cart",
                                "title": "Clear Cart"
                            }
                        }
                    ]
                }
            }
        }

        return await self._send_message(message)

    async def _send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send message via WhatsApp Cloud API"""

        if not self.is_configured:
            # Return mock response for testing
            return {
                "success": True,
                "mock": True,
                "message": "WhatsApp not configured - showing preview",
                "preview": message
            }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.API_URL}/{self.phone_number_id}/messages",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    json=message
                )

                if response.status_code == 200:
                    return {
                        "success": True,
                        "response": response.json()
                    }
                else:
                    return {
                        "success": False,
                        "error": response.text
                    }
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# MCP Tool Functions
async def send_flight_to_whatsapp(
    phone: str,
    flight: Dict[str, Any]
) -> Dict[str, Any]:
    """
    MCP Tool: Send a flight deal to WhatsApp

    Args:
        phone: Recipient phone number with country code (e.g., +1234567890)
        flight: Flight data from search results
    """
    client = WhatsAppClient()
    return await client.send_flight_card(phone, flight)


async def send_hotel_to_whatsapp(
    phone: str,
    hotel: Dict[str, Any]
) -> Dict[str, Any]:
    """
    MCP Tool: Send a hotel to WhatsApp
    """
    client = WhatsAppClient()
    return await client.send_hotel_card(phone, hotel)


async def send_restaurant_to_whatsapp(
    phone: str,
    restaurant: Dict[str, Any]
) -> Dict[str, Any]:
    """
    MCP Tool: Send a restaurant to WhatsApp
    """
    client = WhatsAppClient()
    return await client.send_restaurant_card(phone, restaurant)


async def send_options_list_to_whatsapp(
    phone: str,
    title: str,
    items: List[Dict[str, Any]],
    item_type: str = "flight"
) -> Dict[str, Any]:
    """
    MCP Tool: Send a list of travel options to WhatsApp
    """
    client = WhatsAppClient()
    return await client.send_travel_list(phone, title, items, item_type)
