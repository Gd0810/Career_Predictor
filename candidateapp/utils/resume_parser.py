import re
import pdfplumber

from .ai_client import call_nvidia_ai

KNOWN_SKILLS = [
    # Programming Languages
    "python", "java", "c++", "c#", "javascript", "typescript", "php", "ruby", "go", "swift", "kotlin", "r",
    # Web & Frameworks
    "html", "html5", "css", "css3", "bootstrap", "tailwind", "react", "react.js", "react native",
    "angular", "vue", "node.js", "express", "django", "flask", "fastapi", "spring boot", ".net",
    # Databases & SQL
    "sql", "mysql", "postgresql", "mongodb", "sqlite", "oracle", "redis", "firebase",
    # Data Science & Machine Learning
    "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "opencv", "nlp", "statistics", "data visualization", "seaborn", "matplotlib",
    # Analytics & BI
    "power bi", "excel", "tableau", "dax", "business analysis", "etl", "spark", "hadoop", "airflow",
    # Cloud, DevOps & Tools
    "aws", "azure", "gcp", "docker", "kubernetes", "git", "github", "gitlab", "linux", "bash", "ci/cd",
    # Core Concepts & Other
    "rest api", "graphql", "json", "data structures", "algorithms", "dsa", "oop", "agile", "scrum",
]

ROLE_KEYWORDS_MAP = {
    "python developer": "python_developer",
    "python engineer": "python_developer",
    "django developer": "python_developer",
    "flask developer": "python_developer",
    "full stack developer": "web_developer",
    "fullstack developer": "web_developer",
    "full stack engineer": "web_developer",
    "web developer": "web_developer",
    "frontend developer": "web_developer",
    "frontend engineer": "web_developer",
    "backend developer": "web_developer",
    "backend engineer": "web_developer",
    "react developer": "web_developer",
    "node developer": "web_developer",
    "data analyst": "data_analyst",
    "business intelligence analyst": "data_analyst",
    "data scientist": "data_scientist",
    "machine learning engineer": "machine_learning_engineer",
    "ml engineer": "machine_learning_engineer",
    "ai engineer": "machine_learning_engineer",
    "business analyst": "business_analyst",
    "bi developer": "bi_developer",
    "power bi developer": "bi_developer",
    "software engineer": "software_engineer",
    "software developer": "software_engineer",
    "sde": "software_engineer",
    "devops engineer": "devops_engineer",
    "cloud engineer": "devops_engineer",
    "data engineer": "data_engineer",
    "java developer": "software_engineer",
}


def extract_text_from_resume(file_path: str) -> str:
    text_parts = []
    try:
        if file_path.lower().endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    text_parts.append(page_text)
        elif file_path.lower().endswith(".docx"):
            try:
                import docx
                doc = docx.Document(file_path)
                text_parts.append("\n".join([p.text for p in doc.paragraphs if p.text]))
            except Exception:
                with open(file_path, "r", errors="ignore") as f:
                    text_parts.append(f.read())
        else:
            with open(file_path, "r", errors="ignore") as f:
                text_parts.append(f.read())
    except Exception:
        return ""
    return "\n".join(text_parts)


def _extract_degree(text: str) -> str:
    degree_patterns = [
        r"(bachelor\s+of\s+(?:technology|engineering|science|computer\s+applications|business\s+administration)[^\n,]*)",
        r"(master\s+of\s+(?:technology|engineering|science|computer\s+applications|business\s+administration)[^\n,]*)",
        r"\b(b\.?\s*tech(?:nology)?\b[^\n,]*)",
        r"\b(m\.?\s*tech(?:nology)?\b[^\n,]*)",
        r"\b(b\.?\s*e\b[^\n,]*)",
        r"\b(m\.?\s*e\b[^\n,]*)",
        r"\b(bca\b[^\n,]*)",
        r"\b(mca\b[^\n,]*)",
        r"\b(b\.?\s*sc\b[^\n,]*)",
        r"\b(m\.?\s*sc\b[^\n,]*)",
        r"\b(diploma\s+in\s+[^\n,]*)",
    ]
    for pattern in degree_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            deg = match.group(1).strip()
            deg = re.sub(r"\s+", " ", deg)
            if len(deg) > 85:
                deg = deg[:85]
            return deg.title()
    return ""


