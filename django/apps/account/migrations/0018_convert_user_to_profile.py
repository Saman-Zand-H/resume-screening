# Generated by Django 5.1.4 on 2023-04-18 15:07

from django.db import migrations


def copy_user_to_profile(apps, schema_editor):
    User = apps.get_model("auth_account", "User")
    Profile = apps.get_model("auth_account", "Profile")
    for user in User.objects.all():
        profile, created = Profile.objects.get_or_create(user=user, defaults={"credits": 0})
        profile.gender = user.gender
        profile.birth_date = user.birth_date
        profile.raw_skills = user.raw_skills
        profile.skills.set(user.skills.all())
        profile.available_jobs.set(user.available_jobs.all())
        profile.save()


class Migration(migrations.Migration):
    dependencies = [
        ("auth_account", "0017_profile_available_jobs_profile_birth_date_and_more"),
    ]

    operations = [
        migrations.RunPython(copy_user_to_profile, migrations.RunPython.noop),
    ]
