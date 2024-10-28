from import_export.widgets import Widget


class ArrayFieldWidget(Widget):
    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return []
        return [url.strip() for url in value.split(",")]

    def render(self, value, obj=None, **kwargs):
        return ", ".join(value) if value else ""
