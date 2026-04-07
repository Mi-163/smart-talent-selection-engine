# Approach Document

## 1. Solution Design Philosophy
The primary goal of the Smart Talent Selection Engine was to move modern HR workflows beyond traditional "keyword matching" (ATS 1.0) and transition into "semantic intent mapping" (ATS 2.0). 

Instead of writing brittle regex scripts to search for literal strings like "Python" or "SQL", the system's design leverages the reasoning capabilities of Generative AI. The architecture is built to understand intent—recognizing that a candidate who architected a "Distributed Data Warehouse" inherently possesses advanced database skills, even if specific keywords were omitted from their resume.

The solution is intentionally decoupled into a microservice-style architecture:
* An asynchronous orchestrator (FastAPI) handles the heavy lifting of file-reads and API network calls.
* A reactive presentation layer (Streamlit) handles state management and data visualization.

## 2. High-Level Tech Stack Choices
* **Language:** Python 3.9+ (Chosen for premier AI and data manipulation libraries).
* **AI Engine:** Google Gemini 2.5 Flash API (Chosen for its native multimodal document understanding).
* **Infrastructure:** Streamlit (UI), FastAPI (Routing), Neon Serverless Postgres (Persistence), SQLAlchemy (ORM).

## 3. What I Would Improve With More Time (Future Scope)

If given additional runway to scale this MVP into a production enterprise application, I would prioritize the following upgrades:

**Product Workflow Enhancements:**
1.  **Dual-Portal System (RBAC):** Expand the platform into a dual-portal Applicant Tracking System. This would include an Admin/Recruiter Portal (for opening/closing vacancies) and a public-facing Candidate Portal (where candidates directly upload their profiles).
2.  **Event-Driven Batch Processing:** Modify the analysis trigger so resumes are collected passively over time. Once the recruiter clicks "Close Vacancy," the backend automatically initiates the AI extraction and ranking queue for the entire batch.
3.  **Automated Communications (SMTP Integration):** Build a "1-Click Shortlist" feature. Recruiters can review the AI justifications for the Top 5 ranked candidates and approve automated, template-based interview invitation emails sent directly from the platform.

**Architectural Improvements:**
1.  **JWT Authentication:** Replace the frontend Streamlit session-state mockup with a robust JWT authentication system in FastAPI, complete with a secure `Users` table.
2.  **Cloud Blob Storage (AWS S3):** Stream uploaded resumes directly to an S3 bucket to ensure the API servers remain stateless and horizontally scalable, rather than storing files in a local directory.
3.  **Asynchronous Task Queues (Celery + Redis):** Offload the HTTP request loop to a background Celery worker to prevent browser timeouts when analyzing hundreds of resumes simultaneously.