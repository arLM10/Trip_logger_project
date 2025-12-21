# TripLogger System Architecture

## Overview
TripLogger is a containerized full-stack web application built with modern technologies for personal travel management and destination recommendations.

## Technology Stack

### Frontend Layer
- **Framework**: React 18.2.0
- **Language**: JavaScript (ES6+)
- **HTTP Client**: Axios 1.6.0
- **Charts**: Chart.js with react-chartjs-2
- **Styling**: CSS3 with Glass-morphism design
- **Build Tool**: Create React App (Webpack)
- **Package Manager**: npm

### Backend Layer
- **Framework**: Flask 2.3.0 (Python)
- **Authentication**: Flask-JWT-Extended 4.5.0
- **CORS**: Flask-CORS 4.0.0
- **Password Hashing**: Werkzeug Security
- **API Style**: RESTful
- **Runtime**: Python 3.11

### Database Layer
- **Current**: SQLite 3
- **Future**: PostgreSQL/MySQL compatible
- **ORM**: Raw SQL with sqlite3 module
- **Migrations**: Manual schema management

### Infrastructure Layer
- **Containerization**: Docker & Docker Compose
- **Frontend Container**: Node.js Alpine
- **Backend Container**: Python Alpine
- **Networking**: Docker bridge network
- **Volumes**: Persistent data storage

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     TRIPLOGGER APPLICATION                      │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                       FRONTEND (React)                           │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Browser (http://localhost:3000)                           │  │
│  │  ├─ Auth Card (Login/Register)                             │  │
│  │  ├─ Trip Form (Add new trips)                              │  │
│  │  ├─ Trip List (View past trips)                            │  │
│  │  ├─ Stats Charts (Trips by month, favorites)               │  │
│  │  └─ Recommendations Section                                |  |
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                            ↓↑
                      API Calls (axios)
                   http://localhost:5000
                            ↓↑
┌──────────────────────────────────────────────────────────────────┐
│                       BACKEND (Flask)                            │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  /auth/register, /auth/login                               │  │
│  │  /trips (GET, POST)                                        │  │
│  │  /trips/stats (GET)                                        │  │
│  │  /trips/spending (GET)                                     │  │
│  │  /recommend (GET)                                          |  |
│  │     └─ recommends according to the recommendation logic    │  │
│  │        given below in data flow.                           │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                            ↓↑
                    SQLite Database
                            ↓↑
┌──────────────────────────────────────────────────────────────────┐
│              DATABASE (triplogger.db)                            │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  TABLE: users                                              │  │
│  │  ├─ id, username, password_hash                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  TABLE: trips                                              │  │
│  │  ├─ id, destination, start_date, end_date                  │  │
│  │  ├─ budget, rating, user_id                                │  │
│  └────────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  TABLE: destinations                                       │  │
│  │  ├─ id, name, country, avg_budget, avg_rating              │  │
│  │  ├─ popularity, description                                │  │
│  │  └─ Contains 150 popular cities worldwide                  │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow Architecture

### 1. User Authentication Flow
```
Browser → React Auth Component → Axios → Flask /auth/login → 
Database Query → JWT Generation → Response → Token Storage → 
Axios Interceptor Setup
```

### 2. Trip Management Flow
```
User Input → React Form → Validation → Axios POST → 
Flask Route → JWT Validation → Database Transaction → 
Response → UI Update → Statistics Refresh
```

### 3. Recommendation Flow
```
User Request → Flask /recommend → Database Query (User Trips) → 
KNN Algorithm → Destination Matching → Similarity Calculation → 
Ranked Results → JSON Response → Chart.js Visualization
Recommendation Logic:

Takes your highest-rated trip as the target
Compares it to your other trips using Euclidean distance after vectorizing the trips.
Returns the k closest matches 
Each recommendation includes a reason explaining the similarity
Example:

If your top-rated trip was: Paris, Budget: $2000, Rating: 5.0

The algorithm finds trips with similar budget & rating
Returns destinations like: London ($1800, 4.8) or Amsterdam ($2100, 4.9)
Shows why: "Similar budget ($1800) and rating (4.8) to your top-rated trip to Paris"

```
---

## Database Schema Diagram

```
┌─────────────────────────────────────────────────────────┐
│                TABLE: users                             │
├─────────────────────────────────────────────────────────┤
│ id (PK)      | username (UNIQUE) | password_hash        │
├─────────────────────────────────────────────────────────┤
│ 1            | demo             | hashed_password...    │
│ 2            | john             | hashed_password...    │
└─────────────────────────────────────────────────────────┘
       ↑
       │ (Foreign Key)
       │
       ├──────────────────────────────────────────────┐
       │                                              │
┌──────────────────────────────────────┐   ┌─────────────────────────────────────────┐
│    TABLE: trips                       │   │   TABLE: destinations                   │
├──────────────────────────────────────┤   ├─────────────────────────────────────────┤
│ id(PK) | destination | budget | ...  │   │ id(PK) | name    | country | budget|..│
├──────────────────────────────────────┤   ├─────────────────────────────────────────┤
│ 1      | Paris      | 2000   |...    │   │ 1      | Paris  | France  | 2000  |..│
│ 2      | Tokyo      | 2500   |...    │   │ 2      | Tokyo  | Japan   | 2500  |..│
│ 3      | Rome       | 1800   |...    │   │ 3      | Rome   | Italy   | 1800  |..│
│        |            |        |       │   │ ...    | ...    | ...     | ...   |..│
│        |            |        |       │   │ 150    | Tahiti | French  | 2400  |..│
│        |            |        |       │   │        |        | Polynes.|       |..│
└──────────────────────────────────────┘   └─────────────────────────────────────────┘
  ↑
  │ (Matches destination name with candidates)
  │
  └──────────────────────────────────────────────────────┐
                 (For filtering visited)                  │
         (Unvisited: 150 - visited count)                │
```

---


