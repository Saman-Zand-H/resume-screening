import csv

from common.models import JobIndustry, Skill, SkillTopic

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Import skills, topics, and industries from a CSV file into the database"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="The path to the CSV file")

    @transaction.atomic
    def handle(self, **kwargs):
        csv_file = kwargs["csv_file"]
        try:
            with open(csv_file, newline="") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    industry, _ = JobIndustry.objects.get_or_create(title=row["industry"])
                    topic, _ = SkillTopic.objects.get_or_create(title=row["topic"], industry=industry)
                    Skill.objects.get_or_create(title=row["skill"], topic=topic)
            self.stdout.write(self.style.SUCCESS("Successfully imported skills"))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {csv_file}"))
        except PermissionError:
            self.stdout.write(self.style.ERROR(f"Permission denied: {csv_file}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
        self.import_skill(row)

    def import_skill(self, row):
        industry, _ = JobIndustry.objects.get_or_create(title=row["industry"])
        topic, _ = SkillTopic.objects.get_or_create(title=row["topic"], industry=industry)
        Skill.objects.get_or_create(title=row["skill"], topic=topic)
