"""
Smart Talent Selection Engine - Frontend Application

This module provides the interactive Streamlit user interface for the recruiter portal.
It handles session-state authentication, dynamic data visualization of candidate rankings,
and provides a robust bulk-upload interface for multi-format resumes.
Interacts with the FastAPI backend via RESTful HTTP requests.
"""
import time
import pandas as pd
import requests
import streamlit as st


# Page configuration

st.set_page_config(
    page_title="Smart Talent Selection",
    layout="wide",
)


# Authentication


# Initialise session state keys on first load
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "login_error" not in st.session_state:
    st.session_state["login_error"] = False


def handle_login():
    """
    Callback attached to the Login button.
    Authenticates recruiter credentials and updates session state prior to page re-rendering.
    This prevents UI flickering and race conditions inherent to Streamlit's execution model.
    """
    admin_id = st.session_state.get("input_admin_id", "")
    password = st.session_state.get("input_password", "")

    if admin_id == "admin" and password == "admin123":
        st.session_state["logged_in"] = True
        st.session_state["login_error"] = False
    else:
        st.session_state["logged_in"] = False
        st.session_state["login_error"] = True


# Login Screen
if not st.session_state["logged_in"]:

    st.title("🔒 Recruiter Access")
    st.write("Please log in to view the Talent Dashboard.")

    st.text_input(
        "Admin ID",
        placeholder="Enter your username",

        key="input_admin_id",
    )
    st.text_input(
        "Enter Password",
        type="password",

        key="input_password",
    )

    st.button("Login", on_click=handle_login)

    if st.session_state["login_error"]:
        st.error("Invalid Admin ID or Password. Please try again.")


# Main app

