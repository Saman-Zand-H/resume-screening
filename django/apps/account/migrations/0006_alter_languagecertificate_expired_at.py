# Generated by Django 5.1.1 on 2023-03-16 18:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_account', '0005_remove_workexperience_job_workexperience_job_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='languagecertificate',
            name='expired_at',
            field=models.DateField(blank=True, null=True, verbose_name='Expired At'),
        ),
    ]
