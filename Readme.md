# AI-Powered Environmental Intelligence System

An AI-powered environmental intelligence platform for real-time air quality monitoring, weather & traffic correlation, interactive pollution mapping, and historical time-series telemetry.

## Tech Stack

- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, Leaflet (`react-leaflet`)
- **Backend:** Python 3.12, FastAPI, HTTPX, Pydantic
- **Database:** InfluxDB v2 (Time-Series Database via Docker)
- **Data Sources:** OpenWeatherMap (Air Pollution, Weather, Geocoding), WAQI, OpenAQ v3, TomTom Traffic Flow, OpenStreetMap Nominatim

## Quickstart

### 1. Start InfluxDB
```cmd
docker compose up -d
```

### 2. Start Backend API
```cmd
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```
API Swagger Docs: `http://localhost:8000/docs`

### 3. Start Frontend Dashboard
```cmd
cd frontend
npm install
npm run dev
```
Dashboard URL: `http://localhost:5173`

### 4. Run Tests & Database Verification
```cmd
cd backend
venv\Scripts\pytest.exe -v
venv\Scripts\python.exe verify_database.py
```