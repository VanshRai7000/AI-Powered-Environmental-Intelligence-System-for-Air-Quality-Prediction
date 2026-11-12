# Environmental Intelligence System — Technical Documentation

## 1. Overview & Architecture

The Environmental Intelligence System collects, normalizes, aggregates, stores, and visualizes real-time environmental telemetry (Air Quality, Weather, and Road Traffic) for any user-selected location worldwide.

```text
React + TypeScript + Leaflet (Port 5173)
        │
        ▼ HTTP (Axios)
FastAPI Backend (Port 8000)
  ├── Geo Resolver (OpenWeather Geo + OpenStreetMap Nominatim)
  ├── Air Quality (OpenWeather Air Pollution -> WAQI -> OpenAQ)
  ├── Weather (OpenWeather Current Weather)
  ├── Traffic (TomTom Traffic Flow API)
  └── Data Cleaning & EPA AQI Computation
        │
        ▼ BackgroundTasks
InfluxDB v2 Time-Series Database (Port 8086)
```

---

## 2. Project Structure

```text
environmental-intelligence-system/
├── docker-compose.yml              # InfluxDB v2 container configuration
├── Readme.md                       # Quickstart overview
├── docs/
│   ├── TECHNICAL_DOCUMENTATION.md  # System architecture, API & DB docs
│   └── MILESTONE_1_SUBMISSION.md   # Milestone 1 review & verification evidence
├── backend/
│   ├── main.py                     # FastAPI entry point & CORS setup
│   ├── requirements.txt            # Python dependencies
│   ├── pytest.ini                  # Pytest async configuration
│   ├── verify_database.py          # Live InfluxDB verification script
│   ├── app/
│   │   ├── config/settings.py      # Pydantic environment settings
│   │   ├── database/influxdb.py    # InfluxDB client, write & Flux query helpers
│   │   ├── routes/
│   │   │   ├── health.py           # GET /health
│   │   │   ├── users.py            # POST/GET /api/users
│   │   │   ├── location.py         # POST /api/location, GET /api/location/search
│   │   │   ├── air_quality.py      # GET /api/air-quality/current & /stations
│   │   │   ├── weather.py          # GET /api/weather/current
│   │   │   └── environmental.py    # GET /api/environmental/current & /historical
│   │   ├── schemas/                # Pydantic request/response models
│   │   └── services/               # External API clients, geocoding, cleaning
│   └── tests/                      # Automated pytest suite (29 tests)
└── frontend/
    ├── index.html
    ├── package.json
    └── src/
        ├── App.tsx                 # Wrapped in ErrorBoundary
        ├── pages/Dashboard.tsx     # Main dashboard orchestrating all cards & map
        ├── components/
        │   ├── LocationCard.tsx    # City/locality search + browser GPS detect
        │   ├── AQICard.tsx         # 0-500 AQI display + pollutant grid
        │   ├── WeatherCard.tsx     # Temperature, humidity, wind, icon
        │   ├── TrafficCard.tsx     # TomTom speed & congestion level
        │   ├── PollutionMap.tsx    # Interactive React-Leaflet map & station panel
        │   ├── ErrorBoundary.tsx   # Global React error boundary
        │   ├── Header.tsx
        │   └── Sidebar.tsx         # Section navigation
        ├── services/               # Axios API modules
        └── types/                  # TypeScript interfaces
```

---

## 3. Application Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker Desktop (for InfluxDB v2)

### Step 1: Start InfluxDB
```cmd
docker compose up -d
```
InfluxDB Web UI runs at `http://localhost:8086`.

### Step 2: Configure Environment (`backend/.env`)
```env
APP_NAME=Environmental Intelligence System
APP_ENV=development

INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=<your_influxdb_token>
INFLUXDB_ORG=environmental-intelligence
INFLUXDB_BUCKET=environmental_data

OPENWEATHER_API_KEY=<your_openweather_api_key>
OPENAQ_API_KEY=<your_openaq_api_key>
WAQI_API_TOKEN=<your_waqi_token>
TOMTOM_API_KEY=<your_tomtom_api_key>
```

### Step 3: Start Backend
```cmd
cd backend
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Interactive Swagger API docs: `http://localhost:8000/docs`

### Step 4: Start Frontend
```cmd
cd frontend
npm install
npm run dev
```
Dashboard URL: `http://localhost:5173`

---

## 4. API Endpoints Reference

### Health Check
- **`GET /health`**
  - **Response:** `{ "status": "healthy", "database": "connected" }`

### Location Management
- **`GET /api/location/search?query=Paonta Sahib`**
  - Resolves city, town, or neighborhood queries into coordinates via OpenWeather Geocoding + Nominatim.
  - **Response:**
    ```json
    [
      {
        "name": "Paonta Sahib",
        "state": "Himachal Pradesh",
        "country": "IN",
        "latitude": 30.43844,
        "longitude": 77.62118,
        "display_name": "Paonta Sahib, Himachal Pradesh, IN"
      }
    ]
    ```
