from django.urls import re_path

from . import views

urlspatterns = [
    re_path(
        r"^blob/(?P<path>.*)$",
        views.MediaAuthorizationView.as_view(),
        name="media",
    )
]
