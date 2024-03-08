import csv
from datetime import timedelta

from criteria.models import JobAssessment

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Import job assessments from a CSV file into the database"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="The path to the CSV file")

    @transaction.atomic
    def handle(self, **kwargs):
        csv_file = kwargs["csv_file"]
        try:
            with open(csv_file, newline="") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    duration = timedelta(minutes=int(float(row["duration"])))
                    JobAssessment.objects.update_or_create(
                        title=row["title"],
                        defaults={
                            "short_description": row["short_description"],
                            "time_limit": duration,
                            "description": row["content"],
                            "package_id": "fake_package_id",
                        },
                    )
            self.stdout.write(self.style.SUCCESS("Successfully imported job assessments"))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {csv_file}"))
        except PermissionError:
            self.stdout.write(self.style.ERROR(f"Permission denied: {csv_file}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
