from common.populators import BasePopulator
from common.utils import get_all_subclasses

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Populate initial data defined in populators"

    @transaction.atomic
    def handle(self, *args, **options):
        for populator_class in get_all_subclasses(BasePopulator):
            self.stdout.write(f"Populating {populator_class.__name__}")
            populator = populator_class()
            populator.populate()
