from account.models import UserTask
from common.utils import fj
from flex_pubsub.tasks import task_registry

from django.core.management import BaseCommand
from django.db.models.lookups import In


class Command(BaseCommand):
    def handle(self, *args, **options):
        task_slugs = task_registry.get_all_tasks().keys()
        matched_tasks = UserTask.objects.exclude(**{fj(UserTask.task_name, In.lookup_name): task_slugs})
        if not matched_tasks.exists():
            self.stdout.write("[!] No tasks found out of sync.", style_func=self.style.SUCCESS)
            return

        self.stdout.write(f"[+] Deleting tasks: {", ".join(task_slugs)}", style_func=self.style.WARNING)
        matched_tasks.delete()
