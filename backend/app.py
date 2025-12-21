import math
import os
from collections import Counter
from datetime import datetime
from typing import List, Tuple

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from werkzeug.security import check_password_hash, generate_password_hash

from db import get_connection, init_db, DB_PATH


def create_app():
    app = Flask(__name__)
    secret_key = os.environ.get("JWT_SECRET_KEY", "triplogger-dev-secret-key-2025")
    app.config["JWT_SECRET_KEY"] = secret_key
    app.config["JWT_ALGORITHM"] = "HS256"
    
    # CORS configuration - permissive for development
    is_dev = os.environ.get("FLASK_ENV") != "production"
    if is_dev:
        # Allow all origins in development
        CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["Content-Type", "Authorization"]}}, supports_credentials=True)
    else:
        # Production: restrict to specific origins
        CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"], supports_credentials=True)
    
    jwt = JWTManager(app)
    print(f"🔐 JWT initialized with secret key: {secret_key[:20]}...")
    init_db()

    # JWT error handlers with detailed logging
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        print(f"⏰ Token expired")
        return jsonify({"error": "Token has expired. Please login again."}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        print(f"❌ Invalid token error: {error}")
        return jsonify({"error": "Invalid token. Please login again."}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        print(f"🚫 Missing/unauthorized token: {error}")
        return jsonify({"error": "Authorization required. Please login."}), 401
    
    @app.route("/health", methods=["GET"])
    def health():
        try:
            conn = get_connection()
            # Check database connectivity
            total_users = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()["count"]
            total_trips = conn.execute("SELECT COUNT(*) as count FROM trips").fetchone()["count"]
            conn.close()
            
            return jsonify({
                "status": "ok",
                "message": "TripLogger API is running",
                "database": "connected",
                "total_users": total_users,
                "total_trips": total_trips,
                "db_path": str(DB_PATH)
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": "Database connection failed",
                "error": str(e),
                "db_path": str(DB_PATH)
            }), 500

    # Debug endpoint to check current user
    @app.route("/debug/user", methods=["GET"])
    @jwt_required()
    def debug_user():
        try:
            user_id = int(get_jwt_identity())
            conn = get_connection()
            
            # Get user info
            user_row = conn.execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()
            
            # Get user's trips count
            trips_count = conn.execute("SELECT COUNT(*) as count FROM trips WHERE user_id = ?", (user_id,)).fetchone()["count"]
            
            # Get all users (for debugging)
            all_users = conn.execute("SELECT id, username FROM users").fetchall()
            
            conn.close()
            
            return jsonify({
                "current_user": dict(user_row) if user_row else None,
                "trips_count": trips_count,
                "all_users": [dict(u) for u in all_users]
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# module 1 backend

    # authorization routes::

    # register route
    @app.route("/auth/register", methods=["POST"])
    def register():
        data = request.get_json(force=True)
        username = (data.get("username") or "").strip().lower()
        password = data.get("password")
        if not username or not password:
            return jsonify({"error": "Username and password are required."}), 400
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters."}), 400

        conn = get_connection()
        cur = conn.cursor()
        existing = cur.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            conn.close()
            return jsonify({"error": "Username already exists."}), 400

        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, generate_password_hash(password)),
        )
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        token = create_access_token(identity=str(user_id))
        return jsonify({"access_token": token, "username": username, "user_id": user_id}), 201

    # login route
    @app.route("/auth/login", methods=["POST"])
    def login():
        data = request.get_json(force=True)
        username = (data.get("username") or "").strip().lower()
        password = data.get("password")
        if not username or not password:
            return jsonify({"error": "Username and password are required."}), 400

        conn = get_connection()
        user = conn.execute(
            "SELECT id, password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()
        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Invalid credentials."}), 401
        token = create_access_token(identity=str(user["id"]))
        print(f"✅ Login successful for user: {username} (id: {user['id']})")
        print(f"🎫 Token generated: {token[:50]}...")
        return jsonify({"access_token": token, "username": username, "user_id": user["id"]})

    # trip routes:

    # add trip route
    @app.route("/trips", methods=["POST"])
    @jwt_required()
    def add_trip():
        user_id = get_jwt_identity()
        data = request.get_json(force=True)
        required = ["destination", "start_date", "end_date", "budget", "rating"]
        missing = [k for k in required if k not in data or data[k] in [None, ""]]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

        try:
            start_date = datetime.fromisoformat(data["start_date"]).date()
            end_date = datetime.fromisoformat(data["end_date"]).date()
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid date format. Use ISO format YYYY-MM-DD."}), 400

        if end_date < start_date:
            return jsonify({"error": "End date cannot be before start date."}), 400

        try:
            budget = float(data["budget"])
            rating = float(data["rating"])
        except (TypeError, ValueError):
            return jsonify({"error": "Budget and rating must be numbers."}), 400

        if rating < 0 or rating > 5:
            return jsonify({"error": "Rating must be between 0 and 5."}), 400

        conn = get_connection()
        try:
            print(f"🔍 DEBUG: Adding trip for user_id: {user_id}")
            print(f"🔍 DEBUG: Database path: {DB_PATH}")
            print(f"🔍 DEBUG: Trip data: {data}")
            
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO trips (destination, start_date, end_date, budget, rating, user_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    data["destination"].strip(),
                    start_date.isoformat(),
                    end_date.isoformat(),
                    budget,
                    rating,
                    user_id,
                ),
            )
            conn.commit()
            trip_id = cur.lastrowid
            print(f"✅ DEBUG: Trip saved with ID: {trip_id}")
            
            # Verify the trip was actually saved
            verify_cur = conn.cursor()
            verify_cur.execute("SELECT COUNT(*) as count FROM trips WHERE user_id = ?", (user_id,))
            count = verify_cur.fetchone()["count"]
            print(f"🔍 DEBUG: Total trips for user {user_id}: {count}")
            
            return jsonify({"id": trip_id}), 201
        except Exception as e:
            print(f"❌ DEBUG: Database error: {str(e)}")
            conn.rollback()
            return jsonify({"error": f"Database error: {str(e)}"}), 500
        finally:
            conn.close()

    # list trips route
    @app.route("/trips", methods=["GET"])
    @jwt_required()
    def list_trips():
        try:
            user_id = int(get_jwt_identity())
            print(f"🔍 DEBUG: Listing trips for user_id: {user_id}")
        except Exception as e:
            print(f"❌ JWT validation failed: {str(e)}")
            raise
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT id, destination, start_date, end_date, budget, rating
            FROM trips WHERE user_id = ?
            ORDER BY destination ASC
            """,
            (user_id,),
        ).fetchall()
        conn.close()
        trips = [dict(row) for row in rows]
        print(f"🔍 DEBUG: Found {len(trips)} trips for user {user_id}")
        return jsonify(trips)

    # trip detail route
    @app.route("/trips/<int:trip_id>", methods=["GET"])
    @jwt_required()
    def trip_detail(trip_id: int):
        user_id = int(get_jwt_identity())
        conn = get_connection()
        row = conn.execute(
            """
            SELECT id, destination, start_date, end_date, budget, rating
            FROM trips WHERE id = ? AND user_id = ?
            """,
            (trip_id, user_id),
        ).fetchone()
        conn.close()
        if not row:
            return jsonify({"error": "Trip not found"}), 404
        return jsonify(dict(row))

    # update trip route
    @app.route("/trips/<int:trip_id>", methods=["PUT"])
    @jwt_required()
    def update_trip(trip_id: int):
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        # Validate required fields
        required = ["destination", "start_date", "end_date", "budget", "rating"]
        for field in required:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400
        
        try:
            # Validate data types
            budget = float(data["budget"])
            rating = float(data["rating"])
            
            if budget < 0:
                return jsonify({"error": "Budget must be non-negative"}), 400
            if not (0 <= rating <= 5):
                return jsonify({"error": "Rating must be between 0 and 5"}), 400
                
            # Validate dates
            start_date = datetime.strptime(data["start_date"], "%Y-%m-%d").date()
            end_date = datetime.strptime(data["end_date"], "%Y-%m-%d").date()
            
            if start_date > end_date:
                return jsonify({"error": "Start date must be before end date"}), 400
                
        except ValueError as e:
            return jsonify({"error": f"Invalid data format: {str(e)}"}), 400
        
        conn = get_connection()
        
        # Check if trip exists and belongs to user
        existing = conn.execute(
            "SELECT id FROM trips WHERE id = ? AND user_id = ?",
            (trip_id, user_id)
        ).fetchone()
        
        if not existing:
            conn.close()
            return jsonify({"error": "Trip not found"}), 404
        
        # Update the trip
        conn.execute(
            """
            UPDATE trips 
            SET destination = ?, start_date = ?, end_date = ?, budget = ?, rating = ?
            WHERE id = ? AND user_id = ?
            """,
            (data["destination"], start_date, end_date, budget, rating, trip_id, user_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Trip updated successfully"}), 200

    # delete trip route
    @app.route("/trips/<int:trip_id>", methods=["DELETE"])
    @jwt_required()
    def delete_trip(trip_id: int):
        user_id = int(get_jwt_identity())
        conn = get_connection()
        
        # Check if trip exists and belongs to user
        existing = conn.execute(
            "SELECT id FROM trips WHERE id = ? AND user_id = ?",
            (trip_id, user_id)
        ).fetchone()
        
        if not existing:
            conn.close()
            return jsonify({"error": "Trip not found"}), 404
        
        # Delete the trip
        conn.execute("DELETE FROM trips WHERE id = ? AND user_id = ?", (trip_id, user_id))
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Trip deleted successfully"}), 200

# module 2 backend: stats routes

    # trip stats route
    @app.route("/trips/stats", methods=["GET"])
    @jwt_required()
    def trip_stats():
        user_id = int(get_jwt_identity())
        conn = get_connection()
        rows = conn.execute(
            "SELECT destination, start_date FROM trips WHERE user_id = ?", (user_id,)
        ).fetchall()
        conn.close()
        if not rows:
            return jsonify({"trips_by_month": {}, "favorite_destinations": []})

        by_month = Counter()
        dest_counter = Counter()
        for row in rows:
            month_key = row["start_date"][:7]
            by_month[month_key] += 1
            dest_counter[row["destination"]] += 1

        favorite = [{"destination": d, "count": c} for d, c in dest_counter.most_common(5)]
        return jsonify({"trips_by_month": by_month, "favorite_destinations": favorite})

    # spending stats route
    @app.route("/trips/spending", methods=["GET"])
    @jwt_required()
    def spending():
        user_id = int(get_jwt_identity())
        conn = get_connection()
        rows = conn.execute("SELECT budget FROM trips WHERE user_id = ?", (user_id,)).fetchall()
        conn.close()
        budgets = [row["budget"] for row in rows]
        if not budgets:
            return jsonify({"total": 0, "average": 0})
        total = sum(budgets)
        avg = total / len(budgets)
        return jsonify({"total": total, "average": avg})

# module 3 backend: recommendation routes

    # recommendation algorithm route
    
    @app.route("/recommend", methods=["GET"])
    @jwt_required()
    def recommend():
        user_id = int(get_jwt_identity())
        conn = get_connection()
        
        # Get user's trips
        user_trips_rows = conn.execute(
            """
            SELECT destination, budget, rating
            FROM trips WHERE user_id = ?
            ORDER BY rating DESC
            """,
            (user_id,),
        ).fetchall()
        user_trips = [dict(row) for row in user_trips_rows]
        
        # global variable k in the KNN algorithm
        k = 3

        if len(user_trips) < 3:
            # No trips yet, return popular destinations
            dest_rows = conn.execute(
                "SELECT name as destination, avg_budget as budget, avg_rating as rating FROM destinations ORDER BY popularity DESC LIMIT 5"
            ).fetchall()
            destinations = [dict(row) for row in dest_rows]
            for dest in destinations:
                dest["reason"] = f"Popular destination worldwide"
                dest["is_new"] = True
            conn.close()
            return jsonify({"recommendations": destinations, "message": "Add trips to get personalized recommendations."})
        
        # Get all destinations from database
        all_dest_rows = conn.execute(
            "SELECT name as destination, avg_budget as budget, avg_rating as rating FROM destinations"
        ).fetchall()
        all_destinations = [dict(row) for row in all_dest_rows]
        
        # Get visited destinations
        visited_destinations = {trip["destination"] for trip in user_trips}
        
        # Filter unvisited destinations only
        unvisited_destinations = [d for d in all_destinations if d["destination"] not in visited_destinations]
        
        conn.close()
        
        # Use top-rated trip as target
        top_trip = user_trips[0]
        target_vec = _vectorize_trip(top_trip)
        
        # Combine unvisited destinations with other user trips for KNN
        # Mix new destinations with previous trips for comparison
        all_candidates = unvisited_destinations + user_trips[1:]
        
        # Calculate distances
        distances: List[Tuple[float, dict, bool]] = []
        for candidate in all_candidates:
            vec = _vectorize_trip(candidate)
            dist = _euclidean_distance(target_vec, vec)
            is_new = candidate["destination"] not in visited_destinations
            distances.append((dist, candidate, is_new))
        
        # Sort by distance and get top k
        distances.sort(key=lambda x: x[0])
        top_recommendations = distances[:k]
        
        recommendations = []
        for dist, trip, is_new in top_recommendations:
            recommendation = {
                "destination": trip["destination"],
                "budget": trip["budget"],
                "rating": trip["rating"],
                "is_new": is_new,
            }
            
            if is_new:
                recommendation["reason"] = (
                    f"✨ NEW - Similar budget (${trip['budget']}) and rating ({trip['rating']}) "
                    f"to your top-rated trip to {top_trip['destination']}."
                )
            else:
                recommendation["reason"] = (
                    f"Similar budget (${trip['budget']}) and rating ({trip['rating']}) "
                    f"to your top-rated trip to {top_trip['destination']}."
                )
            
            recommendations.append(recommendation)
        
        return jsonify({"recommendations": recommendations})

    return app

# functions for recommendation algorithm

def _vectorize_trip(trip: dict) -> Tuple[float, float]:
    """
    Vectorize trip with weighted Euclidean distance.
    Budget weight: 2.0 (prioritized for matching user's spending capacity)
    Rating weight: 1.0 (secondary consideration for quality)
    """
    budget_scaled = math.log1p(trip["budget"]) * 2.0  # Higher weight for budget
    rating_scaled = trip["rating"] / 5.0 * 1.0  # Lower weight for rating
    return (budget_scaled, rating_scaled)


def _euclidean_distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    """
    Euclidean distance with weighted dimensions.
    Budget (first dimension) is 2x more important than rating (second dimension).
    This ensures budget-similar destinations are prioritized.
    """
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


# Running the app

if __name__ == "__main__":
    app = create_app()
    print("=" * 60)
    print("🚀 TripLogger Backend Server Starting...")
    print(f"📍 Running on: http://0.0.0.0:5000")
    print(f"🌐 CORS: Enabled (Development mode - all origins allowed)")
    print("=" * 60)
    app.run(
    host="0.0.0.0",
    port=5000,
    debug=True,
    use_reloader=False
)


