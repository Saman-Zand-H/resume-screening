# Generated by Django 5.1.4 on 2024-04-28 14:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0012_auto_20250130_1455'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='job',
            name='industry',
        ),
    ]
