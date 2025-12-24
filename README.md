# TripLogger - Personal Travel Diary & Destination Recommender

A full-stack web application for logging travel experiences and getting personalized destination recommendations.

## Feature description

- **Trip Management**: Add, edit, delete, and view travel history
- **Statistics & Analytics**: Visual charts showing travel patterns and spending
- **Destination Recommendations**: AI-powered suggestions based on travel history and current world conseus
- **User Authentication**: Secure JWT-based authentication system
- **Responsive Design**: Modern glass-morphism UI 

## Prerequisites

- Docker and Docker Compose
- Web browser (Chrome, Firefox, Safari, Edge)
- 4GB RAM minimum
- Ports 3000 and 5000 available

## Setup Instructions

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd triplogger_incomplete
```

### 2. Start Application
```bash
docker compose up 
```

### 3. Access Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000

### 4. Login
Use demo account:
- **Username**: `demo`
- **Password**: `demo123`



## Project Structure
```
triplogger_incomplete/
├── frontend-react/          # React frontend application
|   ├── Dockerfile
│   ├── src/
│   │   ├── App.js          # Main application component
│   │   └── App.css         # Styling and themes
│   └── public/             # Static assets
├── backend/                # Flask backend API
|   ├── Dockerfile         
│   ├── app.py             # Main Flask application
│   ├── db.py              # Database configuration
│   └── triplogger.db      # SQLite database
└── docker-compose.yml     # Container orchestration
```

## Technology Stack

- **Frontend**: React 18, Axios, Chart.js
- **Backend**: Flask, Flask-JWT-Extended, Flask-CORS
- **Database**: SQLite
- **Containerization**: Docker, Docker Compose
- **Authentication**: JWT tokens
- **Styling**: CSS3 with Glass-morphism design

## Troubleshooting

### Common Issues
1. **Port conflicts**: Ensure ports 3000 and 5000 are free
2. **Database not updating**: Refresh DBeaver connection
3. **Login issues**: Use demo account credentials
4. **Container issues**: Run `docker compose down && docker compose up -d`

### Logs
```bash
# Frontend logs
docker logs triplogger_frontend

# Backend logs
docker logs triplogger_backend
```
## Project Demo Video
Drive link:
https://drive.google.com/file/d/18Ic162-buJdS7pi1m5D7fNdh495UYCQX/view?usp=drive_link
