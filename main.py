"""
Streamlit UI Application Module
================================
Provides a browser‑based interface that allows recruiters or candidates to

* upload a resume (PDF / DOCX / TXT)
* paste or upload a job description
* instantly receive a match‑score dashboard + downloadable written report

Run with:
    streamlit run ui_app.py
"""
from __future__ import annotations

import os
import tempfile
import logging
from pathlib import Path
from typing import Dict, Optional

import streamlit as st

from resume_parser import ResumeParser  # local module
from scoring import ResumeScorer, MatchResult  # local module
from visualizer import ResumeVisualizer  # local module
from report_gen import ReportGenerator  # local module

import traceback  # Add traceback for deeper debug

# ----------------------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

# ----------------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------------

def _save_uploaded_file(uploaded) -> Path:
    """Persist the uploaded file to a temporary file and return the path."""
    suffix = Path(uploaded.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.read())
        return Path(tmp.name)


def _run_full_analysis(
    resume_path: Path,
    job_desc: str,
    candidate: str,
    job_title: str,
) -> tuple[Dict, MatchResult, Dict[str, str], Dict[str, str]]:
    """Pipeline that ties together parser → scorer → visualiser → reporter."""
    # 1 ▸ Parse
    parser = ResumeParser()
    parsed_resume = parser.parse_resume(resume_path)

    # 2 ▸ Score
    scorer = ResumeScorer()
    match_result = scorer.calculate_match_score(parsed_resume, job_desc)
    logger.info(f"MATCH RESULT: {match_result}")  # Log for debugging

    # 3 ▸ Visualise
    viz = ResumeVisualizer()
    dashboard = viz.create_comprehensive_dashboard(match_result, candidate, job_title)

    # 4 ▸ Reports
    reporter = ReportGenerator()
    try:
        reports = reporter.generate_comprehensive_report(
            match_result, parsed_resume, job_desc, candidate, job_title
        )
    except Exception:
        tb = traceback.format_exc()
        logger.error("Report generation failed during execution:\n%s", tb)
        reports = {"error": f"Exception during report generation:\n{tb}"}

    # cleanup tmp resume file early
    try:
        resume_path.unlink(missing_ok=True)
    except Exception:
        pass

    logger.debug("Reports dict keys returned: %s", list(reports.keys()))

    return parsed_resume, match_result, dashboard, reports


# ----------------------------------------------------------------------------------
# Streamlit page configuration
# ----------------------------------------------------------------------------------
st.set_page_config(
    page_title="⚡ AI Resume Match Analyzer",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("⚡ AI Resume Match Analyzer")
st.write(
    "Upload a candidate resume and provide the job description.  \
    The app will parse the resume, calculate an overall match score, \
    visualise the breakdown, and generate a written report you can download."  # noqa: E501
)

# ----------------------------------------------------------------------------------
# Sidebar – inputs
# ----------------------------------------------------------------------------------
with st.sidebar:
    st.header("🗂️ Inputs")
    resume_file = st.file_uploader(
        label="Resume file (PDF, DOCX, or TXT)",
        accept_multiple_files=False,
        type=["pdf", "docx", "txt"],
    )

    jd_input_mode = st.radio("Job description input method", ["Paste text", "Upload TXT"])
    job_description: Optional[str] = None

    if jd_input_mode == "Paste text":
        job_description = st.text_area(
            "Paste the job description here", height=300, placeholder="Job description …"
        )
    else:
        jd_file = st.file_uploader("Upload JD (.txt)", type=["txt"])
        if jd_file is not None:
            job_description = jd_file.getvalue().decode("utf-8")

    st.markdown("---")
    st.header("🔖 Meta‑data")
    candidate_name = st.text_input("Candidate name", value="Candidate")
    job_title = st.text_input("Job title", value="Position")

    analyse_btn = st.button("🚀 Analyse Resume", type="primary")

# ----------------------------------------------------------------------------------
# Main panel – output
# ----------------------------------------------------------------------------------
if analyse_btn:
    if resume_file is None or not job_description:
        st.warning("Please provide **both** a resume file and a job description.")
        st.stop()

    # Store to tmp on disk so downstream libs (PyPDF2, docx) can open it.
    tmp_resume_path = _save_uploaded_file(resume_file)

    with st.spinner("Crunching numbers – this might take a moment …"):
        parsed, result, dash, reports = _run_full_analysis(
            tmp_resume_path, job_description, candidate_name, job_title
        )

    # ============================== EXECUTIVE SUMMARY =============================
    st.success("Analysis complete!")
    st.subheader("Executive summary")

    if "executive_summary" in reports:
        st.markdown(reports["executive_summary"])
    else:
        st.error("Executive summary could not be loaded.")
        st.code(reports.get("error", "Unknown error occurred"))
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Overall match score", f"{result.overall_score}%")
    with col2:
        status_text = "-"
        if "executive_summary" in reports and "OVERALL ASSESSMENT:" in reports["executive_summary"]:
            try:
                status_text = (
                    reports["executive_summary"].split("OVERALL ASSESSMENT:")[1].split("\n")[0].strip()
                )
            except Exception:
                pass
        st.metric("Status", status_text)

    # ============================== DASHBOARD VISUALS =============================
    st.markdown("## Visual dashboard")
    st.components.v1.html(dash.get("gauge", "<div>No gauge chart</div>"), height=420)

    colA, colB = st.columns(2)
    with colA:
        st.components.v1.html(dash.get("radar", "<div>No radar chart</div>"), height=520)
    with colB:
        st.components.v1.html(dash.get("skills_matrix", "<div>No matrix</div>"), height=420)

    st.components.v1.html(dash.get("breakdown", "<div>No breakdown chart</div>"), height=420)

    if "experience" in dash and dash["experience"]:
        st.components.v1.html(dash["experience"], height=350)

    st.markdown("### Recommendations")
    st.components.v1.html(dash.get("recommendations", "<div>No recs</div>"), height=320)

    # ============================== DOWNLOADS =====================================
    st.markdown("---")
    st.subheader("Download outputs")

    # Text report – only if generated
    if "full_report" in reports:
        st.download_button(
            label="📄 Full text report (.txt)",
            data=reports["full_report"],
            file_name=f"{candidate_name.replace(' ', '_').lower()}_analysis_report.txt",
            mime="text/plain",
        )

    # Dashboard HTML
    dashboard_html = ResumeVisualizer().export_dashboard_html(dash, candidate_name, job_title)
    st.download_button(
        label="📊 Interactive dashboard (.html)",
        data=dashboard_html,
        file_name=f"{candidate_name.replace(' ', '_').lower()}_dashboard.html",
        mime="text/html",
    )

# ----------------------------------------------------------------------------------
# Footer & credits
# ----------------------------------------------------------------------------------
st.markdown(
    "---\nDeveloped with ❤️ using Streamlit • ResumeParser • ResumeScorer • ResumeVisualizer\nand ReportGenerator modules. | © 2025"
)
