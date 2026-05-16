import os
import re
import requests

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False
from flask import Flask, jsonify, request
from flask_cors import CORS
from pathlib import Path
from threading import Lock
from uuid import uuid4
from datetime import date, timedelta
import json

try:
    BASE_DIR = Path(__file__).resolve().parent
except NameError:
    BASE_DIR = Path.cwd()

load_dotenv(BASE_DIR / ".env", override=True)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
print("OPENROUTER KEY LOADED:", bool(OPENROUTER_API_KEY), "LEN:", len(OPENROUTER_API_KEY))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

EVENTS_FILE = BASE_DIR / "events.json"
STORE_LOCK = Lock()

MONTH_INDEX = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

DEFAULT_STORE = {
    "initialised": False,
    "seed_source": None,
    "events": []
}

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})


def sample_event(
    event_id,
    title,
    date_text,
    time,
    end_time,
    venue,
    venue_id,
    city,
    event_type,
    description,
    image,
    tickets_sold,
    capacity,
    featured=False,
    last_call=False,
    rating=4.2,
    age_restriction="All ages",
    seat_classes=None,
    seat_pricing=None,
    sound_quality=2,
):
    seat_classes = seat_classes or ["VIP", "Normal"]
    seat_pricing = seat_pricing or {"Normal": 45, "VIP": 110}

    return {
        "id": event_id,
        "title": title,
        "date": date_text,
        "time": time,
        "end_time": end_time,
        "venue": venue,
        "venue_id": venue_id,
        "city": city,
        "type": event_type,
        "description": description,
        "image": image,
        "images": [image],
        "featured_artist_ids": [],
        "age_restriction": age_restriction,
        "tickets_sold": tickets_sold,
        "capacity": capacity,
        "featured": featured,
        "last_call": last_call,
        "accessible_seats": True,
        "review_rating": rating,
        "seat_classes": seat_classes,
        "seat_pricing": seat_pricing,
        "ticket_prices": seat_pricing,
        "seat_layout": None,
        "sound_quality": sound_quality,
        "route_path": f"/o_eventinfo?id={event_id}",
        "creator_user_id": None,
    }


