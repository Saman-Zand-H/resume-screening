from apps.api.schema import schema
from graphene_file_upload.django import FileUploadGraphQLView as GraphQLView

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt

from .settings.constants import Environment
from .utils import is_env
from .views import AdminLoginView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("graphql", csrf_exempt(GraphQLView.as_view(graphiql=settings.DEBUG, schema=schema))),
    path("criteria/", include("criteria.urls"), name="criteria"),
    path("academy/", include("academy.urls"), name="academy"),
    path("media/", include("flex_blob.urls"), name="blob"),
]

if not is_env(Environment.LOCAL):
    urlpatterns = [path("admin/login/", AdminLoginView.as_view(), name="admin_login"), *urlpatterns]
