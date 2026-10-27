def compute_match_percent(candidate_skills: list, job_skills: list) -> float:
    candidate_set = {s.strip().lower() for s in candidate_skills if s.strip()}
    job_set = {s.strip().lower() for s in job_skills if s.strip()}
    if not job_set:
        return 0.0
    overlap = len(candidate_set & job_set)
    return round((overlap / len(job_set)) * 100, 1)
