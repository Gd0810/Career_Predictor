from django.contrib import admin
from .models import CompanyProfile, Job, JobQuiz, JobApplication, Education, JobSkill, QuizAttempt

admin.site.register(CompanyProfile)
admin.site.register(Job)
admin.site.register(JobQuiz)
admin.site.register(JobApplication)
admin.site.register(Education)
admin.site.register(JobSkill)
admin.site.register(QuizAttempt)
