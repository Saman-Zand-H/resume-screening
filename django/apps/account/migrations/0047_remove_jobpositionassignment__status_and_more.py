# Generated by Django 5.1.1 on 2025-01-04 13:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_account', '0046_alter_jobpositioninterview_options_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='jobpositionassignment',
            name='_status',
        ),
        migrations.AddField(
            model_name='jobpositionassignment',
            name='interview_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Interview Date'),
        ),
        migrations.AddField(
            model_name='jobpositionassignment',
            name='result_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Result Date'),
        ),
        migrations.AddField(
            model_name='jobpositionassignment',
            name='status',
            field=models.CharField(choices=[('not_reviewed', 'Not Reviewed'), ('awaiting_interview_date', 'Awaiting Interview Date'), ('interview_scheduled', 'Interview Scheduled'), ('interviewing', 'Interviewing'), ('awaiting_interview_results', 'Awaiting Interview Results'), ('interview_canceled_by_jobseeker', 'Interview Canceled By Jobseeker'), ('interview_canceled_by_employer', 'Interview Canceled By Employer'), ('rejected_at_interview', 'Rejected At Interview'), ('rejected', 'Rejected'), ('hired', 'Hired')], default='not_reviewed', max_length=50, verbose_name='Status'),
        ),
        migrations.AlterField(
            model_name='jobpositionassignmentstatushistory',
            name='status',
            field=models.CharField(choices=[('not_reviewed', 'Not Reviewed'), ('awaiting_interview_date', 'Awaiting Interview Date'), ('interview_scheduled', 'Interview Scheduled'), ('interviewing', 'Interviewing'), ('awaiting_interview_results', 'Awaiting Interview Results'), ('interview_canceled_by_jobseeker', 'Interview Canceled By Jobseeker'), ('interview_canceled_by_employer', 'Interview Canceled By Employer'), ('rejected_at_interview', 'Rejected At Interview'), ('rejected', 'Rejected'), ('hired', 'Hired')], max_length=50, verbose_name='Status'),
        ),
        migrations.DeleteModel(
            name='JobPositionInterview',
        ),
    ]
