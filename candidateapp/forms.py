from django import forms
from .models import CandidateProfile, Project


class ResumeUploadForm(forms.Form):
    resume = forms.FileField(label="Upload Resume (PDF)")


class CandidateProfileForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = ["photo", "degree", "role", "cgpa", "experience_type", "experience_years"]
        widgets = {
            "cgpa": forms.NumberInput(attrs={"step": "0.01", "min": 0, "max": 10}),
            "experience_years": forms.NumberInput(attrs={"step": "0.1", "min": 0}),
        }


class SkillsForm(forms.Form):
    skills = forms.CharField(
        label="Skills (comma separated)",
        widget=forms.TextInput(attrs={"placeholder": "python, sql, django"}),
        required=False,
    )


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["title", "description"]
