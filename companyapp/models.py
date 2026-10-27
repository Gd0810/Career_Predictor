from django.conf import settings
from django.db import models

from candidateapp.models import CandidateProfile


class CompanyProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="company_profile")
    company_name = models.CharField(max_length=200)
    website = models.URLField(blank=True)
    about = models.TextField(blank=True)

    def __str__(self):
        return self.company_name


class JobQuiz(models.Model):
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name="quizzes")
    quiz_name = models.CharField(max_length=200)
    quiz_timing_minutes = models.PositiveIntegerField(help_text="Duration of the quiz in minutes")
    questions = models.JSONField(
        help_text=(
            'JSON list, e.g. [{"question": "...", "option_1": "...", "option_2": "...", '
            '"option_3": "...", "option_4": "...", "correct_answer": "option_2"}]'
        )
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.quiz_name

    @property
    def total_questions(self):
        return len(self.questions or [])


class Education(models.Model):
    job = models.ForeignKey("Job", on_delete=models.CASCADE, related_name="educations")
    name = models.CharField(max_length=150)  # e.g. "B.Sc CS", "MCA"

    def __str__(self):
        return self.name


class JobSkill(models.Model):
    job = models.ForeignKey("Job", on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Job(models.Model):
    company = models.ForeignKey(CompanyProfile, on_delete=models.CASCADE, related_name="jobs")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    roles_responsibilities = models.TextField(blank=True)
    openings = models.PositiveIntegerField(default=1)
    salary = models.CharField(max_length=100, blank=True, help_text="e.g. 5-8 LPA")
    min_cgpa = models.FloatField()
    job_quiz = models.ForeignKey(JobQuiz, on_delete=models.SET_NULL, blank=True, null=True, related_name="jobs")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} @ {self.company.company_name}"

    @property
    def skill_names(self):
        return list(self.skills.values_list("name", flat=True))

    @property
    def education_names(self):
        return list(self.educations.values_list("name", flat=True))


class JobApplication(models.Model):
    STATUS_CHOICES = [
        ("applied", "Applied"),
        ("next_round", "Select for next round"),
        ("on_hold", "On hold"),
        ("rejected", "Rejected"),
    ]
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="applied")
    match_percent = models.FloatField(default=0)
    quiz_score = models.FloatField(blank=True, null=True)
    quiz_total = models.IntegerField(blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("job", "candidate")

    def __str__(self):
        return f"{self.candidate.user.email} -> {self.job.title}"


class QuizAttempt(models.Model):
    application = models.OneToOneField(JobApplication, on_delete=models.CASCADE, related_name="quiz_attempt")
    answers = models.JSONField(default=dict, blank=True)
    score = models.FloatField(default=0)
    total_questions = models.IntegerField(default=0)
    violation_count = models.PositiveIntegerField(default=0)
    auto_submitted = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
