# Generated by Django 5.1.4 on 2023-03-06 17:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_account', '0002_resume_about_me_resume_headline'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resume',
            name='resume_json',
            field=models.JSONField(blank=True, default=dict, null=True, verbose_name='Resume JSON'),
        ),
    ]
