from django import forms
from django.contrib.auth import authenticate
from .models import User


class StudentRegisterForm(forms.Form):
    student_name = forms.CharField(max_length=150, label="Student Name")
    student_mail = forms.EmailField(label="Student Mail")
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        pwd, cpwd = cleaned.get("password"), cleaned.get("confirm_password")
        if pwd and cpwd and pwd != cpwd:
            raise forms.ValidationError("Passwords do not match.")
        email = cleaned.get("student_mail")
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return cleaned

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data["student_mail"].split("@")[0] + "_stu",
            email=data["student_mail"],
            password=data["password"],
            first_name=data["student_name"],
            role=User.Role.CANDIDATE,
        )
        return user


class CompanyRegisterForm(forms.Form):
    company_name = forms.CharField(max_length=150, label="Company Name")
    company_mail = forms.EmailField(label="Company Mail")
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        pwd, cpwd = cleaned.get("password"), cleaned.get("confirm_password")
        if pwd and cpwd and pwd != cpwd:
            raise forms.ValidationError("Passwords do not match.")
        email = cleaned.get("company_mail")
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return cleaned

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data["company_mail"].split("@")[0] + "_co",
            email=data["company_mail"],
            password=data["password"],
            first_name=data["company_name"],
            role=User.Role.COMPANY,
        )
        return user


class LoginForm(forms.Form):
    mail = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        user = authenticate(email=cleaned.get("mail"), password=cleaned.get("password"))
        if user is None:
            raise forms.ValidationError("Invalid email or password.")
        cleaned["user"] = user
        return cleaned