def get_sample_events():
    img_concert = "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?q=80&w=1200&auto=format&fit=crop"
    img_sport = "https://images.unsplash.com/photo-1574629810360-7efbbe195018?q=80&w=1200&auto=format&fit=crop"
    img_movie = "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=1200&auto=format&fit=crop"
    img_show = "https://images.unsplash.com/photo-1518998053901-5348d3961a04?q=80&w=1200&auto=format&fit=crop"
    img_expo = "https://images.unsplash.com/photo-1519167758481-83f550bb49b3?q=80&w=1200&auto=format&fit=crop"
    img_education = "https://images.unsplash.com/photo-1517502884422-41eaead166d4?q=80&w=1200&auto=format&fit=crop"
    img_comedy = "https://images.unsplash.com/photo-1527224857830-43a7acc85260?q=80&w=1200&auto=format&fit=crop"
    img_food = "https://images.unsplash.com/photo-1559339352-11d035aa65de?q=80&w=1200&auto=format&fit=crop"

    return [
        sample_event(
            "event-1",
            "Summer Opening Concert",
            "18 Apr 2026",
            "20:00",
            "23:00",
            "Amphithéâtre de Carthage",
            "venue-8",
            "Tunis",
            "Concerts",
            "A big open-air pop concert featuring live vocals and premium summer crowd atmosphere.",
            img_concert,
            25400,
            30000,
            True,
            False,
            4.5,
            "15+",
        ),
        sample_event(
            "event-41",
            "Ariana Live Concert",
            "25 Apr 2026",
            "20:30",
            "22:30",
            "Pathé Tunis City",
            "venue-5",
            "Ariana",
            "Concerts",
            "A modern indoor concert in Ariana with pop, rap, and live stage visuals.",
            img_concert,
            380,
            450,
            True,
            False,
            4.7,
            "12+",
            ["VIP", "Normal"],
            {"Normal": 38, "VIP": 65},
            3,
        ),
        sample_event(
            "event-42",
            "Ariana Movie Night",
            "26 Apr 2026",
            "19:00",
            "21:00",
            "Pathé Tunis City",
            "venue-5",
            "Ariana",
            "Movies",
            "A premium movie night in Ariana with comfortable cinema seating.",
            img_movie,
            240,
            450,
            False,
            False,
            4.3,
        ),
        sample_event(
            "event-43",
            "Ariana Football Fan Zone",
            "26 Apr 2026",
            "17:00",
            "19:00",
            "Ariana Sports Hall",
            "venue-18",
            "Ariana",
            "Sports",
            "A sports fan-zone event with football screening, chants, and community atmosphere.",
            img_sport,
            180,
            300,
            False,
            True,
            4.2,
            "All ages",
            ["VIP", "Normal"],
            {"Normal": 20, "VIP": 45},
        ),
        sample_event(
            "event-2",
            "Weekend Football Clash",
            "25 Apr 2026",
            "18:00",
            "20:00",
            "Stade Olympique de Radès",
            "venue-9",
            "Ben Arous",
            "Sports",
            "A high-energy football match with strong chants and lively weekend crowd.",
            img_sport,
            52000,
            60000,
            True,
            False,
            4.4,
        ),
        sample_event(
            "event-3",
            "Magic Night",
            "02 May 2026",
            "19:30",
            "21:00",
            "Complexe Culturel de Monastir",
            "venue-1",
            "Monastir",
            "Shows",
            "A family-friendly illusion and magic performance with audience interaction.",
            img_show,
            180,
            350,
            True,
            False,
            4.4,
        ),
        sample_event(
            "event-4",
            "Heritage Fashion Expo",
            "08 May 2026",
            "10:00",
            "18:00",
            "Palais Ennejma Ezzahra",
            "venue-7",
            "Tunis",
            "Exhibitions",
            "A fashion and culture expo with themed booths, exhibitions, and artisan showcases.",
            img_expo,
            210,
            250,
            True,
            False,
            4.0,
            "All ages",
            ["Normal"],
            {"Normal": 25},
            1,
        ),
        sample_event(
            "event-5",
            "Rock & Pop Night",
            "14 May 2026",
            "21:00",
            "23:30",
            "Amphithéâtre de Carthage",
            "venue-8",
            "Tunis",
            "Concerts",
            "A high-energy open-air concert blending pop and rock stage energy.",
            img_concert,
            28700,
            30000,
            False,
            True,
            4.6,
            "15+",
        ),
        sample_event(
            "event-6",
            "Rooftop DJ Set",
            "20 May 2026",
            "22:00",
            "01:00",
            "Dar El Marsa Rooftop Bar",
            "venue-12",
            "Tunis",
            "Shows",
            "A nightlife DJ event with rooftop atmosphere, drinks, modern visuals, and limited tickets.",
            img_concert,
            90,
            120,
            False,
            True,
            4.2,
            "18+",
        ),
        sample_event(
            "event-7",
            "Local Football Derby",
            "27 May 2026",
            "19:00",
            "21:00",
            "Stade Olympique de Sousse",
            "venue-10",
            "Sousse",
            "Sports",
            "A local derby with passionate crowd energy and strong home support.",
            img_sport,
            39600,
            40000,
            True,
            True,
            4.6,
        ),
        sample_event(
            "event-8",
            "Monastir Basketball Derby",
            "03 Jun 2026",
            "17:00",
            "19:00",
            "Salle Couverte Mohamed Mzali",
            "venue-11",
            "Monastir",
            "Sports",
            "An indoor basketball derby in Monastir with strong home crowd energy.",
            img_sport,
            4100,
            5000,
            False,
            False,
            4.6,
            "All ages",
            ["VIP", "Normal"],
            {"Normal": 22, "VIP": 44},
        ),
        sample_event(
            "event-9",
            "Film Premiere Night",
            "09 Jun 2026",
            "19:00",
            "21:00",
            "Pathé Azur City",
            "venue-2",
            "Ben Arous",
            "Movies",
            "A red-carpet style film premiere in a modern multiplex cinema.",
            img_movie,
            360,
            420,
            True,
            False,
            4.3,
            "15+",
        ),
        sample_event(
            "event-10",
            "Electronic Hall Session",
            "15 Jun 2026",
            "19:30",
            "21:30",
            "Théâtre de l’Opéra de Tunis",
            "venue-4",
            "Tunis",
            "Shows",
            "A premium electronic stage evening with immersive visuals and strong live sound.",
            img_show,
            1620,
            1800,
            False,
            False,
            4.4,
            "15+",
        ),
        sample_event(
            "event-11",
            "Startup Summit Tunisia",
            "22 Jun 2026",
            "09:00",
            "17:00",
            "Tunis Marriott Hotel",
            "venue-15",
            "Tunis",
            "Education",
            "A business and innovation summit with talks, startup booths, and networking sessions.",
            img_education,
            540,
            700,
            False,
            False,
            4.2,
        ),
        sample_event(
            "event-12",
            "Karim Ben Amor Comedy Night",
            "30 Jun 2026",
            "20:30",
            "22:00",
            "The Saloon",
            "venue-13",
            "Sousse",
            "Comedy",
            "A small-scale comedy evening in Sousse with intimate seating and sharp crowd work.",
            img_comedy,
            96,
            110,
            False,
            True,
            4.3,
            "18+",
            ["Normal"],
            {"Normal": 30},
        ),
        sample_event(
            "event-13",
            "Carthage Music Festival Night 2",
            "10 Jul 2026",
            "21:00",
            "23:45",
            "Amphithéâtre de Carthage",
            "venue-8",
            "Tunis",
            "Concerts",
            "A major open-air music festival night with headline performers.",
            img_concert,
            28600,
            30000,
            True,
            False,
            4.9,
            "15+",
        ),
        sample_event(
            "event-14",
            "Summer Lifestyle Expo",
            "18 Jul 2026",
            "11:00",
            "18:00",
            "Marina Cap Monastir Appart Hôtel",
            "venue-16",
            "Monastir",
            "Exhibitions",
            "A seaside lifestyle expo with curated stands, local brands, and design showcases.",
            img_expo,
            190,
            240,
            False,
            False,
            4.0,
            "All ages",
            ["Normal"],
            {"Normal": 18},
            1,
        ),
        sample_event(
            "event-23",
            "The Yassines: Midnight Syntax",
            "06 Jun 2026",
            "20:30",
            "22:30",
            "Théâtre de l’Opéra de Tunis",
            "venue-4",
            "Tunis",
            "Concerts",
            "A live duet night built around smooth vocals and polished indoor concert atmosphere.",
            img_concert,
            1240,
            1800,
            True,
            False,
            4.8,
            "12+",
            ["VIP", "Special", "Normal"],
            {"Normal": 48, "Special": 78, "VIP": 115},
            3,
        ),
        sample_event(
            "event-24",
            "The Yassines: Three-Way Static",
            "08 Jun 2026",
            "21:00",
            "23:10",
            "Théâtre municipal de Tunis",
            "venue-3",
            "Tunis",
            "Concerts",
            "A sharper late-evening live set mixing melodic hooks and rap sections.",
            img_concert,
            990,
            1350,
            True,
            False,
            4.9,
            "14+",
            ["VIP", "Special", "Normal"],
            {"Normal": 55, "Special": 89, "VIP": 135},
            3,
        ),
        sample_event(
            "event-25",
            "Slaymiya Under the Stars",
            "10 Jun 2026",
            "21:00",
            "23:00",
            "Palais Ennejma Ezzahra",
            "venue-7",
            "Tunis",
            "Cultural Nights",
            "A traditional Tunisian spiritual music evening with calm seated audience.",
            img_concert,
            188,
            250,
            True,
            True,
            4.9,
            "All ages",
            ["VIP", "Normal"],
            {"Normal": 42, "VIP": 68},
            2,
        ),
        sample_event(
            "event-26",
            "Medina Rhythm Showcase",
            "11 Jun 2026",
            "19:30",
            "21:15",
            "Complexe Culturel de Monastir",
            "venue-1",
            "Monastir",
            "Shows",
            "A staged variety performance blending dance, movement, and crowd interaction.",
            img_show,
            262,
            350,
            False,
            False,
            4.4,
            "12+",
            ["VIP", "Normal"],
            {"Normal": 39, "VIP": 64},
            3,
        ),
        sample_event(
            "event-27",
            "Spoken Stories at Sunset",
            "12 Jun 2026",
            "18:30",
            "20:30",
            "Tunis Marriott Hotel",
            "venue-15",
            "Tunis",
            "Education",
            "A curated evening of short talks, storytelling, and public speaking.",
            img_education,
            401,
            700,
            False,
            False,
            4.5,
            "All ages",
            ["VIP", "Special", "Normal"],
            {"Normal": 34, "Special": 55, "VIP": 80},
            1,
        ),
        sample_event(
            "event-28",
            "Product Builders Forum",
            "13 Jun 2026",
            "09:30",
            "16:30",
            "Sousse Palace Hotel & Spa",
            "venue-17",
            "Sousse",
            "Education",
            "A one-day forum for student founders, builders, and product-minded guests.",
            img_education,
            286,
            500,
            False,
            False,
            4.3,
            "All ages",
            ["VIP", "Special", "Normal"],
            {"Normal": 30, "Special": 52, "VIP": 76},
            1,
        ),
        sample_event(
            "event-29",
            "Coastal Football Showcase",
            "14 Jun 2026",
            "18:00",
            "20:00",
            "Stade Olympique de Radès",
            "venue-9",
            "Ben Arous",
            "Sports",
            "A high-attendance football night with chants and big stadium crowd.",
            img_sport,
            33600,
            60000,
            False,
            False,
            4.6,
            "All ages",
            ["VIP", "Special", "Normal"],
            {"Normal": 25, "Special": 40, "VIP": 70},
            2,
        ),
        sample_event(
            "event-31",
            "Anime Movie Marathon",
            "18 Jun 2026",
            "16:00",
            "22:30",
            "Pathé Tunis City",
            "venue-5",
            "Ariana",
            "Movies",
            "A multi-film anime screening block with themed breaks and young fan crowd.",
            img_movie,
            298,
            450,
            False,
            False,
            4.5,
            "13+",
            ["VIP", "Normal"],
            {"Normal": 32, "VIP": 49},
        ),
        sample_event(
            "event-32",
            "Midnight Horror Premiere",
            "19 Jun 2026",
            "21:30",
            "23:30",
            "Pathé Azur City",
            "venue-2",
            "Ben Arous",
            "Movies",
            "A late-night horror premiere with a full cinema crowd and dark visuals.",
            img_movie,
            365,
            420,
            True,
            True,
            4.6,
            "16+",
            ["VIP", "Normal"],
            {"Normal": 36, "VIP": 58},
        ),
        sample_event(
            "event-34",
            "Taste of Tunis Night",
            "23 Jun 2026",
            "18:30",
            "22:00",
            "Marina Cap Monastir Appart Hôtel",
            "venue-16",
            "Monastir",
            "Food & Culture",
            "A social evening around Tunisian flavors, soft live ambiance, and marina crowd.",
            img_food,
            166,
            240,
            False,
            False,
            4.1,
            "All ages",
            ["VIP", "Normal"],
            {"Normal": 28, "VIP": 47},
            1,
        ),
    ]


