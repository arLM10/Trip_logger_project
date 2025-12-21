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

from db import get_connection, init_db


def create_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = os.environ.get(
        "JWT_SECRET_KEY", "triplogger-dev-secret-key-2025"
    )
    app.config["JWT_ALGORITHM"] = "HS256"

    # Enable CORS
    if os.environ.get("FLASK_ENV") != "production":
        CORS(app, resources={r"/*": {"origins": "*"}},
             supports_credentials=True)
    else:
        CORS(app, origins=["http://localhost:3000",
             "http://127.0.0.1:3000"], supports_credentials=True)

    jwt = JWTManager(app)
    print(
        f"🔐 JWT initialized with secret key: {app.config['JWT_SECRET_KEY'][:20]}...")
    init_db()

    # JWT error handlers
    @jwt.expired_token_loader
    def token_expired(jwt_header, jwt_payload):
        print("⏰ Token expired")
        return jsonify({"error": "Token has expired. Please login again."}), 401

    @jwt.invalid_token_loader
    def token_invalid(error):
        print(f"❌ Invalid token: {error}")
        return jsonify({"error": "Invalid token. Please login again."}), 401

    @jwt.unauthorized_loader
    def token_missing(error):
        print(f"🚫 Missing/unauthorized token: {error}")
        return jsonify({"error": "Authorization required. Please login."}), 401

    # Health check
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "message": "TripLogger API is running"})

    # ----------------------
    # AUTH ROUTES
    # ----------------------
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
        if cur.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone():
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
        return jsonify({"access_token": token, "username": username}), 201

    @app.route("/auth/login", methods=["POST"])
    def login():
        data = request.get_json(force=True)
        username = (data.get("username") or "").strip().lower()
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Username and password are required."}), 400

        conn = get_connection()
        user = conn.execute(
            "SELECT id, password_hash FROM users WHERE username = ?", (
                username,)
        ).fetchone()
        conn.close()

        if not user or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Invalid credentials."}), 401

        token = create_access_token(identity=str(user["id"]))
        print(f"✅ Login successful: {username} (id: {user['id']})")
        return jsonify({"access_token": token, "username": username})

    # ----------------------
    # TRIP ROUTES
    # ----------------------
    @app.route("/trips", methods=["POST"])
    @jwt_required()
    def add_trip():
        user_id = get_jwt_identity()
        data = request.get_json(force=True)
        required_fields = ["destination", "start_date",
                           "end_date", "budget", "rating"]
        missing = [
            f for f in required_fields if f not in data or data[f] in [None, ""]]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

        try:
            start_date = datetime.fromisoformat(data["start_date"]).date()
            end_date = datetime.fromisoformat(data["end_date"]).date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

        if end_date < start_date:
            return jsonify({"error": "End date cannot be before start date."}), 400

        try:
            budget = float(data["budget"])
            rating = float(data["rating"])
        except ValueError:
            return jsonify({"error": "Budget and rating must be numbers."}), 400

        if not (0 <= rating <= 5):
            return jsonify({"error": "Rating must be between 0 and 5."}), 400

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO trips (destination, start_date, end_date, budget, rating, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (data["destination"].strip(), start_date.isoformat(),
             end_date.isoformat(), budget, rating, user_id)
        )
        conn.commit()
        trip_id = cur.lastrowid
        conn.close()
        return jsonify({"id": trip_id}), 201

    @app.route("/trips", methods=["GET"])
    @jwt_required()
    def list_trips():
        user_id = get_jwt_identity()
        conn = get_connection()
        rows = conn.execute(
            """
            SELECT id, destination, start_date, end_date, budget, rating
            FROM trips WHERE user_id = ?
            ORDER BY start_date DESC
            """,
            (user_id,),
        ).fetchall()
        conn.close()
        return jsonify([dict(row) for row in rows])

    @app.route("/trips/<int:trip_id>", methods=["GET"])
    @jwt_required()
    def trip_detail(trip_id: int):
        user_id = get_jwt_identity()
        conn = get_connection()
        row = conn.execute(
            "SELECT id, destination, start_date, end_date, budget, rating FROM trips WHERE id = ? AND user_id = ?",
            (trip_id, user_id),
        ).fetchone()
        conn.close()
        if not row:
            return jsonify({"error": "Trip not found"}), 404
        return jsonify(dict(row))

    # ----------------------
    # STATS ROUTES
    # ----------------------
    @app.route("/trips/stats", methods=["GET"])
    @jwt_required()
    def trip_stats():
        user_id = get_jwt_identity()
        conn = get_connection()
        rows = conn.execute(
            "SELECT destination, start_date FROM trips WHERE user_id = ?", (
                user_id,)
        ).fetchall()
        conn.close()

        if not rows:
            return jsonify({"trips_by_month": {}, "favorite_destinations": []})

        trips_by_month = Counter(row["start_date"][:7] for row in rows)
        favorite_destinations = [{"destination": d, "count": c}
                                 for d, c in Counter(row["destination"] for row in rows).most_common(5)]

        return jsonify({"trips_by_month": trips_by_month, "favorite_destinations": favorite_destinations})

    @app.route("/trips/spending", methods=["GET"])
    @jwt_required()
    def spending():
        user_id = get_jwt_identity()
        conn = get_connection()
        rows = conn.execute(
            "SELECT budget FROM trips WHERE user_id = ?", (user_id,)).fetchall()
        conn.close()

        budgets = [row["budget"] for row in rows]
        total = sum(budgets)
        average = total / len(budgets) if budgets else 0
        return jsonify({"total": total, "average": average})

    # ----------------------
    # RECOMMENDATION ROUTE
    # ----------------------
    @app.route("/recommend", methods=["GET"])
    @jwt_required()
    def recommend():
        user_id = get_jwt_identity()
        conn = get_connection()

        # User trips
        user_trips_rows = conn.execute(
            "SELECT destination, budget, rating FROM trips WHERE user_id = ? ORDER BY rating DESC", (
                user_id,)
        ).fetchall()
        user_trips = [dict(row) for row in user_trips_rows]

        if len(user_trips) < 3:
            popular_rows = conn.execute(
                "SELECT name as destination, avg_budget as budget, avg_rating as rating FROM destinations ORDER BY popularity DESC LIMIT 5"
            ).fetchall()
            conn.close()
            recommendations = [
                {**dict(row), "reason": "Popular destination worldwide", "is_new": True} for row in popular_rows
            ]
            return jsonify({"recommendations": recommendations,
                            "message": "Add trips to get personalized recommendations."})

        all_dest_rows = conn.execute(
            "SELECT name as destination, avg_budget as budget, avg_rating as rating FROM destinations"
        ).fetchall()
        all_destinations = [dict(row) for row in all_dest_rows]
        visited_destinations = {trip["destination"] for trip in user_trips}
        unvisited_destinations = [
            d for d in all_destinations if d["destination"] not in visited_destinations
        ]
        conn.close()

        target_vec = _vectorize_trip(user_trips[0])
        candidates = unvisited_destinations + user_trips[1:]
        distances: List[Tuple[float, dict, bool]] = [
            (_euclidean_distance(target_vec, _vectorize_trip(c)),
             c, c["destination"] not in visited_destinations)
            for c in candidates
        ]
        distances.sort(key=lambda x: x[0])

        recommendations = []
        for dist, trip, is_new in distances[:3]:
            reason = f"✨ NEW - Similar budget (${trip['budget']}) and rating ({trip['rating']}) to your top-rated trip to {user_trips[0]['destination']}." if is_new else f"Similar budget (${trip['budget']}) and rating ({trip['rating']}) to your top-rated trip to {user_trips[0]['destination']}."
            recommendations.append(
                {**trip, "is_new": is_new, "reason": reason})

        return jsonify({"recommendations": recommendations})

    return app


# ----------------------
# Helper functions
# ----------------------
def _vectorize_trip(trip: dict) -> Tuple[float, float]:
    return (math.log1p(trip["budget"]) * 2.0, trip["rating"] / 5.0)


def _euclidean_distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


# ----------------------
# Run server
# ----------------------
if __name__ == "__main__":
    app = create_app()
    print("=" * 60)
    print("🚀 TripLogger Backend Server Starting...")
    print("📍 Running on: http://0.0.0.0:5000")
    print("🌐 CORS: Enabled (Development mode)")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)
