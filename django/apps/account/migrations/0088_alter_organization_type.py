# Generated by Django 5.1.5 on 2024-06-29 17:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth_account', '0087_alter_employeeplatformmessage_organization_employee_cooperation_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='organization',
            name='type',
            field=models.CharField(blank=True, choices=[('sole_proprietorship', 'Sole Proprietorship'), ('general_partnership', 'General Partnership'), ('limited_partnership', 'Limited Partnership'), ('private_corporation', 'Private Corporation'), ('public_corporation', 'Public Corporation'), ('cooperative', 'Cooperative'), ('non_profit_organization', 'Non-Profit Organization'), ('branch_office', 'Branch Office'), ('subsidiary', 'Subsidiary')], max_length=50, null=True, verbose_name='Type'),
        ),
    ]
