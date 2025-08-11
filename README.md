# 🌊 HAB Risk Analysis Dashboard — CloudForgeX6

An **AI-assisted environmental monitoring platform** for assessing Harmful Algal Bloom (HAB) risk using satellite-derived measurements, historical event data, and interactive visualizations.

This project combines **PostgreSQL, Flask, React, Leaflet, and Anthropic Claude 3.5 Sonnet** to provide accessible, data-driven HAB risk insights for researchers, agencies, and industry stakeholders.

---

## 🚀 Features

- **On-Demand Risk Assessment**
  - Multi-factor scoring using chlorophyll-a, sea surface temperature, turbidity, and other parameters.
  - Risk interpretation generated via LLM (Claude 3.5 Sonnet).

- **Interactive Data Visualization**
  - Leaflet maps for geographic exploration of HAB sites.
  - Time-series plots of environmental measurements with Recharts.

- **Flexible Data Queries**
  - Site and date range filters with automatic min/max constraints.
  - Dynamic measurements fetching from PostgreSQL.

- **Conversational Chatbot**
  - Context-aware marine science Q&A powered by Claude API.
  - Chat history for iterative questioning.

---

## 🗄 Data Sources

- **Copernicus Marine Data** (CSV exports)
  - Chlorophyll-a concentration
  - Sea surface temperature
  - Turbidity

- **HAEDAT** (Historical Bloom Events)
  - Event date, location, and species details
  - Economic and ecological impacts

> **Note:** Direct NetCDF integration and automated ingestion are planned for future releases.

---

## 🏗 Technology Stack

**Frontend**
- React 18 + Vite
- Tailwind CSS
- Leaflet (maps)
- Recharts (charts)

**Backend**
- Python 3.10 + Flask
- SQLAlchemy ORM
- Pandas / NumPy
- Docker + Nginx

**Database**
- PostgreSQL (Neon.tech / Supabase in earlier versions)

**AI Integration**
- Anthropic Claude 3.5 Sonnet API
- Custom prompt engineering for marine environmental context

---

## 📦 Project Structure

```
root/
├── backend/
│   ├── app.py
│   ├── services/
│   │   ├── llm_service.py
│   │   ├── measurements_service.py
│   ├── models/
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   ├── pages/
│   ├── package.json
├── docker-compose.yml
└── README.md
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ask-llm` | POST | Sends site, date range, and user question to LLM for analysis |
| `/api/measurements` | GET | Fetches measurements with filters |
| `/api/discovery/sites` | GET | Lists available sites with metadata |
| `/api/summary` | GET | Provides dataset statistics |
| `/api/sites/<site>/stats` | GET | Site-specific aggregated statistics |

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/KhushPoddar11/CloudForgeX6-LLM-Dashboard-for-HAB-Alerts.git
cd CloudForgeX6-LLM-Dashboard-for-HAB-Alerts
```

### 2️⃣ Environment Variables
In `backend/.env`:
```
ANTHROPIC_API_KEY=your_api_key_here
DATABASE_URL=postgresql+psycopg2://user:password@host:port/dbname
```

### 3️⃣ Run with Docker
```bash
docker-compose up --build
```

---
