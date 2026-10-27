from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="accounts:login", permanent=False)),
    path("accounts/", include("accounts.urls")),
    path("company/", include("companyapp.urls")),
    path("candidate/", include("candidateapp.urls")),
    path("dashboard-admin/", include("adminapp.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
