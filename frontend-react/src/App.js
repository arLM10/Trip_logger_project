import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';
import './App.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const storage = {
  getToken: () => localStorage.getItem('token'),
  setToken: (t) => localStorage.setItem('token', t),
  clear: () => localStorage.removeItem('token'),
};

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 second timeout
});

api.interceptors.request.use((config) => {
  const token = storage.getToken();
  console.log('📤 Request interceptor - Token present:', !!token);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    console.log('✅ Setting Authorization header');
  }
  return config;
});

// Create a global auth error handler that can be set by App component
let globalAuthErrorHandler = null;

export const setAuthErrorHandler = (handler) => {
  globalAuthErrorHandler = handler;
};

// Response interceptor with global auth error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      console.error('API request timeout - backend may not be running');
      error.message = 'Connection timeout. Please ensure the backend server is running on port 5000.';
    } else if (error.message === 'Network Error' || !error.response) {
      console.error('API connection failed - backend not reachable');
      error.message = 'Cannot connect to backend server. Please ensure it is running on http://localhost:5000';
    } else if (error.response?.status === 401 || error.response?.status === 422) {
      // JWT authentication error - clear token and notify App component
      console.warn('Authentication error:', error.response?.data?.error || 'Unauthorized');
      storage.clear();
      if (globalAuthErrorHandler) {
        globalAuthErrorHandler(error.response?.data?.error || 'Your session has expired. Please login again.');
      }
      error.message = error.response?.data?.error || 'Please login to continue';
    } else {
      console.error('API error:', error.response?.data || error.message);
    }
    return Promise.reject(error);
  }
);

//  Module1 functions and components:

// 1. Authentication Component
function AuthCard({ onAuth }) {
  const [mode, setMode] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const endpoint = mode === 'login' ? '/auth/login' : '/auth/register';
      const { data } = await api.post(endpoint, { username, password });
      console.log('✅ Auth successful, received token:', data.access_token.substring(0, 50) + '...');
      storage.setToken(data.access_token);
      // Force axios to use the new token immediately
      api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`;
      onAuth({ username: data.username, token: data.access_token });
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-card glass-card">
      <div className="auth-header">
        <h2>{mode === 'login' ? 'Welcome Back' : 'Start Your Journey'}</h2>
        <button className="switch-btn" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
          {mode === 'login' ? 'Need an account?' : 'Have an account?'}
        </button>
      </div>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>
            <span className="label-icon">👤</span>
            Username
          </label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            placeholder="Enter your username"
          />
        </div>
        <div className="form-group">
          <label>
            <span className="label-icon">🔒</span>
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
            placeholder="Enter your password"
          />
        </div>
        <button type="submit" className="primary-btn" disabled={loading}>
          {loading ? 'Please wait...' : mode === 'login' ? 'Login' : 'Register'}
        </button>
        {error && <div className="error-message">{error}</div>}
      </form>
    </div>
  );
}

// 2. Trip Form Component

function TripForm({ onSaved }) {
  const [form, setForm] = useState({
    destination: '',
    start_date: '',
    end_date: '',
    budget: '',
    rating: '',
  });
  const [msg, setMsg] = useState('');
  const [msgType, setMsgType] = useState('');

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMsg('Saving...');
    setMsgType('info');
    try {
      await api.post('/trips', form);
      setMsg('Trip saved successfully! ✈️');
      setMsgType('success');
      setForm({ destination: '', start_date: '', end_date: '', budget: '', rating: '' });
      setTimeout(() => {
        setMsg('');
        onSaved();
      }, 2000);
    } catch (err) {
      setMsg(err.response?.data?.error || err.message || 'Failed to save trip');
      setMsgType('error');
    }
  };

  return (
    <div className="glass-card card-animate">
      <h2 className="section-title">
        <span className="icon">✈️</span>
        Add New Trip
      </h2>
      <form onSubmit={handleSubmit} className="trip-form">
        <div className="form-grid">
          <div className="form-group">
            <label>
              <span className="label-icon">🌍</span>
              Destination
            </label>
            <input
              name="destination"
              value={form.destination}
              onChange={handleChange}
              required
              placeholder="e.g., Paris, Tokyo, New York"
            />
          </div>
          <div className="form-group">
            <label>
              <span className="label-icon">📅</span>
              Start Date
            </label>
            <input
              type="date"
              name="start_date"
              value={form.start_date}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label>
              <span className="label-icon">📅</span>
              End Date
            </label>
            <input
              type="date"
              name="end_date"
              value={form.end_date}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label>
              <span className="label-icon">💰</span>
              Budget (USD)
            </label>
            <input
              type="number"
              name="budget"
              min="0"
              step="50"
              value={form.budget}
              onChange={handleChange}
              required
              placeholder="0.00"
            />
          </div>
          <div className="form-group">
            <label>
              <span className="label-icon">⭐</span>
              Rating (0-5)
            </label>
            <input
              type="number"
              name="rating"
              min="0"
              max="5"
              step="0.5"
              value={form.rating}
              onChange={handleChange}
              required
              placeholder="0.0"
            />
          </div>
        </div>
        <button type="submit" className="primary-btn">
          Save Trip
        </button>
        {msg && (
          <div className={`message ${msgType}`}>
            {msg}
          </div>
        )}
      </form>
    </div>
  );
}

// 3. Trip List Component

function TripList({ refreshKey }) {
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    api
      .get('/trips')
      .then(({ data }) => mounted && setTrips(data))
      .catch((err) => mounted && setError(err.response?.data?.error || err.message || 'Failed to load trips'))
      .finally(() => mounted && setLoading(false));
    return () => (mounted = false);
  }, [refreshKey]);

  if (loading) return <div className="glass-card"><div className="loading-spinner">Loading trips...</div></div>;
  if (error) return <div className="glass-card"><div className="error-message">{error}</div></div>;

  return (
    <div className="glass-card card-animate">
      <h2 className="section-title">
        <span className="icon">🗺️</span>
        Your Travel History
      </h2>
      {trips.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">🌴</div>
          <p>No trips yet. Start your adventure by adding your first trip!</p>
        </div>
      ) : (
        <div className="trips-grid">
          {trips.map((t) => (
            <div key={t.id} className="trip-card">
              <div className="trip-header">
                <h3>{t.destination}</h3>
                <span className="rating-badge">⭐ {t.rating}</span>
              </div>
              <div className="trip-details">
                <p className="trip-date">
                  <span>📅</span>
                  {new Date(t.start_date).toLocaleDateString()} → {new Date(t.end_date).toLocaleDateString()}
                </p>
                <p className="trip-budget">
                  <span>💰</span>
                  ${Number(t.budget).toLocaleString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Module2 functions and components:

// experiment to see a merge conflict

// 1. Statistics and Charts Component
function StatsCharts({ refreshKey }) {
  const [data, setData] = useState({ trips_by_month: {}, favorite_destinations: [] });
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    api
      .get('/trips/stats')
      .then(({ data }) => mounted && setData(data))
      .catch((err) => mounted && setError(err.response?.data?.error || err.message || 'Failed to load stats'));
    return () => (mounted = false);
  }, [refreshKey]);

  const monthData = Object.entries(data.trips_by_month || {});
  const barData = {
    labels: monthData.map(([m]) => m),
    datasets: [
      {
        label: 'Trips',
        data: monthData.map(([, c]) => c),
        backgroundColor: 'rgba(58, 198, 255, 0.8)',
        borderColor: 'rgba(58, 198, 255, 1)',
        borderWidth: 2,
      },
    ],
  };

  const pieData = {
    labels: (data.favorite_destinations || []).map((f) => f.destination),
    datasets: [
      {
        data: (data.favorite_destinations || []).map((f) => f.count),
        backgroundColor: [
          'rgba(58, 198, 255, 0.8)',
          'rgba(91, 215, 133, 0.8)',
          'rgba(255, 123, 123, 0.8)',
          'rgba(255, 200, 87, 0.8)',
          'rgba(139, 163, 199, 0.8)',
        ],
        borderWidth: 2,
        borderColor: 'rgba(255, 255, 255, 0.1)',
      },
    ],
  };

  return (
    <div className="charts-container">
      <div className="glass-card card-animate">
        <h2 className="section-title">
          <span className="icon">📊</span>
          Trips by Month
        </h2>
        {error ? (
          <div className="error-message">{error}</div>
        ) : monthData.length > 0 ? (
          <Bar data={barData} options={{ responsive: true, plugins: { legend: { display: false } } }} />
        ) : (
          <div className="empty-state">
            <p>Add trips to see monthly statistics</p>
          </div>
        )}
      </div>
      <div className="glass-card card-animate">
        <h2 className="section-title">
          <span className="icon">🏆</span>
          Favorite Destinations
        </h2>
        {data.favorite_destinations?.length > 0 ? (
          <Doughnut data={pieData} options={{ responsive: true, plugins: { legend: { position: 'bottom' } } }} />
        ) : (
          <div className="empty-state">
            <p>No favorite destinations yet</p>
          </div>
        )}
      </div>
    </div>
  );
}

// 2. Spending Stats Component

function SpendingCard({ refreshKey }) {
  const [spending, setSpending] = useState({ total: 0, average: 0 });
  const [error, setError] = useState('');

  useEffect(() => {
    let mounted = true;
    api
      .get('/trips/spending')
      .then(({ data }) => mounted && setSpending(data))
      .catch((err) => mounted && setError(err.response?.data?.error || err.message || 'Failed to load spending'));
    return () => (mounted = false);
  }, [refreshKey]);

  return (
    <div className="glass-card card-animate">
      <h2 className="section-title">
        <span className="icon">💵</span>
        Travel Spending
      </h2>
      {error ? (
        <div className="error-message">{error}</div>
      ) : (
        <div className="spending-stats">
          <div className="stat-box">
            <div className="stat-label">Total Spent</div>
            <div className="stat-value">${Number(spending.total || 0).toLocaleString()}</div>
          </div>
          <div className="stat-box">
            <div className="stat-label">Average per Trip</div>
            <div className="stat-value">${Number(spending.average || 0).toLocaleString()}</div>
          </div>
        </div>
      )}
    </div>
  );
}

// Module3 functions and components:

// 1. Recommendations Component
function Recommendations({ refreshKey }) {
  const [recs, setRecs] = useState([]);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    api
      .get('/recommend')
      .then(({ data }) => {
        if (!mounted) return;
        setRecs(data.recommendations || []);
        setMessage(data.message || '');
        setError('');
      })
      .catch((err) => mounted && setError(err.response?.data?.error || err.message || 'Failed to load recommendations'))
      .finally(() => mounted && setLoading(false));
    return () => (mounted = false);
  }, [refreshKey]);

  return (
    <div className="glass-card card-animate">
      <h2 className="section-title">
        <span className="icon">🎯</span>
        Recommended Destinations
      </h2>
      {loading && <div className="loading-spinner">Loading recommendations...</div>}
      {error && <div className="error-message">{error}</div>}
      {!loading && !recs.length && (
        <div className="empty-state">
          <div className="empty-icon">🌍</div>
          <p>{message || 'Add more trips to get personalized recommendations!'}</p>
        </div>
      )}
      {recs.length > 0 && (
        <div className="recommendations-grid">
          {recs.map((r, idx) => (
            <div key={idx} className="recommendation-card">
              <div className="rec-header">
                <h3>{r.destination}</h3>
                <span className="rating-badge">⭐ {r.rating}</span>
              </div>
              <p className="rec-budget">💰 ${Number(r.budget).toLocaleString()}</p>
              <p className="rec-reason">{r.reason}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Main App Component

function App() {
  const [user, setUser] = useState(() => {
    const token = storage.getToken();
    return token ? { username: 'user', token } : null;
  });
  const [refreshKey, setRefreshKey] = useState(0);
  const [backendStatus, setBackendStatus] = useState(null);
  const [authError, setAuthError] = useState(null);

  // Set up global auth error handler
  useEffect(() => {
    setAuthErrorHandler((errorMsg) => {
      setAuthError(errorMsg);
      setUser(null);
    });
    return () => setAuthErrorHandler(null);
  }, []);

  // Check backend health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await axios.get(`${API_BASE}/health`, { timeout: 5000 });
        console.log('✅ Backend connection successful:', response.data);
        setBackendStatus('connected');
      } catch (error) {
        console.error('❌ Backend connection failed:', error.message);
        setBackendStatus('disconnected');
      }
    };
    checkHealth();
  }, []);

  // Handle authentication errors globally
  useEffect(() => {
    const handleAuthError = (error) => {
      if (error.response?.status === 401 || error.response?.status === 422) {
        if (user) {
          // User was logged in but token expired/invalid
          storage.clear();
          setUser(null);
          setAuthError('Your session has expired. Please login again.');
        }
      }
    };

    // This will be handled by the interceptor, but we can also check here
    return () => {};
  }, [user]);

  const handleAuthed = (info) => {
    setUser(info);
    setRefreshKey((k) => k + 1);
    setAuthError(null);
  };

  const logout = () => {
    storage.clear();
    setUser(null);
    setAuthError(null);
  };

  if (!user) {
    return (
      <div className="app">
        <div className="background-overlay"></div>
        <header className="main-header">
          <h1 className="main-title">
            <span className="title-icon">✈️</span>
            TripLogger
          </h1>
          <p className="tagline">Your Personal Travel Diary & Destination Recommender</p>
        </header>
        <main className="main-content">
          {backendStatus === 'disconnected' && (
            <div className="glass-card" style={{ background: 'rgba(255, 123, 123, 0.2)', borderColor: 'var(--danger)' }}>
              <p style={{ color: 'var(--danger)', margin: 0 }}>
                ⚠️ <strong>Backend Connection Issue:</strong> Cannot connect to backend server at {API_BASE}. 
                Please ensure the backend is running on port 5000.
              </p>
            </div>
          )}
          {authError && (
            <div className="glass-card" style={{ background: 'rgba(255, 200, 87, 0.2)', borderColor: 'var(--accent)' }}>
              <p style={{ color: 'var(--accent)', margin: 0 }}>
                ⚠️ {authError}
              </p>
            </div>
          )}
          <AuthCard onAuth={handleAuthed} />
          <div className="demo-info glass-card">
            <p>💡 <strong>Quick Start:</strong> Register a new account or use demo credentials</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="background-overlay"></div>
      <header className="main-header">
        <h1 className="main-title">
          <span className="title-icon">✈️</span>
          TripLogger
        </h1>
        <div className="user-info">
          <span className="user-greeting">👋 Welcome, {user.username || 'Traveler'}!</span>
          <button className="logout-btn" onClick={logout}>
            Logout
          </button>
        </div>
      </header>
      <main className="main-content">
        <TripForm onSaved={() => setRefreshKey((k) => k + 1)} />
        <TripList refreshKey={refreshKey} />
        <StatsCharts refreshKey={refreshKey} />
        <SpendingCard refreshKey={refreshKey} />
        <Recommendations refreshKey={refreshKey} />
      </main>
      <footer className="main-footer">
        <p>Built with ❤️ for Digital Transformation 2 - TripLogger Project</p>
      </footer>
    </div>
  );
}

export default App;
