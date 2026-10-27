from django.urls import path
from . import views

app_name = "companyapp"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/create/", views.job_create, name="job_create"),
    path("jobs/<int:job_id>/applicants/", views.review_applicants, name="review_applicants"),
    path("quizzes/", views.quiz_list, name="quiz_list"),
    path("quizzes/create/", views.quiz_create, name="quiz_create"),
]
