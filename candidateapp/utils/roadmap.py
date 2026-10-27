from .ai_client import call_nvidia_ai
from .career_data import CAREER_SKILL_MAP, DETAILED_CAREER_ROADMAPS, STAGE_ORDER


def _fallback_career_recommendation(candidate_skills: set) -> list:
    """Match % = overlap between candidate skills and each career's required skill set."""
    results = []
    for career, required in CAREER_SKILL_MAP.items():
        required_set = set(required)
        overlap = len(candidate_skills & required_set)
        match_pct = round((overlap / len(required_set)) * 100, 1) if required_set else 0
        # baseline so a brand-new profile still gets a reasonable spread instead of all-zero
        match_pct = max(match_pct, 15.0)
        results.append({"career_name": career, "match_percent": match_pct})
    results.sort(key=lambda r: r["match_percent"], reverse=True)
    return results[:5]


def recommend_careers(candidate) -> list:
    """Returns top-5 [{career_name, match_percent}], AI-first with fallback."""
    candidate_skills = {s.lower() for s in candidate.skill_names}
    system_prompt = (
        "You are a career recommendation engine. Given a candidate's degree, role interest, "
        "CGPA and skills, respond ONLY with valid JSON: "
        '{"recommendations": [{"career_name": string, "match_percent": number}, ... up to 5]}'
    )
    user_prompt = (
        f"Degree: {candidate.degree}\nDesired role: {candidate.role}\nCGPA: {candidate.cgpa}\n"
        f"Skills: {', '.join(candidate.skill_names)}"
    )
    ai_result = call_nvidia_ai("career_roadmap", system_prompt, user_prompt, json_mode=True)
    if ai_result and "recommendations" in ai_result:
        return ai_result["recommendations"][:5]
    return _fallback_career_recommendation(candidate_skills)


def generate_skill_roadmap(candidate, target_career: str) -> list:
    """Returns ordered list [{skill_name, stage, sequence_no}] from beginner to job-ready."""
    system_prompt = (
        "You are an expert skill roadmap generator. Build a comprehensive, 7-10 step roadmap "
        f"for the role '{target_career}'. Cover foundational skills (beginner), core frameworks (intermediate), "
        "advanced topics, capstone projects, and production job readiness. "
        "Respond ONLY with valid JSON: "
        '{"steps": [{"skill_name": string, "stage": "beginner"|"intermediate"|"advanced"|"project"|"job_ready", '
        '"sequence_no": number}, ...]}'
    )
    user_prompt = (
        f"Target career: {target_career}\n"
        f"Candidate current skills: {', '.join(candidate.skill_names)}\n"
        "Generate a complete step-by-step career path from fundamentals to advanced frameworks and job readiness."
    )
    ai_result = call_nvidia_ai("career_roadmap", system_prompt, user_prompt, json_mode=True)
    if ai_result and "steps" in ai_result and isinstance(ai_result["steps"], list) and len(ai_result["steps"]) >= 4:
        return ai_result["steps"]

    # Use rich pre-defined detailed roadmap
    roadmap_def = DETAILED_CAREER_ROADMAPS.get(target_career)
    if not roadmap_def:
        roadmap_def = [
            {"skill_name": f"{target_career} Core Fundamentals", "stage": "beginner"},
            {"skill_name": "Git & Version Control", "stage": "beginner"},
            {"skill_name": "Relational Databases & SQL", "stage": "intermediate"},
            {"skill_name": f"{target_career} Primary Frameworks", "stage": "intermediate"},
            {"skill_name": "Advanced Architecture & APIs", "stage": "advanced"},
            {"skill_name": "System Security & Best Practices", "stage": "advanced"},
            {"skill_name": f"Capstone {target_career} Project", "stage": "project"},
            {"skill_name": "Production Deployment & Job Readiness", "stage": "job_ready"},
        ]

    steps = []
    for seq, item in enumerate(roadmap_def, start=1):
        steps.append({
            "skill_name": item["skill_name"],
            "stage": item["stage"],
            "sequence_no": seq,
        })
    return steps
