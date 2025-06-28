"""
Streamlit UI Application Module
================================
Provides a browser‑based interface that allows recruiters or candidates to

* upload a resume (PDF / DOCX / TXT)
* paste or upload a job description
* instantly receive a match‑score dashboard + downloadable written report

It orchestrates the **ResumeParser**, **ResumeScorer**, **ResumeVisualizer** and
**ReportGenerator** modules that you have already implemented.

Run with:
    streamlit run ui_app.py
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Dict, Optional

import streamlit as st

from resume_parser import ResumeParser  # local module
from scoring import ResumeScorer, MatchResult  # local module
from visualizer import ResumeVisualizer  # local module
from report_gen import ReportGenerator  # local module

# ----------------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------------

def _save_uploaded_file(uploaded) -> Path:
    """Persist the uploaded file to a temporary file and return the path."""
    suffix = Path(uploaded.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.read())
        return Path(tmp.name)


def _run_full_analysis(resume_path: Path, job_desc: str, candidate: str, job_title: str
                       ) -> tuple[Dict, MatchResult, Dict[str, str], Dict[str, str]]:
    """Pipeline that ties together parser → scorer → visualiser → reporter."""
    
    # Initialize variables to track progress
    parsed_resume = None
    match_result = None
    dashboard = None
    reports = None
    
    try:
        # 1 ▸ Parse
        st.write("🔄 Step 1/4: Parsing resume...")
        parser = ResumeParser()
        parsed_resume = parser.parse_resume(resume_path)
        st.write("✅ Resume parsing completed")
        
        # 2 ▸ Score
        st.write("🔄 Step 2/4: Calculating match score...")
        scorer = ResumeScorer()
        match_result = scorer.calculate_match_score(parsed_resume, job_desc)
        st.write("✅ Match scoring completed")
        
        # 3 ▸ Visualise
        st.write("🔄 Step 3/4: Creating visualizations...")
        viz = ResumeVisualizer()
        dashboard = viz.create_comprehensive_dashboard(match_result, candidate, job_title)
        st.write("✅ Visualization completed")
        
        # 4 ▸ Reports
        st.write("🔄 Step 4/4: Generating reports...")
        reporter = ReportGenerator()
        reports = reporter.generate_comprehensive_report(
            match_result, parsed_resume, job_desc, candidate, job_title
        )
        st.write("✅ Report generation completed")
        
    except Exception as e:
        error_msg = f"Error in analysis pipeline: {str(e)}"
        st.error(error_msg)
        
        # Determine which step failed based on what's None
        if parsed_resume is None:
            st.error("❌ **FAILED AT STEP 1**: ResumeParser.parse_resume()")
            reports = {"error": f"ResumeParser failed: {str(e)}"}
        elif match_result is None:
            st.error("❌ **FAILED AT STEP 2**: ResumeScorer.calculate_match_score()")
            reports = {"error": f"ResumeScorer failed: {str(e)}"}
        elif dashboard is None:
            st.error("❌ **FAILED AT STEP 3**: ResumeVisualizer.create_comprehensive_dashboard()")
            reports = {"error": f"ResumeVisualizer failed: {str(e)}"}
        else:
            st.error("❌ **FAILED AT STEP 4**: ReportGenerator.generate_comprehensive_report()")
            reports = {"error": f"ReportGenerator failed: {str(e)}"}
        
        # Provide default values for successful steps
        if parsed_resume is None:
            parsed_resume = {}
        if match_result is None:
            # Create a dummy MatchResult - you may need to adjust this based on your MatchResult structure
            from dataclasses import dataclass
            @dataclass
            class DummyMatchResult:
                overall_score: int = 0
            match_result = DummyMatchResult()
        if dashboard is None:
            dashboard = {}

    # cleanup tmp resume file early
    try:
        resume_path.unlink(missing_ok=True)
    except Exception:
        pass

    return parsed_resume, match_result, dashboard, reports


def _extract_executive_summary(full_report: str) -> str:
    """Extract executive summary from the full report."""
    lines = full_report.split('\n')
    summary_lines = []
    in_summary = False
    
    for line in lines:
        if 'EXECUTIVE SUMMARY' in line.upper():
            in_summary = True
            continue
        elif in_summary and line.strip() and line.startswith('='):
            break  # End of summary section
        elif in_summary and line.strip():
            summary_lines.append(line)
    
    return '\n'.join(summary_lines) if summary_lines else "Executive summary not found."


def _extract_status_from_report(full_report: str) -> str:
    """Extract overall assessment/status from the report."""
    if "OVERALL ASSESSMENT:" in full_report:
        try:
            status_section = full_report.split("OVERALL ASSESSMENT:")[1]
            status_line = status_section.split("\n")[0].strip()
            return status_line if status_line else "Assessment pending"
        except (IndexError, AttributeError):
            pass
    
    # Fallback: look for common status indicators
    if "STRONG MATCH" in full_report.upper():
        return "Strong Match"
    elif "GOOD MATCH" in full_report.upper():
        return "Good Match"
    elif "PARTIAL MATCH" in full_report.upper():
        return "Partial Match"
    elif "WEAK MATCH" in full_report.upper():
        return "Weak Match"
    else:
        return "Assessment Complete"


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
# Sidebar – inputs
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
        # Create an expandable section for debugging info
        debug_container = st.expander("🔍 Analysis Progress (click to expand)", expanded=True)
        
        with debug_container:
            try:
                parsed, result, dash, reports = _run_full_analysis(
                    tmp_resume_path, job_description, candidate_name, job_title
                )
            except Exception as e:
                st.error(f"Unexpected error in analysis pipeline: {str(e)}")
                st.error(f"Error type: {type(e).__name__}")
                import traceback
                st.error(f"Traceback: {traceback.format_exc()}")
                st.stop()

    # ============================== EXECUTIVE SUMMARY =============================
    
    # Check if there was an error in report generation
    if isinstance(reports, dict) and "error" in reports:
        st.error("Report Generation Failed!")
        st.subheader("Error Details")
        st.error(f"Error: {reports['error']}")
        
        # Still show the match score if available
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Overall match score", f"{result.overall_score}%")
        with col2:
            st.metric("Status", "Analysis Incomplete")
            
        st.warning("The analysis was partially completed, but report generation failed. Please check your ReportGenerator module.")
        st.stop()
    
    st.success("Analysis complete!")
    st.subheader("Executive summary")
    
    # Handle different report structures
    if isinstance(reports, dict):
        if "executive_summary" in reports:
            executive_summary = reports["executive_summary"]
        elif "full_report" in reports:
            executive_summary = _extract_executive_summary(reports["full_report"])
        else:
            # If reports is a dict but doesn't have expected keys, show available keys
            st.warning(f"Unexpected report structure. Available keys: {list(reports.keys())}")
            executive_summary = str(reports)
    else:
        # If reports is a string (the full report itself)
        executive_summary = _extract_executive_summary(str(reports))
    
    st.markdown(executive_summary)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Overall match score", f"{result.overall_score}%")
    with col2:
        # Extract status safely
        if isinstance(reports, dict) and "full_report" in reports:
            status = _extract_status_from_report(reports["full_report"])
        elif isinstance(reports, str):
            status = _extract_status_from_report(reports)
        else:
            status = "Analysis Complete"
        st.metric("Status", status)

    # ============================== DASHBOARD VISUALS =============================
    st.markdown("## Visual dashboard")
    
    # Safely display dashboard components
    if dash and isinstance(dash, dict):
        if "gauge" in dash:
            st.components.v1.html(dash["gauge"], height=420)
        else:
            st.info("Gauge chart not available")

        colA, colB = st.columns(2)
        with colA:
            if "radar" in dash:
                st.components.v1.html(dash["radar"], height=520)
            else:
                st.info("Radar chart not available")
        with colB:
            if "skills_matrix" in dash:
                st.components.v1.html(dash["skills_matrix"], height=420)
            else:
                st.info("Skills matrix not available")

        if "breakdown" in dash:
            st.components.v1.html(dash["breakdown"], height=420)
        else:
            st.info("Breakdown chart not available")

        if "experience" in dash and dash["experience"]:
            st.components.v1.html(dash["experience"], height=350)

        st.markdown("### Recommendations")
        if "recommendations" in dash:
            st.components.v1.html(dash["recommendations"], height=320)
        else:
            st.info("Recommendations not available")
    else:
        st.warning("Dashboard data not available or in unexpected format")

    # ============================== DOWNLOADS =====================================
    st.markdown("---")
    st.subheader("Download outputs")

    # Text report - handle different report structures
    report_text = ""
    if isinstance(reports, dict):
        if "full_report" in reports:
            report_text = reports["full_report"]
        else:
            # Combine all available report sections
            report_text = "\n\n".join([f"{k}:\n{v}" for k, v in reports.items()])
    else:
        report_text = str(reports)

    st.download_button(
        label="📄 Full text report (.txt)",
        data=report_text,
        file_name=f"{candidate_name.replace(' ', '_').lower()}_analysis_report.txt",
        mime="text/plain",
    )

    # Dashboard HTML - only if dashboard data is available
    if dash and isinstance(dash, dict):
        try:
            viz = ResumeVisualizer()
            dashboard_html = viz.export_dashboard_html(dash, candidate_name, job_title)
            st.download_button(
                label="📊 Interactive dashboard (.html)",
                data=dashboard_html,
                file_name=f"{candidate_name.replace(' ', '_').lower()}_dashboard.html",
                mime="text/html",
            )
        except Exception as e:
            st.warning(f"Could not generate dashboard HTML: {str(e)}")
    else:
        st.info("Dashboard HTML export not available due to missing dashboard data")

# ----------------------------------------------------------------------------------
# Footer & credits
# ----------------------------------------------------------------------------------
st.markdown(
    "---\nDeveloped with ❤️ by **ABHINAV RAM S V** using Streamlit • ResumeParser • ResumeScorer • ResumeVisualizer\nand ReportGenerator modules. | © 2025"
)