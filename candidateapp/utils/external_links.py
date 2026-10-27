"""
Generates clickable, pre-filled search links to external job boards and course
platforms based on the candidate's role/skills.
"""
from urllib.parse import quote_plus


def external_job_links(role: str, location: str = "India") -> list:
    query = quote_plus(role or "software developer")
    loc = quote_plus(location)
    role_slug = (role or "software developer").lower().replace(" ", "-").replace("_", "-")

    return [
        {
            "site": "LinkedIn Jobs",
            "badge": "Corporate & Tech",
            "color": "#0077b5",
            "icon": "💼",
            "description": f"Find top corporate, MNC & remote {role} positions.",
            "url": f"https://www.linkedin.com/jobs/search/?keywords={query}&location={loc}",
        },
        {
            "site": "Naukri.com",
            "badge": "India's #1 Portal",
            "color": "#4a90e2",
            "icon": "🏢",
            "description": f"Explore verified corporate hiring listings for {role}.",
            "url": f"https://www.naukri.com/{role_slug}-jobs",
        },
        {
            "site": "Indeed Jobs",
            "badge": "Global & Local",
            "color": "#2164f3",
            "icon": "🌐",
            "description": f"Search thousands of verified {role} jobs across {location}.",
            "url": f"https://in.indeed.com/jobs?q={query}&l={loc}",
        },
        {
            "site": "Glassdoor",
            "badge": "Jobs & Salaries",
            "color": "#0caa41",
            "icon": "📊",
            "description": f"View salary insights and job postings for {role}.",
            "url": f"https://www.glassdoor.co.in/Job/jobs.htm?sc.keyword={query}",
        },
        {
            "site": "Unstop (Hackathons & Hiring)",
            "badge": "Challenges & Internships",
            "color": "#ff5722",
            "icon": "🏆",
            "description": f"Participate in hiring challenges & competitions for {role}.",
            "url": f"https://unstop.com/jobs?searchTerm={query}",
        },
        {
            "site": "Wellfound (AngelList)",
            "badge": "Startup & Remote",
            "color": "#111827",
            "icon": "🚀",
            "description": f"Connect with high-growth tech startups hiring {role}.",
            "url": f"https://wellfound.com/jobs?keyword={query}",
        },
    ]


def free_course_links(skills: list) -> list:
    results = []
    for skill in skills:
        q_skill = quote_plus(skill)
        results.append({
            "skill": skill.title(),
            "youtube_url": f"https://www.youtube.com/results?search_query={quote_plus(skill + ' tutorial for beginners full course')}",
            "freecodecamp_url": f"https://www.freecodecamp.org/news/search/?query={q_skill}",
            "coursera_url": f"https://www.coursera.org/search?query={q_skill}&priceAttr=free",
        })
    return results


def paid_course_links(skills: list) -> list:
    results = []
    for skill in skills:
        q_skill = quote_plus(skill)
        results.append({
            "skill": skill.title(),
            "udemy_url": f"https://www.udemy.com/courses/search/?q={q_skill}",
            "edx_url": f"https://www.edx.org/search?q={q_skill}",
            "hackerrank_url": f"https://www.hackerrank.com/domains/{skill.lower().replace(' ', '-')}",
        })
    return results
