import json

from django import forms
from .models import Job, JobQuiz


class JobQuizForm(forms.ModelForm):
    questions_text = forms.CharField(
        label="Quiz Questions (JSON format)",
        widget=forms.Textarea(attrs={"rows": 10, "placeholder": (
            '[{"option_1": "...", "option_2": "...", "option_3": "...", "option_4": "...", '
            '"question": "...", "correct_answer": "option_2"}]'
        )}),
    )

    class Meta:
        model = JobQuiz
        fields = ["quiz_name", "quiz_timing_minutes"]

    def clean_questions_text(self):
        raw = self.cleaned_data["questions_text"]
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise forms.ValidationError(f"Invalid JSON: {exc}")
        if not isinstance(data, list) or not data:
            raise forms.ValidationError("Questions must be a non-empty JSON list.")
        for q in data:
            required_keys = {"question", "option_1", "option_2", "option_3", "option_4", "correct_answer"}
            if not required_keys.issubset(q.keys()):
                raise forms.ValidationError(f"Each question needs keys: {required_keys}")
        return data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.questions = self.cleaned_data["questions_text"]
        if commit:
            instance.save()
        return instance


class JobForm(forms.ModelForm):
    educations = forms.CharField(
        label="Education (comma separated, e.g. Bsc.CS, MCA)",
        widget=forms.TextInput(attrs={"placeholder": "Bsc.CS, MCA"}),
    )
    skills = forms.CharField(
        label="Skills required (comma separated)",
        widget=forms.TextInput(attrs={"placeholder": "Python, SQL"}),
    )

    class Meta:
        model = Job
        fields = ["title", "description", "roles_responsibilities", "openings", "salary",
                  "min_cgpa", "job_quiz"]

    def __init__(self, *args, company=None, **kwargs):
        super().__init__(*args, **kwargs)
        if company is not None:
            self.fields["job_quiz"].queryset = JobQuiz.objects.filter(company=company)
        self.fields["job_quiz"].required = False
