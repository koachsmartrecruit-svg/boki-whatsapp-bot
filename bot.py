"""Conversation state machine for the WhatsApp bot."""

from data import (
    VENUES, get_venues_by_sport, get_venue_by_id,
    create_booking, get_bookings_by_phone, cancel_booking
)
from datetime import datetime

# Per-user session state stored in memory — use Redis/DB for production
sessions = {}

SPORTS = ["Football", "Badminton", "Cricket", "Tennis"]


def get_session(phone: str) -> dict:
    if phone not in sessions:
        sessions[phone] = {"step": "menu"}
    return sessions[phone]


def reset_session(phone: str):
    sessions[phone] = {"step": "menu"}


def handle_message(phone: str, message: str) -> str:
    msg = message.strip().lower()
    session = get_session(phone)
    step = session.get("step")

    # Allow user to go back to menu anytime
    if msg in ["menu", "hi", "hello", "start", "0"]:
        reset_session(phone)
        return main_menu()

    if step == "menu":
        return handle_menu(phone, msg, session)
    elif step == "select_sport":
        return handle_select_sport(phone, msg, session)
    elif step == "select_venue":
        return handle_select_venue(phone, msg, session)
    elif step == "enter_date":
        return handle_enter_date(phone, msg, session)
    elif step == "select_slot":
        return handle_select_slot(phone, msg, session)
    elif step == "confirm_booking":
        return handle_confirm_booking(phone, msg, session)
    elif step == "my_bookings":
        return handle_my_bookings_action(phone, msg, session)
    elif step == "cancel_booking":
        return handle_cancel_booking(phone, msg, session)
    else:
        reset_session(phone)
        return main_menu()


def main_menu() -> str:
    return (
        "👋 Welcome to *Boki* — Book Sports Venues Instantly!\n\n"
        "What would you like to do?\n\n"
        "1️⃣  Browse & Book a Venue\n"
        "2️⃣  My Bookings\n"
        "3️⃣  Cancel a Booking\n\n"
        "Reply with 1, 2, or 3"
    )


def handle_menu(phone: str, msg: str, session: dict) -> str:
    if msg == "1":
        session["step"] = "select_sport"
        sports_list = "\n".join([f"{i+1}️⃣  {s}" for i, s in enumerate(SPORTS)])
        return f"🏅 Choose a sport:\n\n{sports_list}\n\nReply with the number"
    elif msg == "2":
        return show_my_bookings(phone, session)
    elif msg == "3":
        session["step"] = "cancel_booking"
        return "Enter your Booking ID to cancel (e.g. BK1001):\n\nOr type *menu* to go back"
    else:
        return "Please reply with 1, 2, or 3\n\n" + main_menu()


def handle_select_sport(phone: str, msg: str, session: dict) -> str:
    try:
        idx = int(msg) - 1
        if idx < 0 or idx >= len(SPORTS):
            raise ValueError
    except ValueError:
        return "Please reply with a number from the list.\n\n" + "\n".join([f"{i+1}. {s}" for i, s in enumerate(SPORTS)])

    sport = SPORTS[idx]
    venues = get_venues_by_sport(sport)

    if not venues:
        reset_session(phone)
        return f"Sorry, no {sport} venues available right now.\n\nType *menu* to go back."

    session["sport"] = sport
    session["venues"] = venues
    session["step"] = "select_venue"

    venue_list = "\n".join([
        f"{i+1}️⃣  *{v['name']}* — {v['city']} — ₹{v['price']}/hr"
        for i, v in enumerate(venues)
    ])
    return f"🏟️ Available *{sport}* venues:\n\n{venue_list}\n\nReply with the number to select"