def save_store(store):
    with EVENTS_FILE.open("w", encoding="utf-8") as file:
        json.dump(store, file, ensure_ascii=False, indent=2)


def ensure_store_file_exists():
    if not EVENTS_FILE.exists():
        save_store({
            "initialised": True,
            "seed_source": "backend_sample_events",
            "events": get_sample_events()
        })


def load_store():
    ensure_store_file_exists()

    try:
        with EVENTS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        data = {
            "initialised": True,
            "seed_source": "backend_sample_events",
            "events": get_sample_events()
        }
        save_store(data)
        return data

    if not isinstance(data, dict):
        data = DEFAULT_STORE.copy()

    if not isinstance(data.get("events"), list):
        data["events"] = []

    if len(data["events"]) == 0:
        data["events"] = get_sample_events()
        data["initialised"] = True
        data["seed_source"] = "backend_sample_events_auto_seed"
        save_store(data)

    if "initialised" not in data:
        data["initialised"] = len(data.get("events", [])) > 0

    if "seed_source" not in data:
        data["seed_source"] = None

    return data


def normalize_event_object(event_data):
    if not isinstance(event_data, dict):
        return None

    event = dict(event_data)
    if not event.get("id"):
        event["id"] = str(uuid4())

    return event


def normalize_event_list(raw_events):
    if not isinstance(raw_events, list):
        return []

    result = {}
    for raw_event in raw_events:
        event = normalize_event_object(raw_event)
        if event:
            result[str(event["id"])] = event

    return list(result.values())


