"""
Smart Talent Selection Engine - Backend API

This module serves as the FastAPI backend for the recruiter dashboard.
It handles file ingestion (PDF, DOCX, Images), orchestrates the Google Gemini 
multimodal AI for semantic resume extraction, and manages PostgreSQL database 
transactions for candidate ranking and scoring.
"""
import os
import io
import json
from fastapi import FastAPI, File, UploadFile, Depends
import pdfplumber
import docx
from dotenv import load_dotenv
import google.generativeai as genai
from pydantic import BaseModel
import os
from fastapi.staticfiles import StaticFiles

# SQLAlchemy Imports
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session


# Load keys
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Database confifuration
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define Schema


class CandidateRecord(Base):
    __tablename__ = "candidate_evaluations_v4"
    id = Column(Integer, primary_key=True, index=True)
    job_title = Column(String)
    job_description = Column(String)
    profile_text = Column(String)
    years_experience = Column(Integer)
    top_skills = Column(String)
    compatibility_score = Column(Integer)
    summary = Column(String)
    resume_url = Column(String)


# Create table in Neon
Base.metadata.create_all(bind=engine)

# Database dependency(open and close connection)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(title="Smart Talent Selection Engine")

# create folder and host files
os.makedirs("uploaded_resumes", exist_ok=True)
app.mount("/resumes", StaticFiles(directory="uploaded_resumes"), name="resumes")


class RankRequest(BaseModel):
    """
    Pydantic schema for data validation on the /rank/ endpoint.
    Ensures the frontend sends all required strings before processing.
    """
    job_title: str
    job_description: str
    candidate_profile: str
    resume_url: str


@app.get("/")
def read_root():
    return {"message": "Welcome to the Smart Talent Selection Engine Backend! Server is running."}


@app.post("/upload/")
async def upload_resume(file: UploadFile = File(...)):
    file_content = await file.read()
    filename_lower = file.filename.lower()
    file_path = f"uploaded_resumes/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(file_content)

    # Generate the clickable URL
    generated_url = f"http://127.0.0.1:8000/resumes/{file.filename}"
    # initialize AI model
    model = genai.GenerativeModel(
        'gemini-2.5-flash',
        generation_config={"temperature": 0.0}
    )

    prompt = """
    You are an expert HR Tech AI. Analyze the provided resume and extract the core technical profile.
    Move beyond simple keyword matching and group the candidate's skills based on intent.
    
    Return the response ONLY as a structured JSON object with the following keys:
    - "Skills": A list of categorized skills.
    - "Experience_Summary": A brief 2-sentence summary of their professional background.
    - "Years_Of_Experience": An integer estimating their total years of work experience.
    """

    # multiformat logic router
    try:
        if filename_lower.endswith('.pdf'):
            # handle pdfs
            extracted_text = ""
            with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"
            ai_response = model.generate_content(
                [prompt, "Resume Text:\n" + extracted_text])

        elif filename_lower.endswith('.docx'):
            # handle word doc
            extracted_text = ""
            doc = docx.Document(io.BytesIO(file_content))
            for para in doc.paragraphs:
                extracted_text += para.text + "\n"
            ai_response = model.generate_content(
                [prompt, "Resume Text:\n" + extracted_text])

        elif filename_lower.endswith(('.png', '.jpg', '.jpeg')):
            # handle image
            image_part = {
                "mime_type": file.content_type,
                "data": file_content
            }
            # pass raw image dictionary directly to Gemini
            ai_response = model.generate_content([prompt, image_part])

        else:
            return {"error": "Unsupported file format."}

    except Exception as e:
        return {"error": f"Failed to process file: {str(e)}"}

    return {
        "filename": file.filename,
        "semantic_profile": ai_response.text,
        "resume_url": generated_url
    }


@app.post("/rank/")
async def rank_candidate(request: RankRequest, db: Session = Depends(get_db)):

    score = 0
    summary = "Analysis failed."
    years_exp = 0
    top_skills_str = "None extracted"

    model = genai.GenerativeModel(
        'gemini-2.5-flash',
        generation_config={"temperature": 0.0}
    )

    prompt = f"""
    You are an expert technical recruiter. Evaluate the candidate's profile against the job description using THIS STRICT SCORING RUBRIC:
    
    - Skills Match (0-40 points): Award points based on the presence of core technologies requested.
    - Experience Depth (0-40 points): Deduct points heavily if the candidate lacks the required years of experience. A candidate with 0 years of professional experience should receive very few points here.
    - Domain Relevance (0-20 points): Award points if the candidate's projects or background align with the core job tasks (e.g., AI API integration).
    
    Job Description:
    {request.job_description}
    
    Candidate Profile:
    {request.candidate_profile}
    
    Return the response ONLY as a valid, raw JSON object (no markdown formatting, no ```json, just the brackets) with the following keys:
    - "Compatibility_Score": The final calculated integer score from 0 to 100.
    - "Summary_Of_Fit": A 2-sentence justification explaining exactly how you calculated those points.
    """

    try:
        ai_response = model.generate_content(prompt)

        # Extract Score and Summary
        try:
            ai_data = json.loads(ai_response.text.strip())
            score = ai_data.get("Compatibility_Score", 0)
            summary = ai_data.get("Summary_Of_Fit", "No summary provided.")
        except json.JSONDecodeError:
            summary = "Error parsing AI score response."

        # Extract Years Exp and Top Skills flexibly

        try:
            # JSON cleaning
            clean_text = request.candidate_profile.replace(
                "```json", "").replace("```", "").strip()
            profile_dict = json.loads(clean_text)

            # Handle both uppercase and lowercase keys
            years_exp = profile_dict.get(
                "Years_Of_Experience", profile_dict.get("years_of_experience", 0))
            skills_data = profile_dict.get(
                "Skills", profile_dict.get("skills", []))

            all_skills = []

            # AI returned a dictionary (e.g., {"Languages": ["Python"], "Tools": ["Git"]})
            if isinstance(skills_data, dict):
                for val in skills_data.values():
                    if isinstance(val, list):
                        all_skills.extend(val)
                    elif isinstance(val, str):
                        all_skills.append(val)

            # AI returned a list
            elif isinstance(skills_data, list):
                for item in skills_data:
                    if isinstance(item, dict):
                        # Look for "Items" or "items"
                        all_skills.extend(
                            item.get("Items", item.get("items", [])))
                    elif isinstance(item, str):
                        all_skills.append(item)

            # Format the final text output
            if len(all_skills) > 0:
                top_skills_str = ", ".join(all_skills[:5])
                if len(all_skills) > 5:
                    top_skills_str += "..."

        except Exception:
            top_skills_str = "Skills parsing failed"
    except Exception as e:
        summary = f"API Error: {str(e)}"

   # Save everything to Neon Database
    new_record = CandidateRecord(
        job_title=request.job_title,
        job_description=request.job_description,
        profile_text=request.candidate_profile,
        years_experience=years_exp,
        top_skills=top_skills_str,
        compatibility_score=score,
        summary=summary,
        resume_url=request.resume_url
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    return {
        "message": "Successfully saved to database!",
        "database_id": new_record.id,
        "ranking_result": {"Compatibility_Score": score, "Summary_Of_Fit": summary}
    }
# dashboard data retrieval


@app.get("/candidates/")
def get_all_candidates(db: Session = Depends(get_db)):
    # query the database for all records, ordered by highest score first
    records = db.query(CandidateRecord).order_by(
        CandidateRecord.compatibility_score.desc()).all()
    return records
