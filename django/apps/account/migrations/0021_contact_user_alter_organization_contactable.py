# Generated by Django 5.1.4 on 2023-04-20 19:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_account', '0020_alter_profile_contactable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='contactable',
            field=models.OneToOneField(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, to='auth_account.contactable', verbose_name='Contactable'),
        ),
    ]
