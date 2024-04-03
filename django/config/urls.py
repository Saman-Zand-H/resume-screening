from apps.api.schema import schema
from graphene_file_upload.django import FileUploadGraphQLView as GraphQLView

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.decorators.csrf import csrf_exempt
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("graphql", csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))),
    path("criteria/", include("criteria.urls"), name="criteria"),
    path("media/", include("blob.urls"), name="blob"),
]
