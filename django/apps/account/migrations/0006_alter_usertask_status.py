# Generated by Django 5.1.4 on 2023-03-14 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_account', '0005_remove_workexperience_job_workexperience_job_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usertask',
            name='status',
            field=models.CharField(blank=True, choices=[('scheduled', 'Scheduled'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('failed', 'Failed')], max_length=50, null=True),
        ),
    ]