def handle_select_venue(phone: str, msg: str, session: dict) -> str:
    venues = session.get("venues", [])
    try:
        idx = int(msg) - 1
        if idx < 0 or idx >= len(venues):
            raise ValueError
    except ValueError:
        return "Please reply with a valid venue number."

    venue = venues[idx]
    session["venue_id"] = venue["id"]
    session["venue_name"] = venue["name"]
    session["step"] = "enter_date"

    return (
        f"📍 *{venue['name']}* selected\n"
        f"💰 ₹{venue['price']}/hr\n\n"
        f"Enter the date you want to book (DD-MM-YYYY):\n"
        f"e.g. {datetime.now().strftime('%d-%m-%Y')}"
    )


def handle_enter_date(phone: str, msg: str, session: dict) -> str:
    try:
        date = datetime.strptime(msg, "%d-%m-%Y")
        if date.date() < datetime.now().date():
            return "That date is in the past. Please enter a future date (DD-MM-YYYY):"
    except ValueError:
        return "Invalid date format. Please use DD-MM-YYYY (e.g. 25-03-2026):"

    session["date"] = msg
    session["step"] = "select_slot"

    venue = get_venue_by_id(session["venue_id"])
    slots = venue["slots"]
    slot_list = "\n".join([f"{i+1}️⃣  {s}" for i, s in enumerate(slots)])

    return f"🕐 Available slots for {msg}:\n\n{slot_list}\n\nReply with the slot number"


def handle_select_slot(phone: str, msg: str, session: dict) -> str:
    venue = get_venue_by_id(session["venue_id"])
    slots = venue["slots"]
    try:
        idx = int(msg) - 1
        if idx < 0 or idx >= len(slots):
            raise ValueError
    except ValueError:
        return "Please reply with a valid slot number."

    slot = slots[idx]
    session["slot"] = slot
    session["step"] = "confirm_booking"

    return (
        f"📋 *Booking Summary*\n\n"
        f"🏟️ Venue: {session['venue_name']}\n"
        f"🏅 Sport: {session['sport']}\n"
        f"📅 Date: {session['date']}\n"
        f"🕐 Time: {slot}\n"
        f"💰 Price: ₹{venue['price']}\n\n"
        f"Confirm booking?\n\n"
        f"✅ Reply *yes* to confirm\n"
        f"❌ Reply *no* to cancel"
    )


def handle_confirm_booking(phone: str, msg: str, session: dict) -> str:
    if msg == "yes":
        booking = create_booking(phone, session["venue_id"], session["date"], session["slot"])
        reset_session(phone)
        return (
            f"🎉 *Booking Confirmed!*\n\n"
            f"Your Booking ID: *{booking['id']}*\n"
            f"🏟️ {booking['venue']}\n"
            f"📅 {booking['date']} at {booking['slot']}\n"
            f"💰 ₹{booking['price']}\n\n"
            f"Save your Booking ID for cancellations.\n"
            f"Type *menu* to go back to home."
        )
    elif msg == "no":
        reset_session(phone)
        return "Booking cancelled. Type *menu* to start over."
    else:
        return "Please reply *yes* to confirm or *no* to cancel."


def show_my_bookings(phone: str, session: dict) -> str:
    bookings = get_bookings_by_phone(phone)
    session["step"] = "my_bookings"

    if not bookings:
        reset_session(phone)
        return "You have no bookings yet.\n\nType *menu* to go back."

    lines = ["📋 *Your Bookings:*\n"]
    for b in bookings:
        lines.append(f"🔖 *{b['id']}*\n🏟️ {b['venue']} | 📅 {b['date']} {b['slot']}\n")

    lines.append("Type *menu* to go back.")
    return "\n".join(lines)


def handle_my_bookings_action(phone: str, msg: str, session: dict) -> str:
    reset_session(phone)
    return main_menu()


def handle_cancel_booking(phone: str, msg: str, session: dict) -> str:
    booking_id = msg.upper()
    success = cancel_booking(booking_id, phone)
    reset_session(phone)

    if success:
        return f"✅ Booking *{booking_id}* has been cancelled.\n\nType *menu* to go back."
    else:
        return (
            f"❌ Could not find booking *{booking_id}* linked to your number.\n"
            f"Please check the ID and try again.\n\nType *menu* to go back."
        )
