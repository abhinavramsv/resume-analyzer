import os
import tempfile
import logging
import traceback
from pathlib import Path
from typing import Dict, Optional

import streamlit as st

from resume_parser import ResumeParser
from scoring import ResumeScorer, MatchResult
from visualizer import ResumeVisualizer
from report_gen import ReportGenerator

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

def _save_uploaded_file(uploaded) -> Path:
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
    parser = ResumeParser()
    parsed_resume = parser.parse_resume(resume_path)

    scorer = ResumeScorer()
    match_result = scorer.calculate_match_score(parsed_resume, job_desc)

    viz = ResumeVisualizer()
    dashboard = viz.create_comprehensive_dashboard(match_result, candidate, job_title)

    reporter = ReportGenerator()
    try:
        reports = reporter.generate_comprehensive_report(
            match_result, parsed_resume, job_desc, candidate, job_title
        )
    except Exception:
        reports = {"error": traceback.format_exc()}

    try:
        resume_path.unlink(missing_ok=True)
    except:
        pass

    return parsed_resume, match_result, dashboard, reports

st.set_page_config(
    page_title="AI Resume Match Analyzer",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("⚡ AI Resume Match Analyzer")
st.write("Upload a resume and job description to receive a match score, dashboard, and report.")

with st.sidebar:
    st.header("🗂️ Inputs")
    resume_file = st.file_uploader(
        label="Resume file (PDF, DOCX, or TXT)",
        type=["pdf", "docx", "txt"],
    )

    jd_input_mode = st.radio("Job description input method", ["Paste text", "Upload TXT"])
    job_description = None

    if jd_input_mode == "Paste text":
        job_description = st.text_area("Paste the job description here", height=300)
    else:
        jd_file = st.file_uploader("Upload JD (.txt)", type=["txt"])
        if jd_file:
            job_description = jd_file.getvalue().decode("utf-8")

    st.markdown("---")
    st.header("🔖 Meta‑data")
    candidate_name = st.text_input("Candidate name", value="Candidate")
    job_title = st.text_input("Job title", value="Position")
    analyse_btn = st.button("🚀 Analyse Resume", type="primary")

if analyse_btn:
    if not resume_file or not job_description:
        st.warning("Please provide both a resume file and a job description.")
        st.stop()

    tmp_resume_path = _save_uploaded_file(resume_file)

    with st.spinner("Analyzing..."):
        parsed, result, dash, reports = _run_full_analysis(
            tmp_resume_path, job_description, candidate_name, job_title
        )

    st.success("Analysis complete!")
    st.subheader("Executive summary")

    if "executive_summary" in reports:
        st.markdown(reports["executive_summary"])
    else:
        st.error("Report generation failed.")
        st.code(reports.get("error", "Unknown error"))
        st.stop()

    c1, c2 = st.columns(2)
    c1.metric("Overall match score", f"{result.overall_score}%")
    
    status = "-"
    if "OVERALL ASSESSMENT:" in reports.get("executive_summary", ""):
        status = reports["executive_summary"].split("OVERALL ASSESSMENT:")[1].split("\n")[0].strip()
    c2.metric("Status", status)

    st.markdown("## Visual dashboard")
    st.components.v1.html(dash.get("gauge", ""), height=420)

    colA, colB = st.columns(2)
    with colA:
        st.components.v1.html(dash.get("radar", ""), height=520)
    with colB:
        st.components.v1.html(dash.get("skills_matrix", ""), height=420)

    st.components.v1.html(dash.get("breakdown", ""), height=420)
    if dash.get("experience"):
        st.components.v1.html(dash["experience"], height=350)
    st.components.v1.html(dash.get("recommendations", ""), height=320)

    st.markdown("---")
    st.subheader("Download outputs")

    if "full_report" in reports:
        st.download_button(
            label="📄 Full text report (.txt)",
            data=reports["full_report"],
            file_name=f"{candidate_name.lower().replace(' ', '_')}_report.txt",
            mime="text/plain",
        )

    export_viz = ResumeVisualizer()
    dash_html = export_viz.export_dashboard_html(dash, candidate_name, job_title)
    st.download_button(
        label="📊 Interactive dashboard (.html)",
        data=dash_html,
        file_name=f"{candidate_name.lower().replace(' ', '_')}_dashboard.html",
        mime="text/html",
    )

st.markdown(

    "---\nDeveloped using Streamlit by Abhinav Ram • ResumeParser • ResumeScorer • ResumeVisualizer\nand ReportGenerator modules. | © 2025"

)