def _extract_cgpa(text: str) -> float | None:
    patterns = [
        r"(?:cgpa|gpa|sgpa)\s*[:\-]?\s*(\d(?:\.\d{1,2})?)\s*(?:\/\s*(?:10|4))?",
        r"(\d(?:\.\d{1,2})?)\s*(?:\/\s*10)?\s*(?:cgpa|gpa|sgpa)",
        r"(?:aggregate|percentage|marks)\s*[:\-]?\s*(\d{2}(?:\.\d{1,2})?)\s*%",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = float(match.group(1))
            if val > 10.0:
                val = round(val / 10.0, 2)
            if 0.0 <= val <= 10.0:
                return val
    return None


def _extract_role(text: str) -> str:
    text_lower = text.lower()
    for phrase, role_code in ROLE_KEYWORDS_MAP.items():
        if phrase in text_lower:
            return role_code
    return "software_engineer"


def _extract_experience(text: str) -> tuple:
    text_lower = text.lower()

    if any(k in text_lower for k in ["fresher", "student", "graduate 202", "pursuing"]):
        if not re.search(r"\d+\s*\+?\s*years?\s+(?:of\s+)?experience", text_lower):
            return "fresher", 0.0

    exp_match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s*(?:of\s*)?(?:work\s*)?experience", text_lower)
    if exp_match:
        yrs = float(exp_match.group(1))
        exp_type = "experienced" if yrs >= 1.0 else "fresher"
        return exp_type, yrs

    year_matches = re.findall(r"\b(20[0-2][0-9])\b", text)
    if len(year_matches) >= 2:
        start_yr = int(year_matches[0])
        end_yr = int(year_matches[-1])
        diff = max(0, end_yr - start_yr)
        if 1 <= diff <= 15:
            return "experienced", float(diff)

    return "fresher", 0.0


def _extract_projects(text: str) -> list:
    projects = []
    lines = text.splitlines()
    in_project_section = False
    current_title = ""
    current_desc = []

    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
        line_lower = line_str.lower()

        if any(h in line_lower for h in ["project", "projects", "key projects", "academic projects"]):
            in_project_section = True
            continue

        if in_project_section:
            if any(h in line_lower for h in ["experience", "education", "skills", "certifications", "achievements"]):
                if current_title:
                    projects.append({"title": current_title, "description": " ".join(current_desc[:3])})
                break

            if len(line_str) < 65 and not line_str.startswith("-") and not line_str.startswith("•"):
                if current_title:
                    projects.append({"title": current_title, "description": " ".join(current_desc[:3])})
                    current_desc = []
                current_title = line_str
            else:
                if current_title:
                    current_desc.append(line_str.lstrip("-•* "))

    if current_title and not any(p["title"] == current_title for p in projects):
        projects.append({"title": current_title, "description": " ".join(current_desc[:3])})

    return projects[:4]


def _fallback_extract(text: str) -> dict:
    """High-accuracy rule-based extraction engine."""
    text_lower = text.lower()

    skills_found = sorted({s for s in KNOWN_SKILLS if s in text_lower})
    degree = _extract_degree(text)
    cgpa = _extract_cgpa(text)
    role = _extract_role(text)
    exp_type, exp_years = _extract_experience(text)
    projects = _extract_projects(text)

    return {
        "degree": degree,
        "role": role,
        "cgpa": cgpa,
        "experience_type": exp_type,
        "experience_years": exp_years,
        "skills": skills_found,
        "projects": projects,
    }


def parse_resume(file_path: str) -> dict:
    text = extract_text_from_resume(file_path)
    if not text.strip():
        return {
            "degree": "", "role": "", "cgpa": None, "experience_type": "fresher",
            "experience_years": None, "skills": [], "projects": []
        }

    system_prompt = (
        "You are an expert resume parsing AI assistant. Extract structured candidate personal, "
        "academic, and professional details from the resume text with high accuracy. "
        "Extract exact degree (e.g. B.Tech Computer Science), target role (e.g. python_developer, web_developer, data_analyst), "
        "numerical CGPA (0.0 to 10.0), experience_type ('fresher' or 'experienced'), experience_years (number or null), "
        "all technical skills, and all projects with titles and descriptions. "
        "Respond ONLY with valid JSON in this exact shape: "
        '{"degree": string, "role": string, "cgpa": number|null, '
        '"experience_type": "fresher"|"experienced", "experience_years": number|null, '
        '"skills": [string, ...], "projects": [{"title": string, "description": string}, ...]}'
    )
    ai_result = call_nvidia_ai("resume_parser", system_prompt, text[:8000], json_mode=True)
    if ai_result and isinstance(ai_result, dict):
        fallback = _fallback_extract(text)
        return {
            "degree": ai_result.get("degree") or fallback["degree"],
            "role": ai_result.get("role") or fallback["role"],
            "cgpa": ai_result.get("cgpa") if ai_result.get("cgpa") is not None else fallback["cgpa"],
            "experience_type": ai_result.get("experience_type") or fallback["experience_type"],
            "experience_years": ai_result.get("experience_years") if ai_result.get("experience_years") is not None else fallback["experience_years"],
            "skills": list(set(ai_result.get("skills", []) + fallback["skills"])),
            "projects": ai_result.get("projects") or fallback["projects"],
        }
    return _fallback_extract(text)
