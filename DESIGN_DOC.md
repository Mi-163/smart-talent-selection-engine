# Design Document

## 1. Tech Stack Chosen & Trade-Offs

**Backend: FastAPI vs. Flask/Django**
* **Chosen:** FastAPI.
* **Trade-off:** Django provides built-in ORMs and admin panels, but FastAPI’s native asynchronous support (`async def`) is critical. We traded built-in UI features for non-blocking I/O operations, ensuring the server doesn't freeze while waiting for external LLM APIs and heavy file uploads.

**AI Extraction: Gemini 2.5 Flash Multimodal vs. Traditional OCR (PyPDF2)**
* **Chosen:** Gemini Multimodal Vision.
* **Trade-off:** Traditional OCR libraries strictly read top-to-bottom, heavily mangling modern, non-linear resume layouts (e.g., sidebars, two-column formats). By passing the raw file bytes directly to a multimodal model, we traded slightly higher API latency for a massive increase in spatial and semantic accuracy.

**Database: PostgreSQL (Neon) vs. NoSQL (MongoDB)**
* **Chosen:** PostgreSQL.
* **Trade-off:** While NoSQL is great for unstructured data, the final outputs of our candidate evaluations are highly structured (Scores, Integers for Years of Experience, IDs). We chose a relational database to ensure ACID compliance and predictable schema enforcement.

**Frontend: Streamlit vs. React/Next.js**
* **Chosen:** Streamlit.
* **Trade-off:** We sacrificed highly customized CSS and granular component lifecycle control to achieve rapid MVP deployment. Streamlit allowed for pure Python UI generation, enabling fast iterations on data visualization features like leaderboards and dynamic progress bars within the 14-day window.

## 2. Edge Case Handling

1.  **LLM Hallucinations (JSON Formatting Drift):** Generative models occasionally return malformed JSON or alter key casing. A robust `try/except` extraction algorithm was built into the backend. It uses `.get()` fallbacks for variable capitalization and type-checking to flatten nested AI lists, guaranteeing database integrity regardless of LLM output variations.
2.  **Experience Inflation:** Academic projects can often trick basic parsers into awarding "years of experience." The prompt engineering enforces a strict penalty for candidates with 0 years of professional experience, preventing internships/projects from artificially inflating the core compatibility score.
3.  **Cross-Role Fallacy:** Comparing a "Data Scientist" score of 95% against a "Sales Rep" score of 95% is a logical edge case that breaks recruitment workflows. The UI actively prevents this by hiding the Detailed AI Justifications until a specific Job Title is selected from the filter dropdown.