# Generated by Django 5.1.5 on 2024-04-19 14:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0015_rename_device_token_pushnotification_token_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='is_scheduler_active',
            field=models.BooleanField(default=False, verbose_name='Is Scheduler Active'),
        ),
    ]
