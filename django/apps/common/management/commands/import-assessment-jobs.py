import csv
import json

from common.models import Job
from criteria.models import JobAssessment, JobAssessmentJob

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
                    assessment = JobAssessment.objects.get(title=row["title"])
                    jobs = json.loads(row["jobs"])
                    for job_title, required in jobs.items():
                        job = Job.objects.filter(title=job_title).first()
                        if not job:
                            self.stdout.write(self.style.WARNING(f"Job not found: {job_title}"))
                            continue
                        JobAssessmentJob.objects.update_or_create(
                            job=job,
                            job_assessment=assessment,
                            defaults={"required": required.lower() == "mandatory"},
                        )
            self.stdout.write(self.style.SUCCESS("Successfully imported job assessments"))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {csv_file}"))
        except PermissionError:
            self.stdout.write(self.style.ERROR(f"Permission denied: {csv_file}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
