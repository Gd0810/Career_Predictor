import json
from datetime import timedelta

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.conf import settings

from .decorators import candidate_required
from .forms import CandidateProfileForm, SkillsForm, ProjectForm, ResumeUploadForm
from .models import (
    CandidateProfile, Skill, Project, ResumeAnalysis, ProgressLog,
    CareerRecommendation, RoadmapStep, SalaryPredictionResult, PlacementProbabilityResult,
)
from .utils.resume_parser import parse_resume
from .utils.resume_analyzer import analyze_resume
from .utils.roadmap import recommend_careers, generate_skill_roadmap
from .utils.external_links import external_job_links, free_course_links, paid_course_links
from .utils.ml_models import predict_salary, predict_placement
from .utils.matching import compute_match_percent
from .utils.career_data import CAREER_TREND

from companyapp.models import Job, JobApplication, QuizAttempt


def _get_or_create_profile(user):
    profile, _ = CandidateProfile.objects.get_or_create(user=user)
    return profile


@candidate_required
def dashboard(request):
    profile = _get_or_create_profile(request.user)
    applications = JobApplication.objects.filter(candidate=profile).select_related("job")
    context = {
        "profile": profile,
        "applications": applications,
        "skills": profile.skill_names,
        "resume_uploaded": bool(profile.resume),
    }
    return render(request, "candidate/dashboard.html", context)


@candidate_required
def profile_view(request):
    profile = _get_or_create_profile(request.user)
    form = CandidateProfileForm(request.POST or None, request.FILES or None, instance=profile)
    skills_form = SkillsForm(initial={"skills": ", ".join(profile.skill_names)})
    project_form = ProjectForm()
    resume_form = ResumeUploadForm()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "save_profile" and form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("candidateapp:profile")

        if action == "save_skills":
            skills_form = SkillsForm(request.POST)
            if skills_form.is_valid():
                names = [s.strip() for s in skills_form.cleaned_data["skills"].split(",") if s.strip()]
                profile.skills.all().delete()
                for n in names:
                    Skill.objects.get_or_create(candidate=profile, name=n)
                messages.success(request, "Skills updated.")
                return redirect("candidateapp:profile")

        if action == "add_project":
            project_form = ProjectForm(request.POST)
            if project_form.is_valid():
                project = project_form.save(commit=False)
                project.candidate = profile
                project.save()
                messages.success(request, "Project added.")
                return redirect("candidateapp:profile")

        if action == "upload_resume":
            resume_form = ResumeUploadForm(request.POST, request.FILES)
            if resume_form.is_valid():
                profile.resume = resume_form.cleaned_data["resume"]
                profile.resume_uploaded_at = timezone.now()
                profile.save()

                extracted = parse_resume(profile.resume.path)
                profile.ai_extracted_raw = extracted

                if extracted.get("degree"):
                    profile.degree = extracted["degree"]
                if extracted.get("role"):
                    profile.role = extracted["role"]
                if extracted.get("cgpa") is not None:
                    profile.cgpa = extracted["cgpa"]
                if extracted.get("experience_years") is not None:
                    profile.experience_years = extracted["experience_years"]
                if extracted.get("experience_type"):
                    profile.experience_type = extracted["experience_type"]
                profile.save()

                for skill_name in extracted.get("skills", []):
                    Skill.objects.get_or_create(candidate=profile, name=skill_name.lower())
                for proj in extracted.get("projects", []):
                    if proj.get("title"):
                        Project.objects.get_or_create(
                            candidate=profile, title=proj["title"],
                            defaults={"description": proj.get("description", "")}
                        )
                sync_progress_logs(profile)
                messages.success(request, "Resume uploaded and auto-filled with high accuracy. Personal, academic & skill details updated!")
                return redirect("candidateapp:profile")

    context = {
        "profile": profile,
        "form": form,
        "skills_form": skills_form,
        "project_form": project_form,
        "resume_form": resume_form,
        "projects": profile.projects.all(),
    }
    return render(request, "candidate/profile.html", context)


