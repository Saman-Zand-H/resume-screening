# Generated by Django 5.1.4 on 2023-08-19 15:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_account', '0038_roleaccess_alter_role_accesses'),
    ]

    operations = [
        migrations.CreateModel(
            name='RoleAccess',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth_account.access', to_field='slug', verbose_name='Access')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth_account.role', to_field='slug', verbose_name='Role')),
            ],
            options={
                'verbose_name': 'Role Access',
                'verbose_name_plural': 'Role Accesses',
                'unique_together': {('role', 'access')},
            },
        ),
        migrations.AddField(
            model_name='role',
            name='accesses',
            field=models.ManyToManyField(blank=True, through='auth_account.RoleAccess', to='auth_account.access', verbose_name='Accesses'),
        ),
    ]
