from django.contrib import admin

from .models import Field, Job, JobCategory, JobIndustry


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
