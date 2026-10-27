from django.urls import path
from . import views

app_name = "candidateapp"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("profile/", views.profile_view, name="profile"),
    path("resume-analyzer/", views.resume_analyzer_view, name="resume_analyzer"),
    path("roadmap/", views.roadmap_view, name="roadmap"),
    path("app-jobs/", views.app_jobs_list, name="app_jobs_list"),
    path("app-jobs/<int:job_id>/", views.app_job_detail, name="app_job_detail"),
    path("app-jobs/quiz/<int:application_id>/", views.take_quiz, name="take_quiz"),
    path("app-jobs/quiz/<int:application_id>/submit/", views.submit_quiz, name="submit_quiz"),
    path("external-jobs/", views.external_jobs_view, name="external_jobs"),
    path("salary-analysis/", views.salary_analysis_view, name="salary_analysis"),
]
