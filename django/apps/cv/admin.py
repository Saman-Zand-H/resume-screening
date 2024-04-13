from django.contrib import admin

from .models import CVTemplate


@admin.register(CVTemplate)
class CVTemplateAdmin(admin.ModelAdmin):
    list_display = (CVTemplate.title.field.name, CVTemplate.path.field.name, CVTemplate.is_active.field.name)
    list_filter = (CVTemplate.is_active.field.name,)
    search_fields = (
        CVTemplate.title.field.name,
        CVTemplate.path.field.name,
    )
