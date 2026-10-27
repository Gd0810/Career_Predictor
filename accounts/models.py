from django.contrib.auth.models import AbstractUser
from django.db import models


class UserManager(models.Manager):
    pass


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        COMPANY = "company", "Company"
        CANDIDATE = "candidate", "Candidate"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CANDIDATE)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return f"{self.email} ({self.role})"

    def save(self, *args, **kwargs):
        # Django superusers created via createsuperuser are treated as Admin role.
        if self.is_superuser and self.role != self.Role.ADMIN:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)
