from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .decorators import company_required
from .forms import JobForm, JobQuizForm
from .models import CompanyProfile, Job, JobQuiz, JobApplication, Education, JobSkill


def _get_or_create_company_profile(user):
    profile, _ = CompanyProfile.objects.get_or_create(user=user, defaults={"company_name": user.first_name or user.email})
    return profile


@company_required
def dashboard(request):
    company = _get_or_create_company_profile(request.user)
    jobs = Job.objects.filter(company=company)
    total_applications = JobApplication.objects.filter(job__company=company).count()
    context = {
        "company": company,
        "jobs": jobs,
        "job_count": jobs.count(),
        "total_applications": total_applications,
    }
    return render(request, "company/dashboard.html", context)


@company_required
def job_list(request):
    company = _get_or_create_company_profile(request.user)
    jobs = Job.objects.filter(company=company).order_by("-created_at")
    return render(request, "company/job_list.html", {"jobs": jobs})


@company_required
def job_create(request):
    company = _get_or_create_company_profile(request.user)
    form = JobForm(request.POST or None, company=company)
    if request.method == "POST" and form.is_valid():
        job = form.save(commit=False)
        job.company = company
        job.save()
        for name in [s.strip() for s in form.cleaned_data["educations"].split(",") if s.strip()]:
            Education.objects.create(job=job, name=name)
        for name in [s.strip() for s in form.cleaned_data["skills"].split(",") if s.strip()]:
            JobSkill.objects.create(job=job, name=name)
        messages.success(request, "Job posted successfully.")
        return redirect("companyapp:job_list")
    return render(request, "company/job_form.html", {"form": form})


@company_required
def quiz_list(request):
    company = _get_or_create_company_profile(request.user)
    quizzes = JobQuiz.objects.filter(company=company).order_by("-created_at")
    return render(request, "company/quiz_list.html", {"quizzes": quizzes})


@company_required
def quiz_create(request):
    company = _get_or_create_company_profile(request.user)
    form = JobQuizForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        quiz = form.save(commit=False)
        quiz.company = company
        quiz.save()
        messages.success(request, "Job quiz created successfully.")
        return redirect("companyapp:quiz_list")
    return render(request, "company/quiz_form.html", {"form": form})


@company_required
def review_applicants(request, job_id):
    company = _get_or_create_company_profile(request.user)
    job = get_object_or_404(Job, id=job_id, company=company)
    applications = job.applications.select_related("candidate", "candidate__user", "quiz_attempt").order_by("-applied_at")

    if request.method == "POST":
        app_id = request.POST.get("application_id")
        new_status = request.POST.get("status")
        application = get_object_or_404(JobApplication, id=app_id, job=job)
        if new_status in dict(JobApplication.STATUS_CHOICES):
            application.status = new_status
            application.save()
            messages.success(request, f"Status updated for {application.candidate.user.email}")
        return redirect("companyapp:review_applicants", job_id=job.id)

    return render(request, "company/review_applicants.html", {
        "job": job,
        "applications": applications,
        "max_violations": getattr(settings, "MAX_QUIZ_VIOLATIONS", 3),
    })