- **`POST /api/location`**
  - Body: `{ "latitude": 30.43844, "longitude": 77.62118 }`

### Combined Environmental Data (Primary Dashboard Endpoint)
- **`GET /api/environmental/current?location=Paonta Sahib`** *(also accepts `?latitude=&longitude=`)*
  - Aggregates Air Quality, Weather, and Traffic, and persists the snapshot into InfluxDB in the background.
  - **Response:**
    ```json
    {
      "location": {
        "name": "Paonta Sahib, Himachal Pradesh, IN",
        "latitude": 30.43844,
        "longitude": 77.62118
      },
      "air_quality": {
        "aqi": 142.0,
        "pollutants": [
          { "pollutant": "PM2.5", "value": 52.1, "unit": "µg/m³" },
          { "pollutant": "PM10", "value": 88.4, "unit": "µg/m³" }
        ],
        "station_name": "Paonta Sahib, Himachal Pradesh, IN",
        "timestamp": "2026-11-12T04:00:00+00:00",
        "source": "OpenWeatherMap"
      },
      "weather": {
        "temperature": 21.5,
        "feels_like": 21.0,
        "humidity": 68,
        "wind_speed_kmh": 7.2,
        "description": "clear sky",
        "icon": "01d"
      },
      "traffic": {
        "current_speed_kmph": 38,
        "free_flow_speed_kmph": 45,
        "congestion_percent": 15.56,
        "congestion_level": "Low"
      },
      "collected_at": "2026-11-12T04:45:38+00:00"
    }
    ```

### Historical Time-Series Data
- **`GET /api/environmental/historical?location=Paonta Sahib, Himachal Pradesh, IN&range=24h`**
  - Queries InfluxDB over `1h`, `6h`, `12h`, `24h`, `48h`, `7d`, or `30d`.

### Air Quality & Monitoring Stations
- **`GET /api/air-quality/current?location=Paonta Sahib`**
- **`GET /api/air-quality/stations?location=Paonta Sahib`**
  - Combines WAQI map bounds and OpenAQ stations within 25 km for the interactive map.

### Weather
- **`GET /api/weather/current?location=Paonta Sahib`**

---

## 5. External Service Integrations

| Provider | Usage | Notes |
|---|---|---|
| **OpenWeatherMap** | Primary Air Pollution (`/data/2.5/air_pollution`), Current Weather (`/data/2.5/weather`), and Geocoding (`/geo/1.0/direct`) | Provides global grid coverage; raw PM2.5 & PM10 are converted to 0–500 US EPA AQI in `openweather_service.py`. |
| **WAQI** | Air quality fallback + Regional map stations (`/map/bounds/`) | Supplies nearby physical monitoring station AQI pins. |
| **OpenAQ v3** | Ground station discovery (`/v3/locations`) | Limited to 25 km max search radius. |
| **OpenStreetMap Nominatim** | Hyper-local geocoding & reverse geocoding | Resolves towns, suburbs, and neighborhoods accurately. |
| **TomTom Traffic API** | Real-time road flow speed & congestion calculation | Computes congestion `%` from `currentSpeed` vs `freeFlowSpeed`. |

---

## 6. Database Schema (InfluxDB v2)

- **Bucket:** `environmental_data`
- **Measurement:** `environmental_measurement`
- **Tags:** `location_name`, `city`, `location` (`lat,lon` rounded to 3 decimals)
- **Fields:** `latitude`, `longitude`, `aqi`, `pollutant_pm2_5`, `pollutant_pm10`, `pollutant_no2`, `pollutant_o3`, `pollutant_co`, `pollutant_so2`, `pollutant_nh3`, `pollutant_no`, `temperature`, `feels_like`, `humidity`, `wind_speed_kmh`, `congestion_percent`, `current_speed_kmph`, `free_flow_speed_kmph`
- **Timestamp Precision:** Nanoseconds (`WritePrecision.NS`, UTC)

---

## 7. Known Implementation Limitations

1. **User Accounts & Health Profiles (`users.py`, `profile.py`):** User registration currently uses an in-memory Python dictionary (`users_db`) rather than a persistent SQL database; `HealthProfile` schema is defined but not yet connected to personalized alerts.
2. **Desktop Browser Geolocation:** Desktops/laptops without GPS hardware approximate coordinates via ISP IP routing. The City/Locality search bar solves this by allowing direct entry of exact locations.
3. **OpenAQ Ground Sensor Coverage:** Smaller towns without ground monitors within 25 km rely on OpenWeather's satellite/CAMS model and regional WAQI stations.
4. **Automated Polling:** InfluxDB records are written on user/API requests; scheduled periodic background polling (e.g., every 15 minutes) is planned for Milestone 2.

