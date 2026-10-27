from django.core.management.base import BaseCommand
from candidateapp.utils.ml_models import train_and_save_models


class Command(BaseCommand):
    help = "Trains and caches the Salary Prediction and Placement Probability ML models."

    def handle(self, *args, **options):
        train_and_save_models()
        self.stdout.write(self.style.SUCCESS("ML models trained and saved to candidateapp/ml_artifacts/"))
