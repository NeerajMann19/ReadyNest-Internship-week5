# Prism IQ — Full-Stack Data Intelligence & Predictive Analytics Workspace

Prism IQ is a production-grade, full-stack data intelligence platform and analytics workspace. It enables users to upload raw datasets, run automated data profiling, execute smart cleaning, perform exploratory data analysis (EDA), train local predictive machine learning models, extract AI-driven insights, and compile detailed reports.

---

## 🚀 Key Features & Pipeline Stages

The platform orchestrates a complete 6-stage data analytics lifecycle:

1. **Import (Data Ingestion)**
   - Support for multiple formats (CSV, Excel `.xlsx`).
   - Drag-and-drop file upload with validation controls.
2. **Profile (Automated Data Profiling)**
   - Interactive statistical auditing (row/column counts, missing values, duplicates, memory footprints).
   - Detailed per-column summary statistics (data type, uniqueness, statistical metrics).
3. **Clean (Smart Data Cleaning)**
   - In-memory simulation and preview of data cleaning operations.
   - Handles missing values, duplicates, type conversions, and outliers.
4. **Explore (Exploratory Data Analysis - EDA)**
   - Statistical distribution analysis.
   - Client-side Pearson Correlation Heatmap reconstruction supporting coefficient-strength thresholds.
5. **Predict (Predictive Machine Learning)**
   - Local training of classifier and regressor algorithms (Random Forest, Gradient Boosting, etc.).
   - Stricter cardinality guards and expected width checks to prevent memory OOM crashes.
   - Automated datetime feature engineering (`year`, `month`, `day_of_week`, `is_weekend`) during training and inference.
   - Interactive inference sandbox to run predictions on newly trained models.
6. **Insights (AI Anomaly Rules)**
   - Automated rule-based anomaly detection and recommendations.
   - Visual executive summary metrics and critical findings dashboards.
7. **Reports (Automated Reporting)**
   - Compilation of analytics findings into downloadable PDF, HTML, and Excel spreadsheets.
   - Programmatic file downloads utilizing authenticated API token-streaming.

---

## 🛠️ Technology Stack

* **Frontend**: React (v18) + Vite + Tailwind CSS + TypeScript + Recharts
* **Backend**: Python (v3.13) FastAPI + Uvicorn + SQLAlchemy Async (PostgreSQL) + Supabase
* **Cache**: Redis for session memory caching
* **ML Core**: Scikit-Learn + Pandas + Joblib

---

## ⚙️ Setup & Installation Instructions

### Prerequisites
* Python 3.10+
* Node.js 18+
* PostgreSQL & Redis instances running locally or via remote hosts (e.g. Supabase)

### 1. Clone the Repository
```bash
git clone https://github.com/NeerajMann19/ReadyNest-Internship-week5.git
cd ReadyNest-Internship-week5
```

### 2. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   Copy `.env.example` to `.env` and configure your database, Supabase, and Redis connections:
   ```bash
   cp .env.example .env
   ```
5. Apply database migrations and seed default records:
   ```bash
   python scripts/reset_db.py
   python scripts/seed_db.py
   ```
6. Run the FastAPI dev server:
   ```bash
   uvicorn app.main:app --reload
   ```

### 3. Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install node dependencies:
   ```bash
   npm install
   ```
3. Configure environment variables:
   Copy `.env.example` to `.env` and specify the API endpoint:
   ```bash
   cp .env.example .env
   ```
   *(Ensure `VITE_API_URL` matches your local backend address, e.g., `http://127.0.0.1:8000`)*
4. Run the Vite development server:
   ```bash
   npm run dev
   ```

---

## 📝 Project Context

This project is submitted as part of the **ReadyNest Internship (Week 5)** curriculum. It serves as a proof of concept for local, privacy-centric data analytics and predictive intelligence pipelines.