def sync_progress_logs(profile):
    """Dynamically calculates and updates ProgressLog percent for each candidate skill based on:
    - Skill listed in candidate profile (+30%)
    - Verified in candidate resume (+20%)
    - Projects added to profile (+20%)
    - Matching RoadmapStep completed (+30%)
    """
    profile_skill_set = {s.lower() for s in profile.skill_names}

    resume_text = ""
    if profile.resume:
        try:
            from .utils.resume_parser import extract_text_from_resume
            resume_text = extract_text_from_resume(profile.resume.path).lower()
        except Exception:
            resume_text = ""

    projects = list(profile.projects.all())
    project_text = " ".join([p.title.lower() + " " + (p.description or "").lower() for p in projects])
    roadmap_steps = list(profile.roadmap_steps.all())

    # Build unique set of skills to track
    all_skills = set(profile.skill_names)
    for step in roadmap_steps:
        all_skills.add(step.skill_name)

    if not all_skills:
        return

    for skill_item in all_skills:
        s_lower = skill_item.lower()
        score = 0.0

        # 1. Listed in profile (+30%)
        if any(ps == s_lower or ps in s_lower or s_lower in ps for ps in profile_skill_set):
            score += 30.0

        # 2. Verified in parsed resume (+20%)
        if resume_text and s_lower in resume_text:
            score += 20.0

        # 3. Project exposure (+20% for specific match, +10% for general project presence)
        if projects:
            if any(term in project_text for term in s_lower.split() if len(term) > 2):
                score += 20.0
            else:
                score += 10.0

        # 4. Roadmap Step completion (+30% if done, +10% if pending step exists)
        matching_steps = [
            st for st in roadmap_steps
            if st.skill_name.lower() == s_lower or s_lower in st.skill_name.lower() or st.skill_name.lower() in s_lower
        ]
        if matching_steps:
            if any(st.is_completed for st in matching_steps):
                score += 30.0
            else:
                score += 10.0
        elif score > 0:
            score += 10.0

        final_percent = min(100.0, round(score, 1))
        if score > 0:
            final_percent = max(20.0, final_percent)

        log, _ = ProgressLog.objects.get_or_create(candidate=profile, skill_name=skill_item)
        log.progress_percent = final_percent
        log.save()


@candidate_required
def resume_analyzer_view(request):
    profile = _get_or_create_profile(request.user)
    latest = profile.analyses.order_by("-created_at").first()

    if request.method == "POST":
        if not profile.resume:
            messages.error(request, "Please upload a resume in your Profile first.")
            return redirect("candidateapp:profile")
        result = analyze_resume(profile.resume.path)
        latest = ResumeAnalysis.objects.create(
            candidate=profile,
            key_points=result.get("key_points", []),
            strengths=result.get("strengths", []),
            improvements=result.get("improvements", []),
            quality_score=result.get("quality_score", 0),
            ats_score=result.get("ats_score", 0),
        )
        sync_progress_logs(profile)
        messages.success(request, "Resume analyzed.")
        return redirect("candidateapp:resume_analyzer")

    sync_progress_logs(profile)
    progress_logs = profile.progress_logs.order_by("-progress_percent", "skill_name")
    return render(request, "candidate/resume_analyzer.html", {
        "profile": profile, "analysis": latest, "progress_logs": progress_logs,
    })


@candidate_required
def roadmap_view(request):
    profile = _get_or_create_profile(request.user)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "get_recommendations":
            recs = recommend_careers(profile)
            profile.career_recs.all().delete()
            for r in recs:
                CareerRecommendation.objects.create(
                    candidate=profile, career_name=r["career_name"], match_percent=r["match_percent"]
                )
            messages.success(request, "Career recommendations generated.")
            return redirect("candidateapp:roadmap")

        if action == "generate_roadmap":
            target_career = request.POST.get("target_career")
            steps = generate_skill_roadmap(profile, target_career)
            RoadmapStep.objects.filter(candidate=profile).delete()
            candidate_skills = {s.lower() for s in profile.skill_names}
            for s in steps:
                s_name = s["skill_name"].lower()
                is_done = any(cs in s_name or s_name in cs for cs in candidate_skills) if candidate_skills else False
                RoadmapStep.objects.create(
                    candidate=profile, target_career=target_career,
                    skill_name=s["skill_name"], stage=s["stage"], sequence_no=s["sequence_no"],
                    is_completed=is_done,
                )
            sync_progress_logs(profile)
            messages.success(request, f"Roadmap generated for {target_career}.")
            return redirect("candidateapp:roadmap")

        if action == "toggle_step":
            step = get_object_or_404(RoadmapStep, id=request.POST.get("step_id"), candidate=profile)
            step.is_completed = not step.is_completed
            step.save()
            sync_progress_logs(profile)
            return redirect("candidateapp:roadmap")

    recommendations = list(profile.career_recs.all())
    for rec in recommendations:
        rec.trend = CAREER_TREND.get(rec.career_name, "Stable")
    roadmap_steps = profile.roadmap_steps.all()
    return render(request, "candidate/roadmap.html", {
        "profile": profile, "recommendations": recommendations, "roadmap_steps": roadmap_steps,
    })


