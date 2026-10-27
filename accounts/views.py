from django.contrib.auth import login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect

from .forms import StudentRegisterForm, CompanyRegisterForm, LoginForm
from .models import User


def register_view(request):
    active_tab = request.POST.get("role_tab", request.GET.get("role", "student"))
    student_form = StudentRegisterForm(request.POST if (request.method == "POST" and active_tab == "student") else None)
    company_form = CompanyRegisterForm(request.POST if (request.method == "POST" and active_tab == "company") else None)

    if request.method == "POST":
        if active_tab == "student" and student_form.is_valid():
            user = student_form.save()
            messages.success(request, "Registration successful. Please log in.")
            return redirect("accounts:login")
        if active_tab == "company" and company_form.is_valid():
            user = company_form.save()
            messages.success(request, "Company registered successfully. Please log in.")
            return redirect("accounts:login")

    return render(request, "registration/register.html", {
        "student_form": student_form,
        "company_form": company_form,
        "active_tab": active_tab,
    })


def login_view(request):
    if request.user.is_authenticated:
        return redirect("accounts:redirect_after_login")
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.cleaned_data["user"]
        django_login(request, user)
        return redirect("accounts:redirect_after_login")
    return render(request, "registration/login.html", {"form": form})


@login_required
def redirect_after_login(request):
    role = request.user.role
    if role == User.Role.ADMIN or request.user.is_superuser:
        return redirect("adminapp:dashboard")
    if role == User.Role.COMPANY:
        return redirect("companyapp:dashboard")
    return redirect("candidateapp:dashboard")


def logout_view(request):
    django_logout(request)
    return redirect("accounts:login")
