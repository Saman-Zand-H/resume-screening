# Generated by Django 5.1.4 on 2023-03-05 14:21

import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('flex_blob', '0002_filemodel_uploaded_at'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CVTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('title', models.CharField(max_length=255, unique=True, verbose_name='Title')),
                ('path', models.CharField(max_length=255, unique=True, verbose_name='Path')),
                ('is_active', models.BooleanField(default=True, verbose_name='Is active')),
            ],
            options={
                'verbose_name': 'CV Template',
                'verbose_name_plural': 'CV Templates',
            },
        ),
        migrations.CreateModel(
            name='GeneratedCV',
            fields=[
                ('filemodel_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='flex_blob.filemodel')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cv', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'CV File',
                'verbose_name_plural': 'CV Files',
            },
            bases=('flex_blob.filemodel',),
        ),
    ]
