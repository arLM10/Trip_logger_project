# TripLogger API Documentation

Base URL: `http://localhost:5000`

## Trip Management API's

### 1. GET /trips
Get all trips for authenticated user (ordered alphabetically by destination).

**Response:**
```json
[
  {
    "id": 1,
    "destination": "Bali",
    "start_date": "2024-01-15",
    "end_date": "2024-01-25",
    "budget": 2500.0,
    "rating": 4.5
  },
  {
    "id": 2,
    "destination": "Paris",
    "start_date": "2024-03-10",
    "end_date": "2024-03-17",
    "budget": 3200.0,
    "rating": 4.8
  }
]
```

### 2. POST /trips
Create a new trip.

**Request:**
```json
{
  "destination": "Tokyo",
  "start_date": "2024-06-01",
  "end_date": "2024-06-10",
  "budget": 4500,
  "rating": 4.9
}
```

**Response:**
```json
{
  "id": 3
}
```

### 3. GET /trips/{trip_id}
Get specific trip details.

**Response:**
```json
{
  "id": 1,
  "destination": "Bali",
  "start_date": "2024-01-15",
  "end_date": "2024-01-25",
  "budget": 2500.0,
  "rating": 4.5
}
```

### 4. PUT /trips/{trip_id}
Update existing trip.

**Request:**
```json
{
  "destination": "Bali (Updated)",
  "start_date": "2024-01-15",
  "end_date": "2024-01-25",
  "budget": 2800,
  "rating": 4.7
}
```

**Response:**
```json
{
  "message": "Trip updated successfully"
}
```

### 5. DELETE /trips/{trip_id}
Delete a trip.

**Response:**
```json
{
  "message": "Trip deleted successfully"
}
```

---

## Statistics API's

### 1. GET /trips/stats
Get travel statistics and analytics.

**Response:**
```json
{
  "trips_by_month": {
    "2024-01": 2,
    "2024-03": 1,
    "2024-06": 1
  },
  "favorite_destinations": [
    {
      "destination": "Bali",
      "count": 3
    },
    {
      "destination": "Paris",
      "count": 2
    }
  ]
}
```

### 6. GET /trips/spending
Get spending statistics.

**Response:**
```json
{
  "total": 15200.0,
  "average": 3800.0
}
```

---

## Recommendation API's

### 1. GET /recommend
Get personalized destination recommendations.

**Response:**
```json
{
  "recommendations": [
    {
      "destination": "Kyoto",
      "budget": 3500.0,
      "rating": 4.8,
      "reason": "Similar to your highly-rated cultural destinations"
    },
    {
      "destination": "Barcelona",
      "budget": 2800.0,
      "rating": 4.6,
      "reason": "Matches your preferred budget range"
    }
  ],
  "message": "Recommendations based on your travel history"
}
```

---

## Authentication details API's

All endpoints except `/health`, `/auth/register`, and `/auth/login` require JWT authentication.

### Headers
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

## Endpoints

### 1. Health Check

#### 1. GET /health
Check API status and database connectivity.

**Response:**
```json
{
  "status": "ok",
  "message": "TripLogger API is running",
  "database": "connected",
  "total_users": 1,
  "total_trips": 11,
  "db_path": "/app/triplogger.db"
}
```

---

### 2. Authentication

#### 1. POST /auth/register
Register a new user account.

**Request:**
```json
{
  "username": "john_doe",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "username": "john_doe",
  "user_id": 2
}
```

#### 2. POST /auth/login
Login with existing credentials.

**Request:**
```json
{
  "username": "demo",
  "password": "demo123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "username": "demo",
  "user_id": 1
}
```

---

## Error Response API's

### 400 Bad Request
```json
{
  "error": "Missing field: destination"
}
```

### 401 Unauthorized
```json
{
  "error": "Please login to continue"
}
```

### 404 Not Found
```json
{
  "error": "Trip not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Database error: connection failed"
}
```

---


