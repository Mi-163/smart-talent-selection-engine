# Smart Talent Selection Engine
 **[Watch the Demo Video Here](https://drive.google.com/file/d/1taDWogWa23gH29TPGSm-O9EKVWn-fZOn/view?usp=sharing)**
## The Problem
Modern HR teams struggle to evaluate creatively formatted, non-linear resumes using traditional keyword-matching ATS software. This results in highly qualified candidates being automatically rejected due to parsing errors, while recruiters waste hours manually cross-referencing surviving candidate skills against complex job descriptions.

## The Solution
The Smart Talent Selection Engine is an intelligent, AI-driven recruiter dashboard that shifts from brittle "keyword matching" to "semantic intent mapping." Instead of relying on traditional OCR, the system utilizes multimodal Generative AI to visually and semantically ingest diverse resume formats (PDFs, DocX, and Images) without losing context. It normalizes these unstructured documents into structured data, dynamically ranks candidates against a specific Job Description (JD) using a weighted scoring algorithm, and provides recruiters with a transparent, 2-sentence AI justification for the top 5 candidates to accelerate decision-making.

## Tech Stack
* **Programming Language:** Python 3.9+
* **Frontend Framework:** Streamlit (UI & Session-State Authentication)
* **Backend Framework:** FastAPI (Async API Routing & File Handling)
* **Database:** PostgreSQL (Hosted via Neon Serverless Postgres)
* **ORM & Validation:** SQLAlchemy, Pydantic
* **AI & APIs:** Google Gemini 2.5 Flash API (Multimodal LLM)
* **File Parsing:** `pdfplumber`, `python-docx`

## Setup Instructions

**1. Clone the Repository**
```bash
git clone https://github.com/Mi-163/smart-talent-selection-engine.git
cd smart-talent-selection-engine
```

**2. Create and Activate a Virtual Environment**
```bash
python -m venv venv
# On Mac/Linux:
source venv/bin/activate  
# On Windows:
venv\Scripts\activate
```

**3. Install Dependencies**
```bash
pip install -r requirements.txt
```

**4. Configure Environment Variables**
Create a `.env` file in the root directory of the project and add your database and AI API credentials:
```env
GEMINI_API_KEY=your_google_api_key_here
DATABASE_URL=your_neon_postgres_connection_string_here
```

**5. Start the Backend Server (FastAPI)**
In your terminal, start the backend to handle the APIs and database connections:
```bash
uvicorn main:app --reload
```
*(The backend will run locally on http://127.0.0.1:8000)*

**6. Start the Frontend Application (Streamlit)**
Open a **new** terminal window, ensure your virtual environment is activated, and run the UI:
```bash
streamlit run frontend.py
```
*(The application will automatically open in your web browser. Use **Admin ID:** `admin` and **Password:** `admin123` to log in).*
