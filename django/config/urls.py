from apps.api.schema import schema
from graphene_django.views import GraphQLView

from django.contrib import admin
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt

# from apps.account.views import sign_in, sign_out, auth_receiver

urlpatterns = [
    path("admin/", admin.site.urls),
    path("graphql", csrf_exempt(GraphQLView.as_view(graphiql=True, schema=schema))),
    path("accounts/", include("allauth.urls")),
    # path("accounts/", include("allauth.socialaccount.urls")),
    # path("accounts/signin", sign_in, name="sign_in"),
    # path("auth-receiver", auth_receiver, name="auth_receiver"),
    # path("accounts/signout", sign_out, name="sign_out"),
]
