
               MODULE 3: DESTINATION RECOMMENDER (AI/ML)                    
                           Aryan Rajput                           
                                                                            
  KNN Algorithm, Machine Learning & Intelligent Recommendations             

📋 FILES I OWN & SHOULD MODIFY:

BACKEND FILES:
──────────────

1. backend/blueprints/recommender.py (195 lines) ⭐ CORE FILE - AI/ML
   - Vector space representation of trips
   - Distance calculation (Euclidean)
   - K-Nearest Neighbors (KNN) algorithm
   - Feature weighting (Budget 2x, Rating 1x)
   - Recommendation ranking
   - 150 pre-loaded destination cities
   
   Functions to implement/modify:
   ✓ _vectorize_trip(trip) - Convert trip to [budget, rating] vector
   ✓ _euclidean_distance(v1, v2) - Calculate distance
   ✓ @recommender_bp.route('/recommend', methods=['GET']) - KNN algorithm

FRONTEND FILES:
───────────────

2. frontend-react/src/services/recommendationService.js (20 lines) ⭐ CORE FILE
   - getRecommendations() function
   - API communication
   - Error handling

3. frontend-react/src/hooks/useRecommendations.js (35 lines) ⭐ CORE FILE
   - Recommendations state management
   - recommendations[] state variable
   - message state variable
   - loading state
   - error state
   - fetchRecommendations method
   - Auto-fetch when user logs in

4. frontend-react/src/components/Module3-Recommender/Recommendations.js (60 lines) ⭐ CORE FILE
   - Display KNN recommendations
   - Show "✨ NEW" badge for recommendations
   - Card layout with destination details
   - Budget and rating display
   - Recommendation reason/explanation
   - Empty state handling
   - Loading animation


🎯 WHAT MY MODULE DOES:

The KNN (K-Nearest Neighbors) Algorithm:

Given a user's existing trips and data of 132 cities around the world, recommend similar destinations they haven't visited yet using KNN.

ALGORITHM FLOW:

1. USER PROFILE CREATION:
   - Analyze user's existing trips
   - Extract average budget: sum(budgets) / count
   - Extract average rating: sum(ratings) / count
   - Create user vector: [avg_budget_scaled, avg_rating_scaled]

2. FEATURE SCALING:
   - Budget: log(budget) * 2.0 (weighted more heavily)
   - Rating: rating / 5.0 * 1.0 (standard scaling)
   
   Why weights?
   - Budget is more informative & important. (log scale)
   - Rating is secondary indicator
   - Weights allow tuning algorithm behavior

3. DISTANCE CALCULATION:
   - Use Euclidean distance in 2D space
   - Distance = sqrt((budget_diff)^2 + (rating_diff)^2)
   - Lower distance = more similar destination

4. KNN SELECTION:
   - Find K nearest neighbor destinations (K=3)
   - Exclude destinations user has visited
   - Sort by distance (ascending)
   - Return top 3 recommendations

════════════════════════════════════════════════════════════════════════════

🔌 API ENDPOINT I CREATE:

GET /recommender/recommend
  Response: [
    {
      "destination": "Paris",
      "budget": 2500,
      "rating": 4.5,
      "distance": 0.15,
      "confidence": 0.87,
      "reason": "Similar to your trip to London"
    },
    {
      "destination": "Barcelona",
      "budget": 2200,
      "rating": 4.3,
      "distance": 0.28,
      "confidence": 0.78,
      "reason": "Matches your budget preferences"
    },
    {
      "destination": "Amsterdam",
      "budget": 2400,
      "rating": 4.4,
      "distance": 0.12,
      "confidence": 0.89,
      "reason": "Highly similar to your travel style"
    }
  ]
  Status: 200 OK
  Auth: Required (Bearer token)
  Description: Returns top 3 destinations NOT yet visited

════════════════════════════════════════════════════════════════════════════

🔑 KEY IMPLEMENTATION TIPS:

1. VECTOR REPRESENTATION (Backend):
   import math
   
   def _vectorize_trip(trip):
       budget_scaled = math.log(trip.budget) * 2.0
       rating_scaled = trip.rating / 5.0 * 1.0
       return [budget_scaled, rating_scaled]

2. EUCLIDEAN DISTANCE:
   def _euclidean_distance(v1, v2):
       return math.sqrt(
           (v1[0] - v2[0])**2 + 
           (v1[1] - v2[1])**2
       )

3. USER PROFILE CREATION:
   user_trips = get_user_trips(user_id)
   if not user_trips:
       return []  # No recommendations for new users
   
   avg_budget = sum(t.budget for t in user_trips) / len(user_trips)
   avg_rating = sum(t.rating for t in user_trips) / len(user_trips)
   
   user_vector = _vectorize_trip(
       type('obj', (object,), {'budget': avg_budget, 'rating': avg_rating})()
   )

4. KNN ALGORITHM:
   visited_dests = set(t.destination for t in user_trips)
   all_dests = Destination.query.all()
   
   distances = []
   for dest in all_dests:
       if dest.name not in visited_dests:
           dest_vector = _vectorize_trip(dest)
           dist = _euclidean_distance(user_vector, dest_vector)
           distances.append((dest, dist))
   
   # Sort by distance, take top 3
   recommendations = sorted(distances, key=lambda x: x[1])[:3]

════════════════════════════════════════════════════════════════════════════

📊 DATABASE - 132 CITIES PRE-LOADED:

The db.py already contains 132 real cities with:
- Name: City name
- Budget: Average trip cost (ranges from $500 to $10000)
- Rating: User ratings (ranges from 2.0 to 5.0)
- Budget and Rating are CORRELATED:
  * Higher budget cities tend to have higher ratings
  * This is realistic (luxury = better experience)
