# Generated by Django 5.1.1 on 2024-04-26 08:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_account', '0077_remove_organizationemployeehiringstatushistory_cooperation_history_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organizationemployeecooperation',
            name='job_position_assignment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='cooperations', to='auth_account.jobpositionassignment', verbose_name='Job Position Assignment'),
        ),
    ]
