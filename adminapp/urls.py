from django.urls import path
from . import views

app_name = "adminapp"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("companies/", views.manage_companies, name="manage_companies"),
    path("companies/<int:pk>/toggle/", views.toggle_company_active, name="toggle_company_active"),
    path("companies/<int:pk>/delete/", views.delete_company, name="delete_company"),
    path("candidates/", views.manage_candidates, name="manage_candidates"),
    path("candidates/<int:pk>/toggle/", views.toggle_candidate_active, name="toggle_candidate_active"),
    path("candidates/<int:pk>/delete/", views.delete_candidate, name="delete_candidate"),
]
