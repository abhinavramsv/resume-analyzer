from __future__ import annotations

import os
import tempfile
import traceback
from pathlib import Path
from typing import Dict, Optional

import streamlit as st

from resume_parser import ResumeParser
from scoring import ResumeScorer, MatchResult
from visualizer import ResumeVisualizer
from report_gen import ReportGenerator

def _save_uploaded_file(uploaded) -> Path:
    suffix = Path(uploaded.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.read())
        return Path(tmp.name)

def _run_full_analysis(resume_path: Path, job_desc: str, candidate: str, job_title: str
                       ) -> tuple[Dict, MatchResult, Dict[str, str], Dict[str, str]]:
    
    parsed_resume = None
    match_result = None
    dashboard = None
    reports = None
    
    try:
        st.write("🔄 Step 1/4: Parsing resume...")
        parser = ResumeParser()
        parsed_resume = parser.parse_resume(resume_path)
        
        st.write("🔄 Step 2/4: Calculating match score...")
        scorer = ResumeScorer()
        match_result = scorer.calculate_match_score(parsed_resume, job_desc)
        
        st.write("🔄 Step 3/4: Creating visualizations...")
        viz = ResumeVisualizer()
        dashboard = viz.create_comprehensive_dashboard(match_result, candidate, job_title)
        
        st.write("🔄 Step 4/4: Generating reports...")
        reporter = ReportGenerator()
        reports = reporter.generate_comprehensive_report(
            match_result, parsed_resume, job_desc, candidate, job_title
        )
        
    except Exception as e:
        st.error(f"Error in analysis pipeline: {str(e)}")
        reports = {"error": traceback.format_exc()}
        if parsed_resume is None: parsed_resume = {}
        if match_result is None:
            from dataclasses import dataclass
            @dataclass
            class DummyResult:
                overall_score: int = 0
            match_result = DummyResult()
        if dashboard is None: dashboard = {}

    try:
        resume_path.unlink(missing_ok=True)
    except:
        pass

    return parsed_resume, match_result, dashboard, reports

def _extract_executive_summary(full_report: str) -> str:
    lines = full_report.split('\n')
    summary_lines = []
    in_summary = False
    for line in lines:
        if 'EXECUTIVE SUMMARY' in line.upper():
            in_summary = True
            continue
        elif in_summary and line.strip() and line.startswith('='):
            break
        elif in_summary and line.strip():
            summary_lines.append(line)
    return '\n'.join(summary_lines) if summary_lines else "Summary not found."

st.set_page_config(page_title="AI Resume Match Analyzer", layout="wide")

st.title("⚡ AI Resume Match Analyzer")
st.write("Upload a resume and job description to get instant matching insights and reports.")

with st.sidebar:
    st.header("🗂️ Inputs")
    resume_file = st.file_uploader("Resume file", type=["pdf", "docx", "txt"])
    jd_input_mode = st.radio("JD input method", ["Paste text", "Upload TXT"])
    
    job_description = None
    if jd_input_mode == "Paste text":
        job_description = st.text_area("Paste JD here", height=300)
    else:
        jd_file = st.file_uploader("Upload JD (.txt)", type=["txt"])
        if jd_file: job_description = jd_file.getvalue().decode("utf-8")

    st.markdown("---")
    candidate_name = st.text_input("Candidate name", value="Candidate")
    job_title = st.text_input("Job title", value="Position")
    analyse_btn = st.button("🚀 Analyse Resume", type="primary")

if analyse_btn:
    if resume_file is None or not job_description:
        st.warning("Please provide both a resume and a job description.")
        st.stop()

    tmp_resume_path = _save_uploaded_file(resume_file)

    with st.spinner("Processing..."):
        debug_container = st.expander("🔍 Analysis Progress", expanded=True)
        with debug_container:
            parsed, result, dash, reports = _run_full_analysis(
                tmp_resume_path, job_description, candidate_name, job_title
            )

    if isinstance(reports, dict) and "error" in reports:
        st.error(f"Analysis Failed: {reports['error']}")
        st.stop()

    st.success("Analysis complete!")
    
    st.subheader("Executive summary")
    summary = reports.get("executive_summary") if isinstance(reports, dict) else _extract_executive_summary(str(reports))
    st.markdown(summary)

    col1, col2 = st.columns(2)
    col1.metric("Overall match score", f"{result.overall_score}%")
    
    status = "Analysis Complete"
    if "OVERALL ASSESSMENT:" in str(reports):
        status = str(reports).split("OVERALL ASSESSMENT:")[1].split("\n")[0].strip()
    col2.metric("Status", status)

    st.markdown("## Visual dashboard")
    st.components.v1.html(dash.get("gauge", ""), height=420)

    colA, colB = st.columns(2)
    with colA: st.components.v1.html(dash.get("radar", ""), height=520)
    with colB: st.components.v1.html(dash.get("skills_matrix", ""), height=420)

    st.components.v1.html(dash.get("breakdown", ""), height=420)
    st.components.v1.html(dash.get("recommendations", ""), height=320)

    st.markdown("---")
    st.subheader("Download outputs")
    
    report_out = reports.get("full_report", str(reports)) if isinstance(reports, dict) else str(reports)
    st.download_button("📄 Download Text Report", report_out, f"{candidate_name.lower()}_report.txt")

    viz = ResumeVisualizer()
    dash_html = viz.export_dashboard_html(dash, candidate_name, job_title)
    st.download_button("📊 Download Interactive Dashboard", dash_html, f"{candidate_name.lower()}_dashboard.html", "text/html")

st.markdown("---\nDeveloped by **ABHINAV RAM S V**")
