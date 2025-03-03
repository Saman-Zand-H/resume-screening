# Generated by Django 5.1.4 on 2024-06-11 14:37

from common.utils import merge_relations
from django.db import migrations
from django.db.models import Count


def list_duplicate_skill_titles(apps, schema_editor):
    Skill = apps.get_model("common", "Skill")
    duplicates = Skill.objects.values("title").annotate(title_count=Count("title")).filter(title_count__gt=1)

    if duplicates.exists():
        for entry in duplicates:
            skills = Skill.objects.filter(title=entry["title"])
            source = skills.first()
            targets = skills.exclude(pk=source.pk)
            merge_relations(source, *targets)
            targets.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0013_remove_job_industry"),
    ]

    operations = [
        migrations.RunPython(list_duplicate_skill_titles, reverse_code=migrations.RunPython.noop),
    ]
