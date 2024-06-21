from django.contrib import admin

from .models import VertexAIModel


@admin.register(VertexAIModel)
class VertexAIModelAdmin(admin.ModelAdmin):
    list_display = [
        VertexAIModel.slug.field.name,
        VertexAIModel.model_name.field.name,
        VertexAIModel.temperature.field.name,
        VertexAIModel.max_tokens.field.name,
    ]
    search_fields = [
        VertexAIModel.slug.field.name,
        VertexAIModel.model_name.field.name,
    ]
    list_filter = [
        VertexAIModel.model_name.field.name,
    ]
    fieldsets = [
        (
            None,
            {
                "fields": [VertexAIModel.slug.field.name, VertexAIModel.model_name.field.name],
            },
        ),
        (
            "Configuration",
            {
                "fields": [
                    VertexAIModel.temperature.field.name,
                    VertexAIModel.max_tokens.field.name,
                    VertexAIModel.instruction.field.name,
                ],
            },
        ),
    ]
    ordering = [VertexAIModel.slug.field.name]
