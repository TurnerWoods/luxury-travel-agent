"""
Luxury Travel Agent - FastAPI Development Server
"""

import os
import sys
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Templates directory
TEMPLATES_DIR = Path(__file__).parent / "templates"

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.widgets.flight_widget import (
    FlightWidget, FlightSearchParams, CabinClass,
    search_flights_tool, get_flight_widget_data_tool
)
from tools.widgets.hotel_widget import (
    HotelWidget, HotelSearchParams, HotelCategory,
    search_hotels_tool, get_hotel_widget_data_tool
)
from tools.widgets.restaurant_widget import (
    RestaurantWidget, RestaurantSearchParams, CuisineType,
    search_restaurants_tool, get_restaurant_widget_data_tool
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    print("Starting Luxury Travel Agent API...")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Luxury Travel Agent API",
    description="API for luxury travel search widgets - flights, hotels, and packages",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Models
class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    adults: int = 1
    cabin_class: str = "BUSINESS"
    max_results: int = 10


class HotelSearchRequest(BaseModel):
    location: str
    check_in: str
    check_out: str
    guests: int = 2
    rooms: int = 1
    min_rating: float = 4.0
    max_price: Optional[float] = None
    category: str = "luxury"


class RestaurantSearchRequest(BaseModel):
    location: str
    date: str
    time: str = "19:00"
    party_size: int = 2
    cuisine: str = "all"


# Routes
@app.get("/")
async def root():
    """API root - health check"""
    return {
        "status": "ok",
        "service": "Luxury Travel Agent API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# Flight endpoints
@app.post("/api/flights/search")
async def search_flights(request: FlightSearchRequest):
    """Search for flights"""
    try:
        result = await search_flights_tool(
            origin=request.origin,
            destination=request.destination,
            departure_date=request.departure_date,
            return_date=request.return_date,
            adults=request.adults,
            cabin_class=request.cabin_class,
            max_results=request.max_results
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/flights/widget")
async def get_flight_widget(user_id: Optional[str] = None, max_deals: int = 3):
    """Get flight widget data for iOS"""
    try:
        result = await get_flight_widget_data_tool(user_id, max_deals)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Hotel endpoints
@app.post("/api/hotels/search")
async def search_hotels(request: HotelSearchRequest):
    """Search for hotels"""
    try:
        result = await search_hotels_tool(
            location=request.location,
            check_in=request.check_in,
            check_out=request.check_out,
            guests=request.guests,
            rooms=request.rooms,
            min_rating=request.min_rating,
            max_price=request.max_price,
            category=request.category
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hotels/widget")
async def get_hotel_widget(user_id: Optional[str] = None, max_hotels: int = 3):
    """Get hotel widget data for iOS"""
    try:
        result = await get_hotel_widget_data_tool(user_id, max_hotels)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hotels/curated")
async def get_curated_hotels(location: str, category: str = "luxury"):
    """Get curated luxury hotels for a location"""
    # Mock curated hotels for demo
    return {
        "hotels": [
            {
                "id": "curated_1",
                "name": "Four Seasons Hotel",
                "brand": "Four Seasons",
                "location": location,
                "city": location,
                "rating": 4.9,
                "reviewCount": 2500,
                "price": 850,
                "category": category,
                "stars": 5,
                "imageUrl": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800",
                "amenities": ["Spa", "Pool", "Restaurant", "Butler Service"],
                "highlights": ["Award-winning", "City Center"]
            }
        ]
    }


# Restaurant endpoints
@app.post("/api/restaurants/search")
async def search_restaurants(request: RestaurantSearchRequest):
    """Search for restaurants"""
    try:
        result = await search_restaurants_tool(
            location=request.location,
            date=request.date,
            time=request.time,
            party_size=request.party_size,
            cuisine=request.cuisine
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/restaurants/widget")
async def get_restaurant_widget(location: Optional[str] = None, max_restaurants: int = 3):
    """Get restaurant widget data for iOS"""
    try:
        result = await get_restaurant_widget_data_tool(location, max_restaurants)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Widget-specific endpoints
@app.get("/api/widget/margaux")
async def get_margaux_widget_data(user_id: Optional[str] = None):
    """Get Margaux (flight deals) widget data"""
    return await get_flight_widget(user_id, max_deals=3)


@app.get("/api/widget/felix")
async def get_felix_widget_data(user_id: Optional[str] = None):
    """Get Felix (trip planner) widget data - placeholder"""
    return {
        "widgetType": "felix_trip_planner",
        "size": "medium_2x2",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "today": {
            "activities": [
                {"time": "10:00 AM", "name": "Hotel Checkout", "status": "confirmed", "icon": "check"},
                {"time": "2:00 PM", "name": "Wine Tasting Tour", "status": "pending", "icon": "clock"}
            ],
            "meals": [
                {"time": "7:00 PM", "name": "Michelin Dinner", "venue": "Le Bernardin", "icon": "utensils"}
            ],
            "groupStatus": {"text": "3/5 confirmed", "confirmed": 3, "total": 5, "percentage": 60}
        },
        "nextActivity": {
            "time": "2:00 PM",
            "name": "Wine Tasting Tour",
            "countdown": "4h 15m",
            "action": "confirm"
        },
        "lastUpdated": datetime.now().isoformat()
    }


# Widget Preview UI
@app.get("/preview", response_class=HTMLResponse)
async def widget_preview():
    """Beautiful widget preview page"""
    template_path = TEMPLATES_DIR / "widget_preview.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text())
    raise HTTPException(status_code=404, detail="Preview template not found")


@app.get("/logo")
async def get_logo():
    """Serve the logo file"""
    logo_paths = [
        Path(__file__).parent / "static" / "logo.png",
        Path(__file__).parent / "static" / "logo.svg",
        Path(__file__).parent.parent / "assets" / "logo.png",
        Path(__file__).parent.parent / "logo.png",
    ]

    for logo_path in logo_paths:
        if logo_path.exists():
            media_type = "image/svg+xml" if logo_path.suffix == ".svg" else "image/png"
            return FileResponse(logo_path, media_type=media_type)

    raise HTTPException(status_code=404, detail="Logo not found")


@app.get("/logo-circle")
async def get_logo_circle():
    """Serve the circular logo for avatars"""
    logo_path = Path(__file__).parent / "static" / "logo-circle.png"
    if logo_path.exists():
        return FileResponse(logo_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Circle logo not found")


@app.get("/preview/flights", response_class=HTMLResponse)
async def flights_preview():
    """Flight cards preview"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>Flight Cards Preview</title>
    <script>window.location.href = '/preview';</script>
</head>
<body>Redirecting...</body>
</html>
    """)


# ============== WhatsApp Webhook ==============

WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "luxurytravel_webhook_2024")

from fastapi import Query

@app.get("/webhook/whatsapp")
async def whatsapp_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """WhatsApp webhook verification (GET request from Meta)"""
    print(f"🔐 Webhook verify: mode={hub_mode}, token={hub_verify_token}")
    if hub_mode == "subscribe" and hub_verify_token == WHATSAPP_VERIFY_TOKEN:
        print(f"✅ WhatsApp webhook verified!")
        return int(hub_challenge) if hub_challenge else "OK"
    raise HTTPException(status_code=403, detail="Verification failed")


from fastapi import Request
import hmac
import hashlib

APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "")

@app.post("/webhook/whatsapp")
async def whatsapp_incoming(request: Request):
    """Handle incoming WhatsApp messages"""
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Get raw body for signature validation
        body = await request.body()
        body_str = body.decode('utf-8')

        # Validate signature if APP_SECRET is configured
        signature = request.headers.get("X-Hub-Signature-256", "")
        if APP_SECRET and signature:
            expected_sig = "sha256=" + hmac.new(
                APP_SECRET.encode(),
                body,
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(signature, expected_sig):
                logger.warning("❌ Invalid webhook signature")
                raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse JSON payload
        import json
        payload = json.loads(body_str)

        # Log incoming webhook
        logger.info(f"📱 WhatsApp webhook received")

        # Extract message data
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        # Check for incoming messages
        messages = value.get("messages", [])
        for message in messages:
            from_number = message.get("from")
            msg_type = message.get("type")

            if msg_type == "text":
                text = message.get("text", {}).get("body", "")
                logger.info(f"📨 Message from {from_number}: {text}")

                # Handle button replies
            elif msg_type == "interactive":
                interactive = message.get("interactive", {})
                button_reply = interactive.get("button_reply", {})
                button_id = button_reply.get("id", "")
                logger.info(f"🔘 Button click from {from_number}: {button_id}")

                # Process button actions
                if button_id.startswith("book_"):
                    logger.info(f"📋 Booking request: {button_id}")
                elif button_id.startswith("details_"):
                    logger.info(f"ℹ️ Details request: {button_id}")
                elif button_id.startswith("cart_"):
                    logger.info(f"🛒 Add to cart: {button_id}")

        # Check for message status updates
        statuses = value.get("statuses", [])
        for status in statuses:
            msg_status = status.get("status")
            recipient = status.get("recipient_id")
            logger.info(f"📊 Message to {recipient}: {msg_status}")

        return {"status": "received"}

    except Exception as e:
        logger.error(f"❌ Webhook error: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/webhook/status")
async def webhook_status():
    """Check webhook configuration status"""
    return {
        "webhook_endpoint": "/webhook/whatsapp",
        "verify_token": WHATSAPP_VERIFY_TOKEN,
        "signature_validation": "enabled" if APP_SECRET else "disabled (set WHATSAPP_APP_SECRET)",
        "status": "ready",
        "setup_steps": [
            "1. Install ngrok: brew install ngrok (or download from ngrok.com)",
            "2. Run: ngrok http 8000",
            "3. Copy the HTTPS URL (e.g., https://abc123.ngrok-free.app)",
            "4. Go to: developers.facebook.com → Your App → WhatsApp → Configuration",
            f"5. Callback URL: <YOUR-NGROK-URL>/webhook/whatsapp",
            f"6. Verify Token: {WHATSAPP_VERIFY_TOKEN}",
            "7. Click 'Verify and Save'",
            "8. Subscribe to: messages, message_deliveries, message_reads"
        ],
        "env_vars_needed": {
            "WHATSAPP_ACCESS_TOKEN": "From App Dashboard → WhatsApp → API Setup",
            "WHATSAPP_PHONE_NUMBER_ID": "From App Dashboard → WhatsApp → API Setup",
            "WHATSAPP_APP_SECRET": "From App Dashboard → Settings → Basic → App Secret"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
