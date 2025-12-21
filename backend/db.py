import sqlite3
from pathlib import Path
from typing import Optional

from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "triplogger.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=20.0)
    conn.row_factory = sqlite3.Row
    # Ensure WAL mode is disabled for better compatibility across systems
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("PRAGMA synchronous=FULL")
    return conn



def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            budget REAL NOT NULL,
            rating REAL NOT NULL CHECK (rating >= 0 AND rating <= 5),
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS destinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            country TEXT NOT NULL,
            avg_budget REAL NOT NULL,
            avg_rating REAL NOT NULL,
            popularity INTEGER DEFAULT 0,
            description TEXT
        )
        """
    )
    _ensure_user_id_column(cur)
    conn.commit()
    _seed_demo_user(conn)
    _seed_destinations(conn)
    conn.close()


def _ensure_user_id_column(cur):
    # For existing DBs without user_id, add it so auth works.
    cur.execute("PRAGMA table_info(trips)")
    cols = [row[1] for row in cur.fetchall()]
    if "user_id" not in cols:
        cur.execute("ALTER TABLE trips ADD COLUMN user_id INTEGER")


def _seed_demo_user(conn):
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = ?", ("demo",))
    if cur.fetchone():
        return
    cur.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("demo", generate_password_hash("demo123")),
    )
    conn.commit()


def _seed_destinations(conn):
    """Seed the destinations table with 150 popular cities worldwide."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as count FROM destinations")
    if cur.fetchone()["count"] > 0:
        return  # Already seeded
    
    destinations = [
        # Europe - Ultra Luxury (High budget, high rating)
        ("Paris", "France", 5500, 4.9, 100, "City of Light - iconic monuments and cuisine"),
        ("London", "United Kingdom", 5800, 4.9, 95, "Historic capital with world-class museums"),
        ("Rome", "Italy", 5200, 4.9, 98, "Ancient history and Renaissance art"),
        ("Barcelona", "Spain", 4800, 4.9, 90, "Beach city with Gaudí architecture"),
        ("Venice", "Italy", 6500, 4.9, 92, "Romantic canals and historic architecture"),
        ("Florence", "Italy", 4500, 4.9, 89, "Renaissance art and Tuscan wine"),
        ("Vienna", "Austria", 5000, 4.8, 87, "Imperial palaces and classical music"),
        
        # Europe - Premium (Mid-high budget, high rating)
        ("Amsterdam", "Netherlands", 4200, 4.8, 88, "Canals, cycling, and vibrant culture"),
        ("Berlin", "Germany", 3500, 4.7, 85, "History, art, and innovative nightlife"),
        ("Prague", "Czech Republic", 2200, 4.7, 82, "Medieval charm and affordable luxury"),
        ("Budapest", "Hungary", 2400, 4.7, 83, "Thermal baths and Danube beauty"),
        ("Edinburgh", "United Kingdom", 4000, 4.7, 84, "Medieval castle and Scottish culture"),
        ("Lisbon", "Portugal", 2800, 4.6, 81, "Coastal charm with historic tiles"),
        ("Dublin", "Ireland", 3200, 4.6, 79, "Literary heritage and lively pubs"),
        ("Stockholm", "Sweden", 4500, 4.6, 86, "Island city with Nordic design"),
        ("Copenhagen", "Denmark", 4200, 4.6, 82, "Design capital with hygge culture"),
        ("Krakow", "Poland", 1800, 4.7, 78, "Medieval old town and Jewish quarter"),
        ("Seville", "Spain", 2200, 4.7, 80, "Flamenco, tapas, and Moorish heritage"),
        ("Milan", "Italy", 4600, 4.6, 78, "Fashion capital and Duomo cathedral"),
        ("Zurich", "Switzerland", 6000, 4.7, 81, "Luxury and Alpine views"),
        ("Geneva", "Switzerland", 5800, 4.6, 79, "International hub with lake views"),
        ("Naples", "Italy", 1800, 4.4, 74, "Pizza, passion, and historic streets"),
        
        # Asia - Ultra Luxury (High budget, high rating)
        ("Tokyo", "Japan", 6800, 4.8, 95, "Modern metropolis with ancient temples"),
        ("Singapore", "Singapore", 5500, 4.8, 88, "Ultra-modern city-state with multicultural blend"),
        ("Hong Kong", "Hong Kong", 6000, 4.8, 89, "Vertical city with stunning harbor"),
        ("Bali", "Indonesia", 3200, 4.9, 91, "Tropical paradise with Hindu temples"),
        
        # Asia - Premium (Mid-high budget, high rating)
        ("Seoul", "South Korea", 3800, 4.8, 86, "K-pop culture and tech innovation"),
        ("Bangkok", "Thailand", 2600, 4.8, 92, "Bustling streets, temples, and street food"),
        ("Siem Reap", "Cambodia", 1600, 4.8, 87, "Angkor temples and local culture"),
        ("Hanoi", "Vietnam", 1400, 4.7, 84, "Historic streets and French colonial charm"),
        
        # Asia - Mid-range (Budget-friendly, solid rating)
        ("Ho Chi Minh City", "Vietnam", 1500, 4.6, 83, "Bustling energy and street markets"),
        ("Phuket", "Thailand", 2000, 4.7, 85, "Beach resort with vibrant nightlife"),
        ("Chiang Mai", "Thailand", 1300, 4.8, 81, "Temples and trekking in the mountains"),
        ("Manila", "Philippines", 1200, 4.3, 72, "Chaotic energy and beach nearby"),
        ("Kuala Lumpur", "Malaysia", 1800, 4.6, 80, "Twin towers and colonial heritage"),
        ("Jaipur", "India", 1400, 4.6, 78, "Pink city with majestic forts"),
        ("Agra", "India", 1300, 4.9, 80, "Taj Mahal and romantic sunsets"),
        ("Delhi", "India", 1200, 4.4, 74, "Chaotic capital with Mughal architecture"),
        ("Goa", "India", 1500, 4.7, 82, "Beaches, churches, and Portuguese heritage"),
        ("Darjeeling", "India", 1200, 4.7, 75, "Tea plantations and Himalayan views"),
        ("Kathmandu", "Nepal", 1100, 4.7, 79, "Mountain temples and spiritual energy"),
        ("Pokhara", "Nepal", 900, 4.8, 76, "Lakes and Annapurna trekking base"),
        
        # Asia - Budget (Low budget, moderate rating)
        ("Yangon", "Myanmar", 1000, 4.4, 70, "Golden pagodas and colonial streets"),
        ("Phnom Penh", "Cambodia", 1100, 4.2, 68, "Historic temples and riverside charm"),
        ("Islamabad", "Pakistan", 1000, 4.4, 68, "Mountain-surrounded capital"),
        ("Lahore", "Pakistan", 950, 4.3, 70, "Mughal gardens and street food"),
        
        # Middle East - Premium
        ("Dubai", "United Arab Emirates", 5500, 4.7, 85, "Luxury shopping and desert safaris"),
        ("Abu Dhabi", "United Arab Emirates", 5200, 4.6, 81, "Modern museums and camel racing"),
        ("Jerusalem", "Israel", 3000, 4.7, 82, "Holy sites and historical significance"),
        ("Petra", "Jordan", 2400, 4.9, 84, "Rose-colored ancient city carved in stone"),
        
        # Middle East - Mid-range
        ("Tel Aviv", "Israel", 3800, 4.6, 78, "Beaches and vibrant nightlife"),
        ("Amman", "Jordan", 1800, 4.5, 72, "Ancient Roman ruins and hospitality"),
        
        # Americas - Ultra Luxury (High budget, high rating)
        ("New York City", "USA", 6500, 4.8, 96, "The city that never sleeps"),
        ("San Francisco", "USA", 6000, 4.7, 87, "Golden Gate and tech culture"),
        
        # Americas - Premium (Mid-high budget, high rating)
        ("Los Angeles", "USA", 5200, 4.6, 85, "Beaches, entertainment, and endless sun"),
        ("Miami", "USA", 4800, 4.6, 84, "Beaches, art deco, and Cuban culture"),
        ("Las Vegas", "USA", 4200, 4.7, 88, "Casinos, shows, and desert nightlife"),
        ("New Orleans", "USA", 3200, 4.8, 86, "Jazz, Creole food, and vibrant culture"),
        ("Chicago", "USA", 3600, 4.7, 83, "Architecture, deep dish pizza, and museums"),
        ("Boston", "USA", 3800, 4.6, 79, "Historic Revolutionary War sites"),
        ("Washington DC", "USA", 3400, 4.7, 81, "Monuments, museums, and politics"),
        ("Vancouver", "Canada", 4500, 4.7, 84, "Mountains, ocean, and cosmopolitan culture"),
        ("Montreal", "Canada", 3200, 4.7, 82, "French flair and vibrant nightlife"),
        ("Rio de Janeiro", "Brazil", 3600, 4.7, 89, "Christ the Redeemer and Copacabana"),
        ("Buenos Aires", "Argentina", 3000, 4.8, 88, "Tango, steak, and European elegance"),
        ("Lima", "Peru", 2600, 4.7, 84, "Culinary capital with coastal views"),
        ("Cusco", "Peru", 2200, 4.8, 88, "Gateway to Machu Picchu and Incan history"),
        ("Machu Picchu", "Peru", 2500, 4.9, 90, "Iconic Incan citadel in the clouds"),
        
        # Americas - Mid-range (Budget-friendly, solid rating)
        ("Seattle", "USA", 3400, 4.6, 78, "Coffee, tech, and mountain views"),
        ("Portland", "USA", 2800, 4.6, 77, "Quirky culture and food scene"),
        ("Denver", "USA", 2600, 4.5, 76, "Mile-high city with Rocky Mountain access"),
        ("Austin", "USA", 2900, 4.7, 80, "Live music and tech startup culture"),
        ("Nashville", "USA", 2400, 4.6, 75, "Country music capital"),
        ("Toronto", "Canada", 3800, 4.6, 81, "Multicultural Canadian metropolis"),
        ("Cancun", "Mexico", 3200, 4.6, 86, "Beach resort with Mayan ruins nearby"),
        ("Playa del Carmen", "Mexico", 3000, 4.5, 82, "Caribbean beaches and cenotes"),
        ("Puerto Vallarta", "Mexico", 2800, 4.6, 80, "Romantic beach town and nightlife"),
        ("Mexico City", "Mexico", 2400, 4.7, 85, "Ancient pyramids and street art"),
        ("San Juan", "Puerto Rico", 3400, 4.6, 81, "Caribbean island with colonial charm"),
        ("Havana", "Cuba", 2200, 4.8, 86, "Classic cars and Caribbean nostalgia"),
        ("Salvador", "Brazil", 2000, 4.7, 82, "Bahian culture and beach vibes"),
        ("Bogota", "Colombia", 2100, 4.6, 77, "Mountain city with art and culture"),
        ("Cartagena", "Colombia", 2400, 4.8, 83, "Walled colonial city on Caribbean"),
        
        # Americas - Budget (Low budget, moderate rating)
        ("Oaxaca", "Mexico", 1500, 4.8, 81, "Indigenous culture and colorful markets"),
        ("Guatemala City", "Guatemala", 1200, 4.3, 68, "Gateway to Mayan wonders"),
        ("Antigua", "Guatemala", 1300, 4.8, 79, "Colorful colonial architecture"),
        ("San Jose", "Costa Rica", 2000, 4.6, 80, "Central valley and volcanic landscapes"),
        ("Panama City", "Panama", 1700, 4.4, 73, "Canal engineering and tropical vibes"),
        ("Belize City", "Belize", 1600, 4.4, 72, "Caribbean vibes and Mayan sites"),
        ("Quito", "Ecuador", 1600, 4.6, 76, "On the equator with mountain views"),
        ("La Paz", "Bolivia", 1400, 4.6, 77, "High altitude city with indigenous culture"),
        ("Santiago", "Chile", 2500, 4.6, 79, "Modern capital with wine and mountains"),
        ("Atacama Desert", "Chile", 2100, 4.8, 80, "Otherworldly desert landscape"),
        ("Sao Paulo", "Brazil", 2300, 4.5, 75, "Art, food scene, and urban energy"),
        
        # Africa - Premium
        ("Cape Town", "South Africa", 3400, 4.9, 89, "Table Mountain and coastal beauty"),
        ("Masai Mara", "Kenya", 3200, 4.9, 87, "World-renowned safari destination"),
        ("Giza", "Egypt", 2200, 4.9, 85, "Ancient wonders of the world"),
        
        # Africa - Mid-range
        ("Cairo", "Egypt", 1800, 4.7, 82, "Pyramids, Sphinx, and Nile River"),
        ("Luxor", "Egypt", 1600, 4.8, 80, "Valley of the Kings and Karnak temples"),
        ("Zanzibar", "Tanzania", 2000, 4.8, 83, "Spice island with pristine beaches"),
        ("Marrakech", "Morocco", 2200, 4.8, 85, "Red city with Sahara access"),
        ("Fez", "Morocco", 1800, 4.7, 80, "Medina with ancient leather tanneries"),
        ("Kigali", "Rwanda", 1900, 4.6, 76, "Clean city with mountain gorilla trekking"),
        
        # Africa - Budget
        ("Johannesburg", "South Africa", 2000, 4.4, 73, "Vibrant city with Apartheid history"),
        ("Nairobi", "Kenya", 1600, 4.5, 75, "Gateway to African safaris"),
        ("Tanzania", "Tanzania", 1900, 4.8, 84, "Mount Kilimanjaro and Serengeti"),
        ("Dar es Salaam", "Tanzania", 1500, 4.5, 74, "Port city with Swahili heritage"),
        ("Casablanca", "Morocco", 1500, 4.6, 78, "Coastal city with Hassan II Mosque"),
        ("Tangier", "Morocco", 1300, 4.5, 76, "Gateway between Africa and Europe"),
        ("Essaouira", "Morocco", 1400, 4.6, 77, "Beach town with bohemian vibe"),
        ("Accra", "Ghana", 1300, 4.4, 70, "West African cultural hub"),
        ("Lagos", "Nigeria", 1400, 4.2, 69, "Bustling metropolis on the coast"),
        ("Kampala", "Uganda", 1200, 4.4, 72, "Vibrant capital in the Pearl of Africa"),
        ("Addis Ababa", "Ethiopia", 900, 4.3, 68, "Ancient Orthodox churches"),
        
        # Oceania - Ultra Luxury
        ("Sydney", "Australia", 5500, 4.8, 89, "Opera House and Bondi Beach"),
        ("Queenstown", "New Zealand", 5200, 4.9, 87, "Adrenaline sports and mountain beauty"),
        
        # Oceania - Premium
        ("Melbourne", "Australia", 4800, 4.7, 86, "Coffee capital and street art"),
        ("Auckland", "New Zealand", 4600, 4.7, 83, "Gateway to Aotearoa"),
        ("Honolulu", "USA", 5800, 4.8, 87, "Hawaiian beaches and culture"),
        ("Fiji", "Fiji", 3600, 4.9, 88, "Tropical island paradise"),
        ("Bora Bora", "French Polynesia", 8500, 5.0, 89, "Overwater bungalows and lagoon"),
        ("Tahiti", "French Polynesia", 7500, 4.9, 86, "Polynesian culture and beaches"),
        
        # Oceania - Mid-range
        ("Brisbane", "Australia", 3200, 4.6, 81, "Sunny subtropical city"),
        ("Cairns", "Australia", 3600, 4.8, 85, "Gateway to Great Barrier Reef"),
        ("Gold Coast", "Australia", 3000, 4.7, 83, "Beach resort paradise"),
        ("Perth", "Australia", 3400, 4.6, 79, "Isolated Western paradise"),
        ("Hobart", "Australia", 2800, 4.7, 77, "Gateway to Tasmania's wilderness"),
        ("Christchurch", "New Zealand", 3400, 4.7, 80, "Adventure capital of the South Island"),
        ("Samoa", "Samoa", 2800, 4.8, 82, "South Pacific island charm"),
    ]
    
    cur.executemany(
        """
        INSERT OR IGNORE INTO destinations (name, country, avg_budget, avg_rating, popularity, description)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        destinations,
    )
    conn.commit()
    print(f"✅ Seeded {len(destinations)} destinations into database")

