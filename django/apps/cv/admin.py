from django.contrib import admin

from .models import CVTemplate, GeneratedCV, GeneratedCVContent


@admin.register(CVTemplate)
class CVTemplateAdmin(admin.ModelAdmin):
    list_display = (CVTemplate.title.field.name, CVTemplate.path.field.name, CVTemplate.is_active.field.name)
    list_filter = (CVTemplate.is_active.field.name,)
    search_fields = (
        CVTemplate.title.field.name,
        CVTemplate.path.field.name,
    )


@admin.register(GeneratedCVContent)
class GeneratedCVContentAdmin(admin.ModelAdmin):
    list_display = (GeneratedCVContent.user.field.name,)
    search_fields = (GeneratedCVContent.user.field.name,)


@admin.register(GeneratedCV)
class GeneratedCVAdmin(admin.ModelAdmin):
    list_display = (GeneratedCV.user.field.name, GeneratedCV.file.field.name)
    search_fields = (
        GeneratedCV.user.field.name,
        GeneratedCV.file.field.name,
    )
