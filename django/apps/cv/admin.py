from django.contrib import admin

from .models import CVRequiredContext, CVTemplate


@admin.register(CVRequiredContext)
class CVContextAdmin(admin.ModelAdmin):
    list_display = ('title', 'value')
    search_fields = ('title', 'value')


@admin.register(CVTemplate)
class CVTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'path', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'path')
