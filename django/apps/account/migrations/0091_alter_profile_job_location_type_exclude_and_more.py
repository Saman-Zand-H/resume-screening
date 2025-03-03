# Generated by Django 5.1.4 on 2024-06-30 20:22

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_account', '0090_auto_20250206_2000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='job_location_type_exclude',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('precise_location', 'On-site (Precise Location)'), ('limited_area', 'On-site (Within a Limited Area)'), ('remote', 'Remote'), ('hybrid', 'Hybrid'), ('on_the_road', 'On the road'), ('global', 'Global')], max_length=50), blank=True, null=True, size=None, verbose_name='Job Location Type Exclude'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='job_type_exclude',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('full_time', 'Full Time'), ('part_time', 'Part Time'), ('permanent', 'Permanent'), ('fix_term_contract', 'Fix Term Contract'), ('seasonal', 'Seasonal'), ('freelance', 'Freelance'), ('apprenticeship', 'Apprenticeship'), ('prince_edward_island', 'Prince Edward Island'), ('internship_co_op', 'Internship/Co-op')], max_length=50), blank=True, null=True, size=None, verbose_name='Job Type Exclude'),
        ),
    ]
