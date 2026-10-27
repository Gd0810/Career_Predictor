from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from companyapp.models import CompanyProfile, Job, JobApplication
from candidateapp.models import CandidateProfile
from .decorators import superadmin_required


@superadmin_required
def dashboard(request):
    company_count = CompanyProfile.objects.count()
    candidate_count = CandidateProfile.objects.count()
    job_count = Job.objects.count()
    application_count = JobApplication.objects.count()

    since = timezone.now() - timedelta(days=30)
    jobs_per_company = (
        Job.objects.values("company__company_name").annotate(total=Count("id")).order_by("-total")[:8]
    )
    applications_by_status = (
        JobApplication.objects.values("status").annotate(total=Count("id"))
    )
    recent_users = User.objects.order_by("-date_joined")[:10]

    context = {
        "company_count": company_count,
        "candidate_count": candidate_count,
        "job_count": job_count,
        "application_count": application_count,
        "jobs_per_company": list(jobs_per_company),
        "applications_by_status": list(applications_by_status),
        "recent_users": recent_users,
    }
    return render(request, "adminapp/dashboard.html", context)


@superadmin_required
def manage_companies(request):
    companies = CompanyProfile.objects.select_related("user").order_by("-user__date_joined")
    return render(request, "adminapp/manage_companies.html", {"companies": companies})


@superadmin_required
def toggle_company_active(request, pk):
    company = get_object_or_404(CompanyProfile, pk=pk)
    company.user.is_active = not company.user.is_active
    company.user.save()
    messages.success(request, f"{company.company_name} is now {'active' if company.user.is_active else 'inactive'}.")
    return redirect("adminapp:manage_companies")


@superadmin_required
def delete_company(request, pk):
    company = get_object_or_404(CompanyProfile, pk=pk)
    name = company.company_name
    company.user.delete()
    messages.success(request, f"Deleted company: {name}")
    return redirect("adminapp:manage_companies")


@superadmin_required
def manage_candidates(request):
    candidates = CandidateProfile.objects.select_related("user").order_by("-user__date_joined")
    return render(request, "adminapp/manage_candidates.html", {"candidates": candidates})


@superadmin_required
def toggle_candidate_active(request, pk):
    candidate = get_object_or_404(CandidateProfile, pk=pk)
    candidate.user.is_active = not candidate.user.is_active
    candidate.user.save()
    messages.success(request, f"{candidate.user.email} is now {'active' if candidate.user.is_active else 'inactive'}.")
    return redirect("adminapp:manage_candidates")


@superadmin_required
def delete_candidate(request, pk):
    candidate = get_object_or_404(CandidateProfile, pk=pk)
    email = candidate.user.email
    candidate.user.delete()
    messages.success(request, f"Deleted candidate: {email}")
    return redirect("adminapp:manage_candidates")
