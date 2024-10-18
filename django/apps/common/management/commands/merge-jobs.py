import json

from common.models import Job
from common.utils import merge_relations

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Merge jobs and industries from json file into the database"

    def add_arguments(self, parser):
        parser.add_argument("json_file", type=str, help="The path to the JSON file")

    @transaction.atomic
    def handle(self, **kwargs):
        json_file = kwargs["json_file"]
        try:
            with open(json_file, newline="") as file:
                mergeables = json.load(file)
                for mergeable in mergeables:
                    group = mergeable["group"]
                    new_title = mergeable.get("new_title")
                    merge_pk = mergeable.get("merge_pk")
                    targets = Job.objects.filter(pk__in=[i[0] for i in group])

                    if merge_pk or new_title:
                        source = Job.objects.get(pk=merge_pk) if merge_pk else Job.objects.create(title=new_title)
                        targets = targets.exclude(pk=source.pk) if merge_pk else targets
                        industries = targets.values_list(Job.industries.field.name, flat=True)
                        source.industries.add(*industries)
                        merge_relations(source, *targets)
                        targets.delete()

            self.stdout.write(self.style.SUCCESS("Successfully imported jobs"))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {json_file}"))
