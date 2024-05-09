import random
import string

from account.models import User
from graphql_auth.models import UserStatus

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

DEFAULT_PREFIX = "cpj-test-user-zqML-"


class Command(BaseCommand):
    help = "Create or delete dummy users"

    def add_arguments(self, parser):
        parser.add_argument("-c", "--create", type=int, help="Number of dummy users to create")
        parser.add_argument("-d", "--delete", action="store_true", help="Delete dummy users")
        parser.add_argument("-s", "--prefix", type=str, default=DEFAULT_PREFIX, help="Prefix for dummy users")
        parser.add_argument("-p", "--password", type=str, help="Password for dummy users")

    def handle(self, *args, **options):
        num_to_create = options["create"]
        delete = options["delete"]
        prefix = options["prefix"]
        password = options.get("password")

        if num_to_create and delete:
            raise CommandError("Cannot use --create and --delete at the same time.")

        if num_to_create:
            self.create_dummy_users(num_to_create, prefix, password)
        elif delete:
            self.delete_dummy_users(prefix)
        else:
            raise CommandError("Either --create or --delete must be specified.")

    def create_dummy_users(self, count, prefix, password=None):
        if not password:
            password = "".join(random.choices(string.ascii_letters + string.digits, k=12))
        hashed_password = make_password(password)
        emails = set(f"{prefix}{i}@example.com" for i in range(count))
        existing_emails = set(User.objects.filter(email__in=emails).values_list("email", flat=True))
        users = [
            User(username=email, email=email, password=hashed_password) for email in emails.difference(existing_emails)
        ]

        with transaction.atomic():
            User.objects.bulk_create(users)
            User.objects.filter(email__in=existing_emails).update(password=hashed_password)
            existing_statuses = UserStatus.objects.filter(user__in=users).values_list("user", flat=True)
            user_statuses = [UserStatus(user=user, verified=True) for user in users if user.pk not in existing_statuses]
            UserStatus.objects.bulk_create(user_statuses)
            UserStatus.objects.filter(user__in=users).update(verified=True)

        self.stdout.write(self.style.SUCCESS(f"Successfully created {len(users)} users with password: {password}"))

    def delete_dummy_users(self, prefix):
        users = User.objects.filter(username__startswith=prefix)
        count = users.count()
        with transaction.atomic():
            users.delete()
        self.stdout.write(self.style.SUCCESS(f"Successfully deleted {count} users"))
