# Generated by Django 5.1.4 on 2023-08-31 23:55

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cv', '0002_generatedcv_additional_sections_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GeneratedCVContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('work_experiences', models.JSONField(blank=True, null=True, verbose_name='Work Experiences')),
                ('educations', models.JSONField(blank=True, null=True, verbose_name='Educations')),
                ('certifications', models.JSONField(blank=True, null=True, verbose_name='Certifications')),
                ('additional_sections', models.JSONField(blank=True, null=True, verbose_name='Additional Sections')),
                ('input_json', models.JSONField(blank=True, null=True, verbose_name='Input JSON')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cv_contents', to=settings.AUTH_USER_MODEL, unique=True, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Generated CV Contents',
                'verbose_name_plural': 'Generated CV Contents',
            },
        ),
    ]
