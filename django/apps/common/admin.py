from django.contrib import admin

from .models import Field, Job, JobCategory, JobIndustry, University, Skill


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title",)


@admin.register(JobIndustry)
class JobIndustryAdmin(admin.ModelAdmin):
    list_display = ("title",)
    search_fields = ("title",)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "industry")
    search_fields = ("title", "category__title", "industry__title")
    list_filter = ("category", "industry")


@admin.register(Field)
class FieldAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    list_filter = ("name",)


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "website")
    search_fields = ("name", "city__name", "website")
    list_filter = ("name",)
    raw_id_fields = ("city",)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("id", "title",)
    search_fields = ("title",)
    list_filter = ("title",)