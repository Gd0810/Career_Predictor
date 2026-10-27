from django.conf import settings
from django.db import models


class CandidateProfile(models.Model):
    EXPERIENCE_CHOICES = [("fresher", "Fresher"), ("experienced", "Experienced")]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="candidate_profile")
    photo = models.ImageField(upload_to="photos/", blank=True, null=True)
    degree = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=150, blank=True, help_text="e.g. python_developer")
    cgpa = models.FloatField(blank=True, null=True)
    experience_type = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default="fresher")
    experience_years = models.FloatField(blank=True, null=True, help_text="Only if experienced")
    resume = models.FileField(upload_to="resumes/", blank=True, null=True)
    resume_uploaded_at = models.DateTimeField(blank=True, null=True)
    ai_extracted_raw = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Profile: {self.user.email}"

    @property
    def skill_names(self):
        return list(self.skills.values_list("name", flat=True))


class Skill(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ("candidate", "name")

    def __str__(self):
        return self.name


class Project(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="projects")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class ResumeAnalysis(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="analyses")
    created_at = models.DateTimeField(auto_now_add=True)
    key_points = models.JSONField(default=list, blank=True)     # Data Analyze Engine output
    strengths = models.JSONField(default=list, blank=True)
    improvements = models.JSONField(default=list, blank=True)
    quality_score = models.FloatField(default=0)
    ats_score = models.FloatField(default=0)

    def __str__(self):
        return f"Analysis for {self.candidate} @ {self.created_at:%Y-%m-%d}"


class ProgressLog(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="progress_logs")
    skill_name = models.CharField(max_length=100)
    progress_percent = models.FloatField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("candidate", "skill_name")


class CareerRecommendation(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="career_recs")
    career_name = models.CharField(max_length=150)
    match_percent = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-match_percent"]


class RoadmapStep(models.Model):
    STAGE_CHOICES = [
        ("beginner", "Beginner"), ("intermediate", "Intermediate"),
        ("advanced", "Advanced"), ("project", "Project"), ("job_ready", "Job Ready"),
    ]
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="roadmap_steps")
    target_career = models.CharField(max_length=150)
    skill_name = models.CharField(max_length=100)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES)
    sequence_no = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ["target_career", "sequence_no"]


class SalaryPredictionResult(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="salary_predictions")
    role = models.CharField(max_length=150)
    predicted_salary = models.FloatField()
    salary_min = models.FloatField()
    salary_max = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)


class PlacementProbabilityResult(models.Model):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="placement_predictions")
    probability_percent = models.FloatField()
    tips = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