@candidate_required
def app_jobs_list(request):
    profile = _get_or_create_profile(request.user)
    jobs = Job.objects.filter(is_active=True).select_related("company").prefetch_related("skills")
    applied_job_ids = set(JobApplication.objects.filter(candidate=profile).values_list("job_id", flat=True))

    job_cards = []
    for job in jobs:
        match = compute_match_percent(profile.skill_names, job.skill_names)
        job_cards.append({"job": job, "match_percent": match, "already_applied": job.id in applied_job_ids})

    return render(request, "candidate/app_jobs_list.html", {"job_cards": job_cards})


@candidate_required
def app_job_detail(request, job_id):
    profile = _get_or_create_profile(request.user)
    job = get_object_or_404(Job, id=job_id, is_active=True)
    match_percent = compute_match_percent(profile.skill_names, job.skill_names)
    application = JobApplication.objects.filter(job=job, candidate=profile).first()

    if request.method == "POST" and not application:
        if job.job_quiz_id:
            # must attend quiz first - redirect to quiz page
            application = JobApplication.objects.create(job=job, candidate=profile, match_percent=match_percent, status="applied")
            return redirect("candidateapp:take_quiz", application_id=application.id)
        else:
            JobApplication.objects.create(job=job, candidate=profile, match_percent=match_percent, status="applied")
            messages.success(request, "Applied successfully.")
            return redirect("candidateapp:app_jobs_list")

    return render(request, "candidate/app_job_detail.html", {
        "job": job, "match_percent": match_percent, "application": application,
    })


@candidate_required
def take_quiz(request, application_id):
    profile = _get_or_create_profile(request.user)
    application = get_object_or_404(JobApplication, id=application_id, candidate=profile)
    quiz = application.job.job_quiz
    if quiz is None:
        raise PermissionDenied("This job has no quiz attached.")

    attempt, _ = QuizAttempt.objects.get_or_create(
        application=application, defaults={"total_questions": quiz.total_questions}
    )
    if attempt.submitted_at:
        return redirect("candidateapp:app_jobs_list")

    context = {
        "job": application.job,
        "quiz": quiz,
        "application": application,
        "attempt": attempt,
        "max_violations": settings.MAX_QUIZ_VIOLATIONS,
        "questions_json": json.dumps(quiz.questions),
    }
    return render(request, "candidate/quiz.html", context)


@candidate_required
def submit_quiz(request, application_id):
    profile = _get_or_create_profile(request.user)
    application = get_object_or_404(JobApplication, id=application_id, candidate=profile)
    quiz = application.job.job_quiz
    attempt = get_object_or_404(QuizAttempt, application=application)

    if request.method == "POST" and not attempt.submitted_at:
        answers = json.loads(request.POST.get("answers_json", "{}"))
        violation_count = int(request.POST.get("violation_count", 0))
        auto_submitted = request.POST.get("auto_submitted") == "true"

        correct = 0
        for idx, q in enumerate(quiz.questions):
            given = answers.get(str(idx))
            if given == q.get("correct_answer"):
                correct += 1
        score = round((correct / max(1, len(quiz.questions))) * 100, 1)

        attempt.answers = answers
        attempt.score = score
        attempt.total_questions = len(quiz.questions)
        attempt.violation_count = violation_count
        attempt.auto_submitted = auto_submitted
        attempt.submitted_at = timezone.now()
        attempt.save()

        application.quiz_score = score
        application.quiz_total = len(quiz.questions)
        application.save()

        messages.success(request, f"Quiz submitted. Score: {score}%. Your application is now recorded.")
        return redirect("candidateapp:app_jobs_list")

    return redirect("candidateapp:app_jobs_list")


