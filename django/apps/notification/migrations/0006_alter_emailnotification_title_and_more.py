# Generated by Django 5.1.4 on 2024-01-14 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0005_alter_campaignnotification_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailnotification',
            name='title',
            field=models.TextField(verbose_name='Title'),
        ),
        migrations.AlterField(
            model_name='inappnotification',
            name='title',
            field=models.TextField(verbose_name='Title'),
        ),
        migrations.AlterField(
            model_name='pushnotification',
            name='title',
            field=models.TextField(verbose_name='Title'),
        ),
    ]
