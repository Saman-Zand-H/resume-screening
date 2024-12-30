from common.populators import BasePopulator
from common.utils import get_all_subclasses

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Populate initial data defined in populators"

    @transaction.atomic
    def handle(self, *args, **options):
        for populator_class in get_all_subclasses(BasePopulator):
            self.stdout.write(f"Populating {populator_class.__name__}", style_func=self.style.HTTP_NOT_FOUND)
            populator = populator_class()
            populator.populate()
            self.stdout.write(f"Successfully populated {populator_class.__name__}", style_func=self.style.SUCCESS)
            self.stdout.write("+" * 40, style_func=self.style.HTTP_INFO)