def find_event_index(events, event_id):
    for index, event in enumerate(events):
        if str(event.get("id")) == str(event_id):
            return index
    return -1


def normalize_text(value):
    return " ".join(str(value or "").strip().lower().split())


def parse_request_iso_date(value):
    text = str(value or "").strip()
    if not text:
        return None

    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def parse_event_date(value):
    text = str(value or "").strip()
    if not text:
        return None

    try:
        return date.fromisoformat(text)
    except ValueError:
        pass

    parts = text.replace(",", " ").split()
    if len(parts) < 3:
        return None

    try:
        day = int(parts[0])
        month = MONTH_INDEX.get(parts[1][:3].lower())
        year = int(parts[2])
        if not month:
            return None
        return date(year, month, day)
    except (ValueError, TypeError):
        return None


def enumerate_date_range(start_date, end_date):
    if not start_date or not end_date or end_date < start_date:
        return []

    dates = []
    current = start_date

    while current <= end_date:
        dates.append(current.isoformat())
        current += timedelta(days=1)

    return dates


def get_available_categories(events):
    return sorted({
        str(event.get("type", "")).strip()
        for event in events
        if str(event.get("type", "")).strip()
    })


def get_available_locations(events):
    return sorted({
        str(event.get("city", "")).strip()
        for event in events
        if str(event.get("city", "")).strip()
    })


def get_event_seats_left(event):
    try:
        return max(0, int(event.get("capacity", 0) or 0) - int(event.get("tickets_sold", 0) or 0))
    except (ValueError, TypeError):
        return 0


