import io
import re
from skills_data import ROLE_SKILLS, WEIGHT_MULTIPLIERS


def extract_text_from_pdf(uploaded_file) -> str:
    import pdfplumber

    uploaded_file.seek(0)
    file_bytes = uploaded_file.read()

    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return text.strip()


def _count_keyword_hits(text: str, keywords: list[str]) -> int:
    total = 0
    for keyword in keywords:
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(keyword) + r"(?![a-zA-Z0-9])"
        total += len(re.findall(pattern, text, re.IGNORECASE))
    return min(2, total)


def analyze_skills(resume_text: str, role: str) -> dict:
    skills = ROLE_SKILLS.get(role, [])

    found = []
    partial = []
    missing = []

    breakdown = {
        "core":      {"found": 0, "partial": 0, "total": 0},
        "important": {"found": 0, "partial": 0, "total": 0},
        "nice":      {"found": 0, "partial": 0, "total": 0},
    }

    total_weight = 0
    earned_weight = 0

    for skill in skills:
        name       = skill["name"]
        tier       = skill.get("tier", "nice")
        suggestion = skill.get("suggestion", f"Consider learning {name}.")
        weight     = WEIGHT_MULTIPLIERS.get(tier, 1)

        total_weight          += weight
        breakdown[tier]["total"] += 1

        hits = _count_keyword_hits(resume_text, skill["keywords"])

        entry = {"name": name, "tier": tier, "suggestion": suggestion}

        if hits >= 2:
            entry["match"] = "full"
            found.append(entry)
            earned_weight            += weight
            breakdown[tier]["found"] += 1
        elif hits == 1:
            entry["match"] = "partial"
            partial.append(entry)
            earned_weight              += weight * 0.5
            breakdown[tier]["partial"] += 1
        else:
            entry["match"] = "missing"
            missing.append(entry)

    score = round((earned_weight / total_weight) * 100) if total_weight > 0 else 0
    score = min(100, score)

    if score >= 75:
        label = "High"
    elif score >= 50:
        label = "Medium"
    else:
        label = "Low"

    return {
        "found":         found,
        "partial":       partial,
        "missing":       missing,
        "score":         score,
        "label":         label,
        "total_weight":  total_weight,
        "earned_weight": earned_weight,
        "total_skills":  len(skills),
        "found_count":   len(found),
        "partial_count": len(partial),
        "breakdown":     breakdown,
    }
