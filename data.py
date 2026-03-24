"""Mock data for venues and bookings — replace with DB calls later."""

VENUES = [
    {"id": 1, "name": "Green Turf FC", "sport": "Football", "city": "Mumbai", "price": 800, "slots": ["06:00", "08:00", "10:00", "16:00", "18:00", "20:00"]},
    {"id": 2, "name": "Smash Badminton", "sport": "Badminton", "city": "Mumbai", "price": 400, "slots": ["07:00", "09:00", "11:00", "17:00", "19:00"]},
    {"id": 3, "name": "Cricket Nets Arena", "sport": "Cricket", "city": "Bangalore", "price": 600, "slots": ["06:00", "08:00", "10:00", "15:00", "17:00"]},
    {"id": 4, "name": "Ace Tennis Club", "sport": "Tennis", "city": "Bangalore", "price": 700, "slots": ["07:00", "09:00", "16:00", "18:00", "20:00"]},
    {"id": 5, "name": "Goal Zone", "sport": "Football", "city": "Bangalore", "price": 900, "slots": ["06:00", "08:00", "18:00", "20:00"]},
]

# In-memory bookings store — replace with DB later
BOOKINGS = {}
booking_counter = 1000


def get_venues_by_sport(sport: str):
    return [v for v in VENUES if v["sport"].lower() == sport.lower()]


def get_venue_by_id(venue_id: int):
    return next((v for v in VENUES if v["id"] == venue_id), None)


def create_booking(phone: str, venue_id: int, date: str, slot: str):
    global booking_counter
    venue = get_venue_by_id(venue_id)
    if not venue:
        return None
    booking_counter += 1
    booking_id = f"BK{booking_counter}"
    BOOKINGS[booking_id] = {
        "id": booking_id,
        "phone": phone,
        "venue": venue["name"],
        "sport": venue["sport"],
        "date": date,
        "slot": slot,
        "price": venue["price"],
    }
    return BOOKINGS[booking_id]


def get_bookings_by_phone(phone: str):
    return [b for b in BOOKINGS.values() if b["phone"] == phone]


def cancel_booking(booking_id: str, phone: str):
    booking = BOOKINGS.get(booking_id)
    if booking and booking["phone"] == phone:
        del BOOKINGS[booking_id]
        return True
    return False