def build_missing_fields(payload):
    missing = []

    if not str(payload.get("bundle_name", "")).strip():
        missing.append("bundle_name")

    categories = payload.get("categories", [])
    if not isinstance(categories, list) or not [c for c in categories if str(c).strip()]:
        missing.append("categories")

    date_mode = str(payload.get("date_mode", "")).strip().lower()
    if date_mode not in {"range", "exact"}:
        missing.append("date_mode")
    elif date_mode == "range":
        if not parse_request_iso_date(payload.get("start_date")) or not parse_request_iso_date(payload.get("end_date")):
            missing.append("date_range")
    elif date_mode == "exact":
        exact_dates = payload.get("exact_dates", [])
        if not isinstance(exact_dates, list) or not [d for d in exact_dates if parse_request_iso_date(d)]:
            missing.append("exact_dates")

    return missing


def build_missing_field_question(missing):
    questions = {
        "bundle_name": "What should I call this bundle?",
        "categories": "What kind of events do you want in this bundle?",
        "date_mode": "Do you want exact dates or a date range?",
        "date_range": "Please give me a valid start date and end date.",
        "exact_dates": "Please give me at least one valid exact date.",
    }
    return questions.get(missing[0], "Please complete the missing information.") if missing else ""


def normalize_bundle_request(payload, categories_available, locations_available):
    date_mode = str(payload.get("date_mode", "")).strip().lower()
    start = parse_request_iso_date(payload.get("start_date"))
    end = parse_request_iso_date(payload.get("end_date"))

    selected_dates = []
    if date_mode == "range":
        selected_dates = enumerate_date_range(start, end)
    elif date_mode == "exact":
        selected_dates = sorted({
            parsed.isoformat()
            for parsed in [parse_request_iso_date(item) for item in payload.get("exact_dates", [])]
            if parsed
        })

    normalized_categories = {
        normalize_text(category): category
        for category in categories_available
    }

    categories = []
    for category in payload.get("categories", []):
        key = normalize_text(category)
        if key in normalized_categories:
            categories.append(normalized_categories[key])

    categories = list(dict.fromkeys(categories))

    location = str(payload.get("location", "")).strip()
    normalized_locations = {
        normalize_text(location_name): location_name
        for location_name in locations_available
    }

    location = normalized_locations.get(normalize_text(location), location) if location else ""

    return {
        "bundle_name": str(payload.get("bundle_name", "")).strip(),
        "note": str(payload.get("note", "")).strip(),
        "date_mode": date_mode,
        "start_date": start.isoformat() if start else "",
        "end_date": end.isoformat() if end else "",
        "exact_dates": selected_dates if date_mode == "exact" else [],
        "selected_dates": selected_dates,
        "total_days": len(selected_dates),
        "categories": categories,
        "location": location,
    }


def validate_bundle_request(normalized):
    errors = []

    if normalized["total_days"] == 0:
        errors.append("Please select at least one valid date.")

    if normalized["total_days"] > 7:
        errors.append("The bundle can cover at most 7 total days.")

    if normalized["date_mode"] == "range":
        if normalized["start_date"] and normalized["end_date"] and normalized["end_date"] < normalized["start_date"]:
            errors.append("The end date must be after the start date.")

    return errors


def event_matches_request(event, normalized):
    event_date = parse_event_date(event.get("date"))
    if not event_date:
        return False

    if event_date.isoformat() not in normalized["selected_dates"]:
        return False

    if normalized["categories"] and str(event.get("type", "")).strip() not in normalized["categories"]:
        return False

    if normalized["location"] and normalize_text(event.get("city")) != normalize_text(normalized["location"]):
        return False

    return True


def event_summary(event):
    parsed = parse_event_date(event.get("date"))

    return {
        "id": event.get("id"),
        "title": event.get("title"),
        "date": event.get("date"),
        "date_iso": parsed.isoformat() if parsed else "",
        "time": event.get("time", ""),
        "end_time": event.get("end_time", ""),
        "city": event.get("city", ""),
        "venue": event.get("venue", ""),
        "type": event.get("type", ""),
        "image": event.get("image", ""),
        "route_path": event.get("route_path", ""),
        "review_rating": event.get("review_rating", 0),
        "featured": bool(event.get("featured")),
        "last_call": bool(event.get("last_call")),
        "seats_left": get_event_seats_left(event),
    }


