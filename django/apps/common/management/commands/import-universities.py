import csv

from common.models import University

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Import universities from a CSV file into the database"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="The path to the CSV file")

    @transaction.atomic
    def handle(self, **kwargs):
        csv_file = kwargs["csv_file"]
        try:
            with open(csv_file, newline="") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    websites = row["website"].split("|")
                    University.objects.get_or_create(
                        name=row["name"], defaults={"websites": list(filter(bool, map(str.strip, websites)))}
                    )
            self.stdout.write(self.style.SUCCESS("Successfully imported universities"))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {csv_file}"))
        except PermissionError:
            self.stdout.write(self.style.ERROR(f"Permission denied: {csv_file}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
