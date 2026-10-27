from .ai_client import call_nvidia_ai
from .resume_parser import extract_text_from_resume, KNOWN_SKILLS


def _fallback_analysis(text: str, skills_found: list) -> dict:
    text_lower = text.lower()
    words = text.split()
    word_count = len(words)

    # Quality Score Calculation (0 - 100)
    length_score = min(30, word_count // 15)                       # up to 30 pts for depth
    skill_score = min(40, len(skills_found) * 4)                    # up to 40 pts for breadth of skills
    structure_score = 15 if any(k in text_lower for k in ["project", "experience", "education"]) else 5
    formatting_score = 15 if any(k in text_lower for k in ["email", "phone", "contact", "summary", "objective"]) else 5
    quality_score = min(100, length_score + skill_score + structure_score + formatting_score)

    # ATS Score Calculation (0 - 100)
    ats_sections = sum(1 for section in ["education", "experience", "work", "projects", "skills", "certifications"] if section in text_lower)
    ats_section_score = min(40, ats_sections * 8)
    ats_keyword_score = min(40, len(skills_found) * 5)
    ats_format_score = 20 if word_count >= 150 else 10
    ats_score = min(100, ats_section_score + ats_keyword_score + ats_format_score)

    # Comprehensive Key Points (4 - 6 points)
    key_points = []
    if skills_found:
        key_points.append(f"Detected {len(skills_found)} technical skills ({', '.join(skills_found[:6])}).")
    else:
        key_points.append("Low technical keyword density; adding specific languages and frameworks is recommended.")

    if ats_sections >= 3:
        key_points.append(f"Standard ATS section headers present ({ats_sections} core sections identified).")
    else:
        key_points.append("Non-standard section headers detected; using standard titles improves ATS parsing.")

    if word_count >= 150:
        key_points.append(f"Good document length (~{word_count} words) with appropriate detail depth.")
    else:
        key_points.append(f"Resume text is brief (~{word_count} words); expanding work and project details is recommended.")

    if any(k in text_lower for k in ["built", "developed", "managed", "created", "lead", "designed", "achieved", "increased"]):
        key_points.append("Action-oriented verbs and active phrasing detected in project descriptions.")
    else:
        key_points.append("Incorporate strong action verbs (e.g., Developed, Optimized, Managed) to highlight impact.")

    if any(c.isdigit() for c in text):
        key_points.append("Quantifiable figures and performance metrics identified in content.")

    # Comprehensive Strengths (4 - 5 points)
    strengths = []
    if skills_found:
        strengths.append(f"Strong technical keyword breadth: {', '.join(skills_found[:8])}.")
    if "experience" in text_lower or "work" in text_lower:
        strengths.append("Clear work experience section outlining roles and responsibilities.")
    if "project" in text_lower:
        strengths.append("Dedicated project showcase demonstrating practical tool application.")
    if "education" in text_lower:
        strengths.append("Structured academic background and qualifications.")
    if any(k in text_lower for k in ["summary", "objective"]):
        strengths.append("Professional summary section included to state career objectives.")
    if not strengths:
        strengths.append("Resume text extracted successfully and structured for ATS readability.")

    # Comprehensive Improvements (4 - 5 points)
    improvements = []
    if quality_score < 75 or not any(c.isdigit() for c in text):
        improvements.append("Include measurable business impact (e.g., 'Reduced load time by 30%' or 'Managed 5+ projects').")
    if ats_score < 75 or ats_sections < 4:
        improvements.append("Use standard ATS section headings: 'Technical Skills', 'Work Experience', 'Education', 'Projects'.")
    if len(skills_found) < 6:
        improvements.append("Add additional relevant tools, frameworks, and domain-specific technical keywords.")
    if "summary" not in text_lower and "objective" not in text_lower:
        improvements.append("Add a 2-3 sentence Professional Summary at the top highlighting key strengths.")
    if not any(k in text_lower for k in ["certif", "award", "achievement"]):
        improvements.append("Add a Certifications or Accomplishments section to increase recruiter & ATS matching.")
    if not improvements:
        improvements.append("Resume is well-structured; keep updating with recent achievements and new skills.")

    return {
        "quality_score": round(quality_score, 1),
        "ats_score": round(ats_score, 1),
        "key_points": key_points,
        "strengths": strengths,
        "improvements": improvements,
    }


def analyze_resume(file_path: str) -> dict:
    """Data Analyze Engine + basis for Progress Tracker. Returns quality_score, ats_score,
    key_points, strengths, improvements. AI-first (feature='resume_analyzer') with rule-based fallback."""
    text = extract_text_from_resume(file_path)
    skills_found = sorted({s for s in KNOWN_SKILLS if s in text.lower()})

    system_prompt = (
        "You are an expert resume analyzer and ATS scoring engine. Given a candidate's resume text, "
        "evaluate both Resume Quality Score (0-100) and ATS Resume Score (0-100). "
        "Provide 4-6 detailed key_points, 4-5 strengths, and 4-5 actionable improvements. "
        "Respond ONLY with valid JSON: "
        '{"quality_score": number (0-100), "ats_score": number (0-100), '
        '"key_points": [string,...], "strengths": [string,...], "improvements": [string,...]}'
    )
    ai_result = call_nvidia_ai("resume_analyzer", system_prompt, text[:6000], json_mode=True)
    if ai_result and "quality_score" in ai_result:
        if "ats_score" not in ai_result:
            ai_result["ats_score"] = min(100.0, float(ai_result["quality_score"]) + 5.0)
        return ai_result
    return _fallback_analysis(text, skills_found)