def build_bundle_suggestions(events, normalized):
    def rating_sort(event):
        return (
            0 if bool(event.get("featured")) else 1,
            0 if bool(event.get("last_call")) else 1,
            -float(event.get("review_rating", 0) or 0),
            parse_event_date(event.get("date")) or date.max,
        )

    sorted_events = sorted(events, key=rating_sort)

    variants = [
        ("Best Match", sorted_events[:4], "Best rated and most relevant events for your filters."),
        (
            "Balanced Match",
            sorted(events, key=lambda e: parse_event_date(e.get("date")) or date.max)[:4],
            "Balanced date order for your selected days."
        ),
        (
            "Popular Match",
            sorted(events, key=lambda e: -int(e.get("tickets_sold", 0) or 0))[:4],
            "Popular events with stronger demand."
        ),
    ]

    suggestions = []
    seen = set()

    for index, (name, selected_events, description) in enumerate(variants, start=1):
        ids = tuple(event.get("id") for event in selected_events if event.get("id"))
        if not ids or ids in seen:
            continue

        seen.add(ids)
        summaries = [event_summary(event) for event in selected_events]

        suggestions.append({
            "id": f"bundle-option-{index}",
            "title": f"{normalized['bundle_name']} — {name}",
            "description": description,
            "bundle_name": normalized["bundle_name"],
            "note": normalized["note"],
            "criteria": {
                "date_mode": normalized["date_mode"],
                "start_date": normalized["start_date"],
                "end_date": normalized["end_date"],
                "exact_dates": normalized["exact_dates"],
                "categories": normalized["categories"],
                "location": normalized["location"],
            },
            "selected_event_ids": [event["id"] for event in summaries],
            "selected_events": summaries,
            "summary": {
                "total_events": len(summaries),
                "categories": sorted({event["type"] for event in summaries if event["type"]}),
                "locations": sorted({event["city"] for event in summaries if event["city"]}),
                "dates": sorted({event["date_iso"] for event in summaries if event["date_iso"]}),
            },
        })

    return suggestions[:3]


@app.get("/api/health")
def health_check():
    return jsonify({"status": "ok", "message": "Backend is running."})


@app.get("/api/is-initialised")
def is_initialised():
    store = load_store()
    return jsonify({
        "initialised": bool(store.get("initialised")) or len(store.get("events", [])) > 0,
        "event_count": len(store.get("events", []))
    })


@app.get("/api/events")
def get_all_events():
    store = load_store()
    return jsonify({
        "events": store["events"],
        "count": len(store["events"])
    })


@app.get("/api/events/<event_id>")
def get_one_event(event_id):
    store = load_store()

    for event in store["events"]:
        if str(event.get("id")) == str(event_id):
            return jsonify({"event": event})

    return jsonify({"error": "Event not found."}), 404


@app.post("/api/sync-events")
def sync_events():
    payload = request.get_json(silent=True)

    if isinstance(payload, list):
        events = payload
        source = "frontend_sync"
    elif isinstance(payload, dict) and isinstance(payload.get("events"), list):
        events = payload["events"]
        source = payload.get("source", "frontend_sync")
    else:
        return jsonify({"error": "Request body must be an array or an object with an events array."}), 400

    normalized_events = normalize_event_list(events)

    if len(normalized_events) == 0:
        normalized_events = get_sample_events()
        source = "backend_sample_events_fallback_after_empty_sync"

    with STORE_LOCK:
        store = {
            "initialised": True,
            "seed_source": source,
            "events": normalized_events,
        }
        save_store(store)

    return jsonify({
        "message": "Events mirror synced successfully.",
        "new_count": len(normalized_events),
        "initialised": True
    })


@app.post("/api/events")
def create_event():
    payload = request.get_json(silent=True)
    event = normalize_event_object(payload)

    if not event:
        return jsonify({"error": "Request body must be a JSON event object."}), 400

    with STORE_LOCK:
        store = load_store()
        if find_event_index(store["events"], event["id"]) != -1:
            return jsonify({"error": "An event with this id already exists."}), 409

        store["events"].append(event)
        store["initialised"] = True
        save_store(store)

    return jsonify({"message": "Event created successfully.", "event": event}), 201


@app.put("/api/events/<event_id>")
@app.patch("/api/events/<event_id>")
def update_event(event_id):
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    with STORE_LOCK:
        store = load_store()
        index = find_event_index(store["events"], event_id)

        if index == -1:
            return jsonify({"error": "Event not found."}), 404

        current = dict(store["events"][index])
        updated = {**current, **payload, "id": current["id"]}
        store["events"][index] = updated
        save_store(store)

    return jsonify({"message": "Event updated successfully.", "event": updated})


@app.delete("/api/events/<event_id>")
def delete_event(event_id):
    with STORE_LOCK:
        store = load_store()
        index = find_event_index(store["events"], event_id)

        if index == -1:
            return jsonify({"error": "Event not found."}), 404

        deleted = store["events"].pop(index)
        save_store(store)

    return jsonify({"message": "Event deleted successfully.", "event": deleted})


@app.get("/api/ai/bundle-options")
def get_ai_bundle_options():
    store = load_store()
    events = store.get("events", [])

    return jsonify({
        "categories": get_available_categories(events),
        "locations": get_available_locations(events),
        "event_count": len(events)
    })


