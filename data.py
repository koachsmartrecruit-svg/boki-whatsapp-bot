"""
data.py — Drop-in replacement for Boki WhatsApp bot.
Replaces mock VENUES dict and in-memory BOOKINGS with real API calls
to the SportsBook Flask backend.

Usage: copy this file to the boki-whatsapp-bot repo as data.py
"""

import requests

BASE_URL = "https://vbs-83xv.onrender.com"

# Timeout for all API calls (seconds)
TIMEOUT = 10


# ─────────────────────────────────────────────────────────────
# Venues
# ─────────────────────────────────────────────────────────────

def get_venues_by_sport(sport: str) -> list:
    """Return list of venue dicts matching the given sport."""
    try:
        r = requests.get(
            f"{BASE_URL}/api/venues",
            params={"sport": sport},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        venues = r.json()
        # Normalise to match bot's expected shape
        return [_normalise_venue(v) for v in venues]
    except Exception as e:
        print(f"[Boki] get_venues_by_sport error: {e}")
        return []


def get_venue_by_id(venue_id: int) -> dict | None:
    """Return a single venue dict or None."""
    try:
        r = requests.get(f"{BASE_URL}/api/venues/{venue_id}", timeout=TIMEOUT)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return _normalise_venue(r.json())
    except Exception as e:
        print(f"[Boki] get_venue_by_id error: {e}")
        return None


def get_available_slots(venue_id: int, date_str: str) -> list:
    """
    Return list of available start-time strings for a venue on a date.
    date_str format: YYYY-MM-DD
    Returns e.g. ["06:00", "08:00", "10:00", ...]
    """
    try:
        r = requests.get(
            f"{BASE_URL}/api/venues/{venue_id}/available-slots",
            params={"date": date_str},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        return [s["start"] for s in data.get("slots", [])]
    except Exception as e:
        print(f"[Boki] get_available_slots error: {e}")
        return []


# ─────────────────────────────────────────────────────────────
# Bookings
# ─────────────────────────────────────────────────────────────

def create_booking(phone: str, venue_id: int, date_str: str, slot: str, player_name: str = "WhatsApp User") -> dict | None:
    """
    Create a booking. Returns booking dict on success, None on failure.
    date_str: DD-MM-YYYY (bot format) — converted to YYYY-MM-DD for API
    slot: "HH:MM"
    """
    # Convert DD-MM-YYYY → YYYY-MM-DD
    try:
        from datetime import datetime
        api_date = datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")
    except ValueError:
        api_date = date_str  # pass through if already YYYY-MM-DD

    try:
        r = requests.post(
            f"{BASE_URL}/api/bookings",
            json={
                "phone": phone,
                "venue_id": venue_id,
                "date": api_date,
                "slot": slot,
                "player_name": player_name,
            },
            timeout=TIMEOUT,
        )
        if r.status_code == 409:
            # Slot already taken
            return {"error": r.json().get("error", "Slot already booked")}
        r.raise_for_status()
        data = r.json()
        b = data["booking"]
        # Normalise to bot's expected shape
        return {
            "id": b["id"],           # "BK1234"
            "phone": b["phone"],
            "venue": b["venue"],
            "sport": b["sport"],
            "date": date_str,        # keep original DD-MM-YYYY for display
            "slot": b["slot"],
            "price": b["price"],
        }
    except Exception as e:
        print(f"[Boki] create_booking error: {e}")
        return None


def get_bookings_by_phone(phone: str) -> list:
    """Return list of active booking dicts for a phone number."""
    try:
        r = requests.get(
            f"{BASE_URL}/api/bookings",
            params={"phone": phone},
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        bookings = r.json()
        result = []
        for b in bookings:
            # Convert YYYY-MM-DD → DD-MM-YYYY for display
            try:
                from datetime import datetime
                display_date = datetime.strptime(b["date"], "%Y-%m-%d").strftime("%d-%m-%Y")
            except Exception:
                display_date = b["date"]
            result.append({
                "id": b["id"],
                "phone": b.get("phone", phone),
                "venue": b["venue"],
                "sport": b["sport"],
                "date": display_date,
                "slot": b["slot"],
                "price": b["price"],
            })
        return result
    except Exception as e:
        print(f"[Boki] get_bookings_by_phone error: {e}")
        return []


def cancel_booking(booking_id: str, phone: str) -> bool:
    """Cancel a booking by ID (BK1234 format) and phone. Returns True on success."""
    try:
        r = requests.post(
            f"{BASE_URL}/api/bookings/{booking_id}/cancel",
            json={"phone": phone},
            timeout=TIMEOUT,
        )
        if r.status_code in (404, 400):
            return False
        r.raise_for_status()
        return r.json().get("success", False)
    except Exception as e:
        print(f"[Boki] cancel_booking error: {e}")
        return False


# ─────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────

def _normalise_venue(v: dict) -> dict:
    """Map API venue shape to the shape bot.py expects."""
    return {
        "id": v["id"],
        "name": v["name"],
        "sport": v["sport"],
        "city": v["city"],
        "price": v["price"],
        # slots are fetched separately via get_available_slots()
        "slots": [],
    }
