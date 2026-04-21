import streamlit as st
from analyzer import extract_text_from_pdf, analyze_skills
from skills_data import ROLE_SKILLS, ROLE_DESCRIPTIONS, WEIGHT_MULTIPLIERS

st.set_page_config(
    page_title="Resume Analyzer — Skill Gap Detector",
    page_icon="📄",
    layout="centered",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .hero-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        padding: 2.5rem 2rem;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.25);
    }
    .hero-banner h1 {
        color: white;
        font-size: 2rem;
        font-weight: 800;
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.5px;
    }
    .hero-banner p {
        color: rgba(255,255,255,0.85);
        font-size: 1.05rem;
        margin: 0;
        font-weight: 400;
    }

    .score-card {
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        margin: 1.5rem 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    }
    .score-card.high {
        background: linear-gradient(135deg, #00b09b, #96c93d);
    }
    .score-card.medium {
        background: linear-gradient(135deg, #f7971e, #ffd200);
    }
    .score-card.low {
        background: linear-gradient(135deg, #eb3349, #f45c43);
    }
    .score-card .score-value {
        font-size: 3.2rem;
        font-weight: 800;
        color: white;
        line-height: 1;
    }
    .score-card .score-label {
        font-size: 1rem;
        font-weight: 600;
        color: rgba(255,255,255,0.9);
        margin-top: 0.3rem;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .score-card .score-subtitle {
        font-size: 0.85rem;
        color: rgba(255,255,255,0.75);
        margin-top: 0.25rem;
    }

    .chip-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    .chip {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.35rem 0.85rem;
        border-radius: 99px;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.2px;
    }
    .chip-found {
        background: rgba(0, 176, 155, 0.12);
        color: #00906e;
        border: 1.5px solid rgba(0, 176, 155, 0.3);
    }
    .chip-missing {
        background: rgba(235, 51, 73, 0.10);
        color: #c0392b;
        border: 1.5px solid rgba(235, 51, 73, 0.25);
    }
    .chip-partial {
        background: rgba(243, 156, 18, 0.12);
        color: #d35400;
        border: 1.5px solid rgba(243, 156, 18, 0.3);
    }
    .chip .tier-badge {
        font-size: 0.65rem;
        padding: 0.1rem 0.35rem;
        border-radius: 4px;
        font-weight: 700;
        text-transform: uppercase;
    }
    .tier-core { background: #e74c3c22; color: #e74c3c; }
    .tier-important { background: #f39c1222; color: #e67e22; }
    .tier-nice { background: #3498db22; color: #3498db; }

    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1a1a2e;
        margin: 1.5rem 0 0.5rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    .suggestion-box {
        background: linear-gradient(135deg, #fdfcfb 0%, #e2d1c3 100%);
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        border-left: 4px solid #764ba2;
        margin-top: 0.5rem;
        font-size: 0.95rem;
        line-height: 1.7;
        color: #2c2c54;
    }

    .info-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        font-size: 0.92rem;
        color: #34495e;
    }

    .breakdown-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 0.75rem;
        margin: 0.5rem 0;
    }
    .breakdown-item {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 0.8rem;
        text-align: center;
    }
    .breakdown-item .tier-name {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.25rem;
    }
    .breakdown-item .tier-stat {
        font-size: 1.3rem;
        font-weight: 800;
    }

    .suggestions-intro {
        font-size: 0.95rem;
        font-weight: 600;
        color: #2c2c54;
        margin-bottom: 1rem;
    }
    .priority-section {
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.85rem;
    }
    .priority-section.fix-first {
        background: rgba(231, 76, 60, 0.05);
        border-left: 4px solid #e74c3c;
    }
    .priority-section.worth-adding {
        background: rgba(230, 126, 34, 0.05);
        border-left: 4px solid #e67e22;
    }
    .priority-section.nice-to-have {
        background: rgba(52, 152, 219, 0.05);
        border-left: 4px solid #3498db;
    }
    .priority-header {
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .priority-count {
        font-size: 0.72rem;
        font-weight: 500;
        color: #7f8c8d;
        text-transform: none;
        letter-spacing: 0;
        background: rgba(0,0,0,0.06);
        padding: 0.1rem 0.45rem;
        border-radius: 99px;
    }
    .priority-item {
        padding: 0.5rem 0;
        border-bottom: 1px solid rgba(0,0,0,0.06);
    }
    .priority-item:last-child {
        border-bottom: none;
        padding-bottom: 0;
    }
    .priority-skill-name {
        font-size: 0.9rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 0.2rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .partial-tag {
        font-size: 0.68rem;
        font-weight: 600;
        color: #d35400;
        background: rgba(211, 84, 0, 0.1);
        border: 1px solid rgba(211, 84, 0, 0.2);
        border-radius: 4px;
        padding: 0.05rem 0.35rem;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    .priority-suggestion {
        font-size: 0.84rem;
        color: #555e6e;
        line-height: 1.55;
    }
    .suggestions-tip {
        font-size: 0.83rem;
        color: #7f8c8d;
        margin-top: 0.85rem;
        padding-top: 0.75rem;
        border-top: 1px solid rgba(0,0,0,0.08);
        line-height: 1.5;
    }

    .disclaimer {
        background: #f0f0f5;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        font-size: 0.78rem;
        color: #7f8c8d;
        line-height: 1.5;
        margin-top: 1.5rem;
        border: 1px solid #e0e0e8;
    }

    .footer {
        text-align: center;
        margin-top: 3rem;
        padding: 1rem;
        color: #95a5a6;
        font-size: 0.8rem;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown(
    """
    <div class="hero-banner">
        <h1>📄 Resume Analyzer</h1>
        <p>Upload your resume &bull; Pick a role &bull; Get instant skill-gap feedback</p>
    </div>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.markdown("### ⚙️ Settings")

    role = st.selectbox(
        "🎯 Target Role",
        list(ROLE_SKILLS.keys()),
        help="Select the role you're applying for.",
    )
    st.markdown(
        f'<div class="info-card">💡 <b>{role}</b>: {ROLE_DESCRIPTIONS[role]}</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    st.markdown("### 📋 Required Skills")
    skills_list = ROLE_SKILLS[role]

    for tier, emoji in [("core", "🔴"), ("important", "🟡"), ("nice", "🔵")]:
        tier_skills = [s for s in skills_list if s.get("tier", "nice") == tier]
        if tier_skills:
            st.caption(f"{emoji} {tier.upper()} ({WEIGHT_MULTIPLIERS[tier]}× weight)")
            for s in tier_skills:
                st.markdown(f"&nbsp;&nbsp;• {s['name']}")

    st.divider()
    st.markdown(
        '<div class="footer">Built with ❤️ using Streamlit</div>',
        unsafe_allow_html=True,
    )


uploaded_file = st.file_uploader(
    "📎 Upload your resume (PDF)",
    type=["pdf"],
    help="Only text-based PDF files are supported. Scanned/image PDFs won't work.",
)

if uploaded_file:
    st.success(f"✅ **{uploaded_file.name}** uploaded successfully!")

analyze_clicked = st.button(
    "🔍 Analyze Resume",
    use_container_width=True,
    type="primary",
    disabled=not uploaded_file,
)

if analyze_clicked and uploaded_file:
    with st.spinner("Extracting text and analyzing skills…"):
        try:
            resume_text = extract_text_from_pdf(uploaded_file)
        except Exception as e:
            st.error(f"❌ Failed to extract text: {e}")
            import traceback
            st.code(traceback.format_exc())
            st.stop()

        if not resume_text:
            uploaded_file.seek(0)
            raw = uploaded_file.read(200)
            st.warning("⚠️ No text could be extracted. This might be a scanned/image PDF.")
            st.info("💡 **Tip:** Export your resume from Word, Google Docs, or similar tools as PDF — those create text-based PDFs that work perfectly.")
            st.caption(f"File size: {uploaded_file.size} bytes")
            st.stop()

        result = analyze_skills(resume_text, role)

    st.divider()

    st.markdown(
        '<div class="section-header">📝 Resume Preview</div>',
        unsafe_allow_html=True,
    )
    preview_lines = resume_text[:800]
    if len(resume_text) > 800:
        preview_lines += "…"
    with st.expander("Show extracted text", expanded=False):
        st.text(preview_lines)

    label_lower = result["label"].lower()

    st.markdown(
        f"""
        <div class="score-card {label_lower}">
            <div class="score-value">{result['score']}%</div>
            <div class="score-label">{result['label']} Match</div>
            <div class="score-subtitle">{result['found_count']} full · {result['partial_count']} partial · {result['total_skills']} total skills</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.progress(min(1.0, result["score"] / 100))

    st.markdown(
        '<div class="section-header">📊 Score Breakdown by Priority</div>',
        unsafe_allow_html=True,
    )
    breakdown = result["breakdown"]
    tier_colors = {"core": "#e74c3c", "important": "#e67e22", "nice": "#3498db"}

    bc1, bc2, bc3 = st.columns(3)
    for col, (tier, label) in zip([bc1, bc2, bc3], [("core", "Core"), ("important", "Important"), ("nice", "Nice-to-Have")]):
        f_count = breakdown[tier]["found"]
        p_count = breakdown[tier].get("partial", 0)
        t_count = breakdown[tier]["total"]
        partial_html = f'<div style="font-size:0.75rem;color:#f39c12;margin-top:0.25rem;">+{p_count} partial (50%)</div>' if p_count > 0 else ''
        with col:
            st.markdown(
                f'<div style="background:#f8f9fa;border-radius:10px;padding:0.8rem;text-align:center;">'
                f'<div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:{tier_colors[tier]};margin-bottom:0.25rem;">{label} ({WEIGHT_MULTIPLIERS[tier]}×)</div>'
                f'<div style="font-size:1.3rem;font-weight:800;color:{tier_colors[tier]};">{f_count}/{t_count}</div>'
                f'{partial_html}'
                f'</div>',
                unsafe_allow_html=True,
            )

    def _render_chips(skills_list, css_class):
        if not skills_list:
            return ""
        html = '<div class="chip-container">'
        for s in skills_list:
            tier = s.get("tier", "nice")
            html += f'<span class="chip {css_class}"><span class="tier-badge tier-{tier}">{tier[0].upper()}</span>{s["name"]}</span>'
        html += "</div>"
        return html

    has_partials = bool(result.get("partial"))
    if has_partials:
        cols = st.columns(3)
        c_found, c_partial, c_missing = cols[0], cols[1], cols[2]
    else:
        cols = st.columns(2)
        c_found, c_partial, c_missing = cols[0], None, cols[1]

    with c_found:
        st.markdown('<div class="section-header">✅ Found</div>', unsafe_allow_html=True)
        if result["found"]:
            st.markdown(_render_chips(result["found"], "chip-found"), unsafe_allow_html=True)
        else:
            st.caption("No matching skills detected.")

    if c_partial:
        with c_partial:
            st.markdown('<div class="section-header">⚠️ Partial</div>', unsafe_allow_html=True)
            if result["partial"]:
                st.markdown(_render_chips(result["partial"], "chip-partial"), unsafe_allow_html=True)
            else:
                st.caption("None.")

    with c_missing:
        st.markdown('<div class="section-header">❌ Missing</div>', unsafe_allow_html=True)
        if result["missing"]:
            st.markdown(_render_chips(result["missing"], "chip-missing"), unsafe_allow_html=True)
        else:
            if not has_partials:
                st.balloons()
            st.caption("🎉 None!")

    st.markdown(
        '<div class="section-header">💡 Actionable Suggestions</div>',
        unsafe_allow_html=True,
    )

    partial_ids  = {id(s) for s in result.get("partial", [])}
    worth_adding = [s for s in result["missing"] if s.get("tier") == "important"] + [s for s in result.get("partial", []) if s.get("tier") == "important"]
    nice_to_have = [s for s in result["missing"] if s.get("tier") == "nice"]

    if worth_adding or nice_to_have:

        def _render_priority_section(title, css_class, items, partial_ids=set()):
            count = len(items)
            noun  = "skill" if count == 1 else "skills"
            html  = f'<div class="priority-section {css_class}">'
            html += (
                f'<div class="priority-header">'
                f'{title}'
                f'<span class="priority-count">{count} {noun}</span>'
                f'</div>'
            )
            for s in items:
                partial_tag = (
                    '<span class="partial-tag">mentioned once</span>'
                    if id(s) in partial_ids else ""
                )
                html += (
                    f'<div class="priority-item">'
                    f'<div class="priority-skill-name">{s["name"]}{partial_tag}</div>'
                    f'<div class="priority-suggestion">{s["suggestion"]}</div>'
                    f'</div>'
                )
            html += '</div>'
            return html

        sections_html = ""
        if worth_adding:
            sections_html += _render_priority_section(
                "🟡 Worth Adding", "worth-adding", worth_adding, partial_ids
            )
        if nice_to_have:
            sections_html += _render_priority_section(
                "🔵 Nice to Have", "nice-to-have", nice_to_have
            )

        tip_map = {
            "Low":    "📌 <i>Focus on the <b>Worth Adding</b> skills first — they have the most impact on your score.</i>",
            "Medium": "📌 <i>Good foundation. Closing the <b>Worth Adding</b> gaps will push you above 75%.</i>",
            "High":   "📌 <i>Strong match. The remaining items are lower priority and can help you stand out.</i>",
        }

        intro = f'<div class="suggestions-intro">How to strengthen your resume for <b>{role}</b>:</div>'
        tip   = f'<div class="suggestions-tip">{tip_map[result["label"]]}</div>'

        st.markdown(
            f'<div class="suggestion-box">{intro}{sections_html}{tip}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="suggestion-box">🏆 Your resume covers all the required skills for this role. Well done!</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="disclaimer">
            ⚠️ <b>Disclaimer:</b> This tool uses heuristic keyword matching — not AI or recruiter evaluation.
            It scans for specific terms in your resume text and may miss context, synonyms, or implied skills.
            Use the results as a <b>starting point</b> to improve your resume, not as a definitive assessment.
            A real recruiter evaluates experience depth, project impact, communication, and culture fit — none of which can be captured by keyword matching alone.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown(
        '<div class="footer">Resume Analyzer v1.0 — No data is stored or shared.</div>',
        unsafe_allow_html=True,
    )

elif not uploaded_file:
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 📤 Upload")
        st.caption("Drop your PDF resume above")
    with col2:
        st.markdown("#### 🎯 Select Role")
        st.caption("Pick from the sidebar")
    with col3:
        st.markdown("#### 📊 Get Results")
        st.caption("Instant skill-gap analysis")

    st.markdown(
        """
        <div class="disclaimer">
            ⚠️ <b>Disclaimer:</b> This tool uses heuristic keyword matching — not AI or recruiter evaluation.
            Results are a starting point to identify skill gaps, not a substitute for professional resume review.
        </div>
        """,
        unsafe_allow_html=True,
    )