else:

    # Sidebar — Logout

    def handle_logout():
        """Callback to cleanly reset all auth-related session state."""
        st.session_state["logged_in"] = False
        st.session_state["login_error"] = False

    with st.sidebar:
        st.markdown("### 👤 Recruiter Panel")
        st.button("Logout", on_click=handle_logout)

    # App title and tabs

    st.title("Smart Talent Selection Engine")

    tab1, tab2 = st.tabs(["📊 Recruiter Dashboard", "📥 Bulk Upload Portal"])

    # Recruiter dashboard

    with tab1:

        st.header("Active Talent Pool Overview")

        try:
            response = requests.get("http://127.0.0.1:8000/candidates/")

            if response.status_code == 200:
                candidates = response.json()

                if len(candidates) > 0:
                    df = pd.DataFrame(candidates)

                    # Role filter dropdown
                    job_roles = df["job_title"].unique().tolist()
                    selected_role = st.selectbox(
                        "🎯 Filter Dashboard by Job Role:",
                        ["All Roles"] + job_roles,
                    )

                    if selected_role != "All Roles":
                        df = df[df["job_title"] == selected_role]
                    df = df.sort_values(
                        by="compatibility_score", ascending=False).reset_index(drop=True)

                    if not df.empty:

                        # Metrics
                        col1, col2, col3 = st.columns(3)
                        col1.metric(f"Resumes for '{selected_role}'", len(df))
                        col2.metric("Highest Score",
                                    f"{df['compatibility_score'].max()}%")
                        col3.metric("Average Score",
                                    f"{int(df['compatibility_score'].mean())}%")

                        st.divider()

                        # Leaderboard
                        st.subheader(f"🏆 Leaderboard: {selected_role}")

                        def get_status(score: int) -> str:
                            """
                            Evaluates the AI compatibility score and assigns a visual 
                            traffic-light status indicator for rapid recruiter scanning.
                            """
                            if score >= 80:
                                return "🟢 Strong"
                            elif score >= 50:
                                return "🟡 Potential"
                            else:
                                return "🔴 Weak"

                        df["status"] = df["compatibility_score"].apply(
                            get_status)

                        display_df = df[[
                            "id", "status", "compatibility_score",
                            "years_experience", "top_skills", "resume_url",
                        ]].copy()

                        display_df.columns = [
                            "ID", "Match Status", "Score (%)",
                            "Years Exp", "Top Skills", "Resume Link",
                        ]

                        st.dataframe(
                            display_df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "Score (%)": st.column_config.ProgressColumn(
                                    "Score (%)",
                                    help="AI Compatibility Score",
                                    format="%d",
                                    min_value=0,
                                    max_value=100,
                                ),
                                "Resume Link": st.column_config.LinkColumn(
                                    "Original Resume",
                                    help="Click to open the uploaded file in a new tab",
                                    display_text="📄 View File",
                                ),
                            },
                        )

                        st.divider()

                        # Detailed AI Cards
                        if selected_role != "All Roles":
                            st.subheader("📄 Top 5 Candidate Reports")

                        # Render detailed AI justification cards for the top 5 ranking candidates
                            for _, row in df.head(5).iterrows():
                                with st.expander(
                                    label=f"Candidate {row['id']} | Match Score: {row['compatibility_score']}%",
                                    expanded=False,
                                ):
                                    col_a, col_b = st.columns(2)
                                    col_a.write(
                                        f"**Years of Experience:** {row['years_experience']}")
                                    col_b.write(
                                        f"**Top Skills:** {row['top_skills']}")
                                    st.markdown("**AI Justification:**")
                                    st.info(row["summary"])
                        else:
                            st.info(
                                "💡 Select a specific Job Role from the dropdown above to view the Top 5 AI Candidate Reports.")

                    else:
                        st.warning(
                            f"No candidates found for '{selected_role}'.")

                else:
                    st.info(
                        "No candidates processed yet. Go to the **Upload Portal** tab to get started!")

            else:
                st.error(f"Backend returned status {response.status_code}.")

        except Exception as e:
            st.error(
                f"⚠️ Backend connection error. Is the FastAPI server running?\n\nDetails: {e}")

    # Bulk upload portal

    with tab2:

        st.markdown(
            "Upload multiple candidate resumes and rank them against a specific job role.")

        col_upload, col_job = st.columns(2)

        with col_upload:
            st.header("1. Upload Resumes")
            uploaded_files = st.file_uploader(
                label="Upload Resumes (PDF, DOCX, Images)",
                type=["pdf", "docx", "png", "jpg", "jpeg"],
                accept_multiple_files=True,
            )

        with col_job:
            st.header("2. Job Details")
            job_title = st.text_input(
                "Job Role Title",
                placeholder="e.g., Senior Python Developer",
            )
            job_description = st.text_area(
                "Paste the Job Description here",
                height=150,
            )

        if st.button("Analyze & Rank All Candidates"):

            if uploaded_files and job_description and job_title:

                st.success(
                    f"Starting analysis for **{len(uploaded_files)}** candidate(s) "
                    f"for the **'{job_title}'** role…"
                )

                progress_bar = st.progress(0)
                total_files = len(uploaded_files)

                for i, uploaded_file in enumerate(uploaded_files):

                    with st.status(
                        label=f"Processing: {uploaded_file.name}…",
                        expanded=True,
                    ) as status:

                        files = {
                            "file": (
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                                uploaded_file.type,
                            )
                        }

                        upload_response = requests.post(
                            "http://127.0.0.1:8000/upload/",
                            files=files,
                        )

                        if upload_response.status_code == 200:
                            upload_data = upload_response.json()
                            semantic_profile = upload_data.get(
                                "semantic_profile", "")
                            resume_url = upload_data.get("resume_url", "")

                            rank_payload = {
                                "job_title": job_title,
                                "job_description": job_description,
                                "candidate_profile": semantic_profile,
                                "resume_url": resume_url,
                            }

                            rank_response = requests.post(
                                "http://127.0.0.1:8000/rank/",
                                json=rank_payload,
                            )

                            if rank_response.status_code == 200:
                                score = (
                                    rank_response.json()
                                    .get("ranking_result", {})
                                    .get("Compatibility_Score", 0)
                                )
                                status.update(
                                    label=f"✅ Completed: {uploaded_file.name} — Score: {score}%",
                                    state="complete",
                                    expanded=False,
                                )
                            else:
                                status.update(
                                    label=f"❌ Ranking failed for: {uploaded_file.name}",
                                    state="error",
                                )

                        else:
                            status.update(
                                label=f"❌ Extraction failed for: {uploaded_file.name}",
                                state="error",
                            )

                    progress_bar.progress((i + 1) / total_files)
                    time.sleep(4)

                st.success(
                    " Batch processing complete! "
                    "Switch to the **Recruiter Dashboard** tab to view results."
                )

            else:
                st.warning(
                    "Please fill out the **Job Title**, **Job Description**, "
                    "AND upload at least one resume file before proceeding."
                )
