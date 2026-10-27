from django.contrib import admin
from .models import (
    CandidateProfile, Skill, Project, ResumeAnalysis, ProgressLog,
    CareerRecommendation, RoadmapStep, SalaryPredictionResult, PlacementProbabilityResult,
)

admin.site.register(CandidateProfile)
admin.site.register(Skill)
admin.site.register(Project)
admin.site.register(ResumeAnalysis)
admin.site.register(ProgressLog)
admin.site.register(CareerRecommendation)
admin.site.register(RoadmapStep)
admin.site.register(SalaryPredictionResult)
admin.site.register(PlacementProbabilityResult)
