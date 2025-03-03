# Generated by Django 5.1.1 on 2024-01-20 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_account', '0064_organizationemployee'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobpositionassignment',
            name='status',
            field=models.CharField(choices=[('awaiting_jobseeker_approval', 'Awaiting Jobseeker Approval'), ('rejected_by_jobseeker', 'Rejected By Jobseeker'), ('not_reviewed', 'Not Reviewed'), ('awaiting_interview_date', 'Awaiting Interview Date'), ('interview_scheduled', 'Interview Scheduled'), ('interviewing', 'Interviewing'), ('awaiting_interview_results', 'Awaiting Interview Results'), ('interview_canceled_by_jobseeker', 'Interview Canceled By Jobseeker'), ('interview_canceled_by_employer', 'Interview Canceled By Employer'), ('rejected_at_interview', 'Rejected At Interview'), ('rejected', 'Rejected'), ('hired', 'Hired')], default='awaiting_jobseeker_approval', max_length=50, verbose_name='Status'),
        ),
        migrations.AlterField(
            model_name='jobpositionassignmentstatushistory',
            name='status',
            field=models.CharField(choices=[('awaiting_jobseeker_approval', 'Awaiting Jobseeker Approval'), ('rejected_by_jobseeker', 'Rejected By Jobseeker'), ('not_reviewed', 'Not Reviewed'), ('awaiting_interview_date', 'Awaiting Interview Date'), ('interview_scheduled', 'Interview Scheduled'), ('interviewing', 'Interviewing'), ('awaiting_interview_results', 'Awaiting Interview Results'), ('interview_canceled_by_jobseeker', 'Interview Canceled By Jobseeker'), ('interview_canceled_by_employer', 'Interview Canceled By Employer'), ('rejected_at_interview', 'Rejected At Interview'), ('rejected', 'Rejected'), ('hired', 'Hired')], max_length=50, verbose_name='Status'),
        ),
    ]
