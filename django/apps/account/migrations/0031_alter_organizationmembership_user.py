# Generated by Django 5.1.1 on 2023-07-15 15:39

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_account', '0030_remove_communicateorganizationmethod_email_code_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organizationmembership',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='organization_memberships', to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
    ]
