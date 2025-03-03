# Generated by Django 5.1.4 on 2024-04-11 15:35

import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_account', '0075_merge_20250128_1520'),
        ('notification', '0013_campaign_max_attempts'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPushNotificationToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('device_token', models.CharField(max_length=255, verbose_name='Device Token')),
                ('device', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='push_notification_token', to='auth_account.userdevice', verbose_name='Device')),
            ],
            options={
                'verbose_name': 'User Push Notification Token',
                'verbose_name_plural': 'User Push Notification Tokens',
            },
        ),
        migrations.DeleteModel(
            name='UserDevice',
        ),
    ]
