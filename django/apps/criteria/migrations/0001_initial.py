# Generated by Django 5.1.4 on 2023-03-05 14:21

import common.validators
import computedfields.resolver
import criteria.models
import datetime
import django.db.models.deletion
import markdownfield.models
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('common', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='JobAssessment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('package_id', models.CharField(max_length=64, verbose_name='Package ID')),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('logo', models.ImageField(blank=True, null=True, upload_to=criteria.models.job_assessment_logo_path, validators=[common.validators.ValidateFileSize(max=1)], verbose_name='Logo')),
                ('short_description', models.CharField(max_length=255, verbose_name='Short Description')),
                ('description', markdownfield.models.MarkdownField(rendered_field='description_rendered')),
                ('resumable', models.BooleanField(default=False, verbose_name='Resumable')),
                ('retry_interval', models.DurationField(default=datetime.timedelta(days=7), verbose_name='Retry Interval')),
                ('count_limit', models.PositiveIntegerField(default=10, verbose_name='Count Limit')),
                ('time_limit', models.DurationField(default=datetime.timedelta(seconds=1800), verbose_name='Time Limit')),
            ],
            options={
                'verbose_name': 'Job Assessment',
                'verbose_name_plural': 'Job Assessments',
            },
        ),
        migrations.CreateModel(
            name='JobAssessmentJob',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('required', models.BooleanField(default=False, verbose_name='Required')),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_assessment_jobs', to='common.job', verbose_name='Job')),
                ('job_assessment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_assessment_jobs', to='criteria.jobassessment', verbose_name='Job Assessment')),
            ],
            options={
                'verbose_name': 'Job Assessment Job',
                'verbose_name_plural': 'Job Assessment Jobs',
                'unique_together': {('job_assessment', 'job')},
            },
        ),
        migrations.AddField(
            model_name='jobassessment',
            name='related_jobs',
            field=models.ManyToManyField(related_name='assessments', through='criteria.JobAssessmentJob', to='common.job', verbose_name='Related Jobs'),
        ),
        migrations.CreateModel(
            name='JobAssessmentResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raw_status', models.CharField(default='In Progress', max_length=64, verbose_name='Status')),
                ('raw_score', models.JSONField(blank=True, null=True, verbose_name='Raw Score')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('order_id', models.UUIDField(default=uuid.uuid4, editable=False, verbose_name='Order ID')),
                ('report_url', models.URLField(blank=True, editable=False, null=True, verbose_name='Report URL')),
                ('score', models.CharField(blank=True, choices=[('average', 'Average'), ('good', 'Good'), ('great', 'Great'), ('exceptional', 'Exceptional')], editable=False, max_length=32, null=True)),
                ('status', models.CharField(blank=True, choices=[('not_started', 'Not Started'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('timeout', 'Timeout')], default='not_started', editable=False, max_length=32, null=True)),
                ('job_assessment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='results', to='criteria.jobassessment', verbose_name='Job Assessment')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='job_assessment_results', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Job Assessment Result',
                'verbose_name_plural': 'Job Assessment Results',
            },
            bases=(computedfields.resolver._ComputedFieldsModelBase, models.Model),
        ),
    ]