@app.post("/api/ai/bundle-suggestions")
def get_ai_bundle_suggestions():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    store = load_store()
    events = store.get("events", [])

    missing = build_missing_fields(payload)
    if missing:
        return jsonify({
            "missing_fields": missing,
            "question": build_missing_field_question(missing),
            "errors": [],
            "bundles": []
        })

    categories_available = get_available_categories(events)
    locations_available = get_available_locations(events)

    normalized = normalize_bundle_request(payload, categories_available, locations_available)
    errors = validate_bundle_request(normalized)

    if errors:
        return jsonify({
            "missing_fields": [],
            "errors": errors,
            "bundles": []
        })

    matching_events = [
        event for event in events
        if event_matches_request(event, normalized)
    ]

    if not matching_events:
        return jsonify({
            "missing_fields": [],
            "errors": [],
            "bundles": [],
            "message": "No event available that matches the filters you selected. Try changing the date, category, or location."
        })

    suggestions = build_bundle_suggestions(matching_events, normalized)

    return jsonify({
        "missing_fields": [],
        "errors": [],
        "bundles": suggestions,
        "message": f"{len(suggestions)} bundle suggestion(s) created successfully."
    })

def event_ai_payload(event):
    parsed = parse_event_date(event.get("date"))

    return {
        "id": event.get("id"),
        "title": event.get("title", ""),
        "date": event.get("date", ""),
        "date_iso": parsed.isoformat() if parsed else "",
        "time": event.get("time", ""),
        "end_time": event.get("end_time", ""),
        "city": event.get("city", ""),
        "venue": event.get("venue", ""),
        "type": event.get("type", ""),
        "description": event.get("description", ""),
        "review_rating": event.get("review_rating", 0),
        "featured": bool(event.get("featured")),
        "last_call": bool(event.get("last_call")),
        "tickets_sold": event.get("tickets_sold", 0),
        "capacity": event.get("capacity", 0),
        "seats_left": get_event_seats_left(event),
    }