@candidate_required
def external_jobs_view(request):
    profile = _get_or_create_profile(request.user)
    search_role = request.GET.get("search_role") or (profile.role or "software developer").replace("_", " ")
    location = request.GET.get("location") or "India"

    job_links = external_job_links(search_role, location)

    skills_to_learn = profile.skill_names[:6] or ["python", "sql", "javascript", "react", "django"]
    free_courses = free_course_links(skills_to_learn)
    paid_courses = paid_course_links(skills_to_learn)

    return render(request, "candidate/external_jobs.html", {
        "profile": profile,
        "search_role": search_role,
        "location": location,
        "job_links": job_links,
        "free_courses": free_courses,
        "paid_courses": paid_courses,
        "skills_to_learn": skills_to_learn,
    })


@candidate_required
def salary_analysis_view(request):
    profile = _get_or_create_profile(request.user)
    salary_result = profile.salary_predictions.order_by("-created_at").first()
    placement_result = profile.placement_predictions.order_by("-created_at").first()

    if request.method == "POST":
        action = request.POST.get("action")
        skills_count = len(profile.skill_names)

        if action == "predict_salary":
            role = profile.role or "software_engineer"
            exp_years = profile.experience_years or 0
            pred, smin, smax = predict_salary(role, exp_years, skills_count, profile.cgpa or 7.0)
            salary_result = SalaryPredictionResult.objects.create(
                candidate=profile, role=role, predicted_salary=pred, salary_min=smin, salary_max=smax
            )
            messages.success(request, f"Salary prediction generated for {role.replace('_', ' ').title()}.")

        if action == "predict_placement":
            projects_count = profile.projects.count()
            proba, tips = predict_placement(profile.cgpa or 7.0, skills_count, projects_count)
            placement_result = PlacementProbabilityResult.objects.create(
                candidate=profile, probability_percent=proba, tips=tips
            )
            messages.success(request, "Placement probability analyzed.")

    salary_context = None
    if salary_result:
        p_sal = salary_result.predicted_salary
        salary_context = {
            "predicted": p_sal,
            "min": salary_result.salary_min,
            "max": salary_result.salary_max,
            "role_title": salary_result.role.replace("_", " ").title(),
            "yr1": round(p_sal * 1.15, 2),
            "yr3": round(p_sal * 1.45, 2),
            "yr5": round(p_sal * 1.95, 2),
        }

    placement_context = None
    if placement_result:
        prob = placement_result.probability_percent
        cgpa_score = min(100.0, round(((profile.cgpa or 7.0) / 10.0) * 100, 1))
        skills_score = min(100.0, round((len(profile.skill_names) / 10.0) * 100, 1))
        projects_score = min(100.0, round((profile.projects.count() / 3.0) * 100, 1))
        aptitude_score = 75.0

        if prob >= 80:
            tier_label = "High Placement Probability"
            tier_color = "#10b981"
        elif prob >= 60:
            tier_label = "Good Placement Probability"
            tier_color = "#6366f1"
        elif prob >= 40:
            tier_label = "Moderate Chance"
            tier_color = "#f59e0b"
        else:
            tier_label = "Needs Improvement"
            tier_color = "#ef4444"

        placement_context = {
            "probability": prob,
            "gap": round(100.0 - prob, 1),
            "tier_label": tier_label,
            "tier_color": tier_color,
            "cgpa_score": cgpa_score,
            "skills_score": skills_score,
            "projects_score": projects_score,
            "aptitude_score": aptitude_score,
            "tips": placement_result.tips,
        }

    return render(request, "candidate/salary_analysis.html", {
        "profile": profile,
        "salary_result": salary_result,
        "salary_context": salary_context,
        "placement_result": placement_result,
        "placement_context": placement_context,
    })