def extract_json_from_llm_text(text):
    text = str(text or "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    text = re.sub(r"^```(?:json)?", "", text.strip(), flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text.strip()).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    first = text.find("{")
    last = text.rfind("}")

    if first != -1 and last != -1 and last > first:
        candidate = text[first:last + 1]
        return json.loads(candidate)

    raise ValueError("The AI response was not valid JSON.")


def build_openrouter_messages(message, history, events):
    safe_history = history if isinstance(history, list) else []
    safe_history = safe_history[-8:]

    available_events = [event_ai_payload(event) for event in events]

    system_prompt = f"""
You are Blassti AI, a professional event bundle planner for a Vue/Vuetify ticketing app.

Your job:
- Understand natural language from the user.
- User can write in English, French, Arabic, or mixed language.
- Create 2 or 3 bundle suggestions using ONLY the available event IDs.
- A bundle can cover maximum 7 distinct days.
- Prefer matching the user's category, city, date, mood, and budget if mentioned.
- If the user gives vague text, infer the best possible bundle from available events.
- If impossible, ask one short clarification question.

Today is {date.today().isoformat()}.

Available events:
{json.dumps(available_events, ensure_ascii=False)}

Return ONLY valid JSON, no markdown.

Required JSON schema:
{{
  "reply": "short helpful message to show to user",
  "needs_more_info": false,
  "question": "",
  "missing_fields": [],
  "errors": [],
  "bundles": [
    {{
      "id": "ai-bundle-option-1",
      "title": "Bundle title",
      "description": "Why this bundle is good",
      "bundle_name": "Short bundle name",
      "note": "Optional note",
      "criteria": {{
        "date_mode": "exact",
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD",
        "exact_dates": ["YYYY-MM-DD"],
        "categories": ["Concerts"],
        "location": "Tunis"
      }},
      "selected_event_ids": ["event-1", "event-2"]
    }}
  ]
}}

Important rules:
- selected_event_ids must contain only real IDs from available events.
- Never invent events.
- Never invent dates.
- selected_event_ids should match the user's request.
- If the user asks for "weekend", select Saturday/Sunday events if available.
- If the user asks for "cinema/movie", use Movies.
- If the user asks for "football/match/sport", use Sports.
- If the user asks for "music/concert/festival", use Concerts.
- If no date is given, choose the best matching upcoming available events.
- Keep each bundle between 1 and 4 events.
"""

    messages = [{"role": "system", "content": system_prompt}]

    for item in safe_history:
        role = item.get("role")
        content = str(item.get("content", "")).strip()

        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": message})

    return messages


def call_openrouter_for_bundle(message, history, events):
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is missing. Add it to backend/.env")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "Blassti Bundle AI",
    }

    payload = {
    "model": OPENROUTER_MODEL,
    "messages": build_openrouter_messages(message, history, events),
    "temperature": 0.1,
    "max_tokens": 2500,
    "response_format": {
        "type": "json_object"
    },
}

    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=35,
    )

    if response.status_code >= 400:
        raise RuntimeError(f"OpenRouter error {response.status_code}: {response.text}")

    data = response.json()
    content = data["choices"][0]["message"]["content"]

    return extract_json_from_llm_text(content)


def normalize_llm_bundle_response(ai_data, events):
    if not isinstance(ai_data, dict):
        ai_data = {}

    event_by_id = {
        str(event.get("id")): event
        for event in events
        if event.get("id")
    }

    bundles = []
    raw_bundles = ai_data.get("bundles", [])

    if not isinstance(raw_bundles, list):
        raw_bundles = []

    for index, raw_bundle in enumerate(raw_bundles, start=1):
        if not isinstance(raw_bundle, dict):
            continue

        raw_ids = raw_bundle.get("selected_event_ids", [])

        if not isinstance(raw_ids, list):
            raw_ids = []

        selected_ids = []
        for event_id in raw_ids:
            event_id = str(event_id)
            if event_id in event_by_id and event_id not in selected_ids:
                selected_ids.append(event_id)

        selected_events = [event_summary(event_by_id[event_id]) for event_id in selected_ids]
        selected_dates = sorted({
            event.get("date_iso")
            for event in selected_events
            if event.get("date_iso")
        })

        if len(selected_dates) > 7:
            allowed_dates = set(selected_dates[:7])
            selected_events = [
                event for event in selected_events
                if event.get("date_iso") in allowed_dates
            ]
            selected_ids = [event.get("id") for event in selected_events]
            selected_dates = sorted(allowed_dates)

        if not selected_events:
            continue

        categories = sorted({
            event.get("type")
            for event in selected_events
            if event.get("type")
        })

        locations = sorted({
            event.get("city")
            for event in selected_events
            if event.get("city")
        })

        criteria = raw_bundle.get("criteria", {})
        if not isinstance(criteria, dict):
            criteria = {}

        bundle_name = str(
            raw_bundle.get("bundle_name")
            or raw_bundle.get("title")
            or f"AI Bundle {index}"
        ).strip()

        title = str(
            raw_bundle.get("title")
            or f"{bundle_name} — AI Match"
        ).strip()

        description = str(
            raw_bundle.get("description")
            or "AI selected these events because they best match your request."
        ).strip()

        bundles.append({
            "id": str(raw_bundle.get("id") or f"ai-bundle-option-{index}"),
            "title": title,
            "description": description,
            "bundle_name": bundle_name,
            "note": str(raw_bundle.get("note") or "").strip(),
            "criteria": {
                "date_mode": "exact",
                "start_date": selected_dates[0] if selected_dates else "",
                "end_date": selected_dates[-1] if selected_dates else "",
                "exact_dates": selected_dates,
                "categories": categories,
                "location": locations[0] if len(locations) == 1 else "",
            },
            "selected_event_ids": selected_ids,
            "selected_events": selected_events,
            "summary": {
                "total_events": len(selected_events),
                "categories": categories,
                "locations": locations,
                "dates": selected_dates,
            },
        })

    return {
        "reply": str(ai_data.get("reply") or "").strip(),
        "needs_more_info": bool(ai_data.get("needs_more_info")) and not bundles,
        "question": str(ai_data.get("question") or "").strip(),
        "missing_fields": ai_data.get("missing_fields", []) if isinstance(ai_data.get("missing_fields", []), list) else [],
        "errors": ai_data.get("errors", []) if isinstance(ai_data.get("errors", []), list) else [],
        "bundles": bundles[:3],
    }


@app.post("/api/ai/llm-bundle-suggestions")
def get_llm_bundle_suggestions():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    message = str(payload.get("message", "")).strip()
    history = payload.get("history", [])

    if not message:
        return jsonify({
            "reply": "Tell me what kind of bundle you want.",
            "needs_more_info": True,
            "question": "What kind of event bundle do you want?",
            "missing_fields": ["message"],
            "errors": [],
            "bundles": []
        }), 400

    store = load_store()
    events = store.get("events", [])

    try:
        ai_data = call_openrouter_for_bundle(message, history, events)
        normalized = normalize_llm_bundle_response(ai_data, events)

        if not normalized["reply"]:
            if normalized["bundles"]:
                normalized["reply"] = f"I created {len(normalized['bundles'])} smart bundle suggestion(s) for you."
            else:
                normalized["reply"] = normalized["question"] or "I need a little more information."

        return jsonify(normalized)

    except Exception as error:
        return jsonify({
            "reply": "The AI service could not create a bundle right now.",
            "needs_more_info": False,
            "question": "",
            "missing_fields": [],
            "errors": [str(error)],
            "bundles": []
        }), 503
if __name__ == "__main__":
    ensure_store_file_exists()
    app.run(host="0.0.0.0", port=5000, debug=True)