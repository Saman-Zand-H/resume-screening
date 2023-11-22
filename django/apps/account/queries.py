import graphene
from graphql_auth.queries import MeQuery
from graphql_jwt.decorators import login_required

from .types import EducationType, UserNode, CertificateAndLicenseType, LanguageCertificateType


class EducationQuery(graphene.ObjectType):
    get = graphene.Field(EducationType, id=graphene.Int())

    @login_required
    def resolve_get(self, info, id):
        return EducationType.get_node(info, id)
    

class LanguageCertificateQuery(graphene.ObjectType):
    get = graphene.List(LanguageCertificateType)

    @login_required
    def resolve_get(self, info):
        return LanguageCertificateType.get_queryset(LanguageCertificateType._meta.model.objects, info)


class CertificateAndLicenseQuery(graphene.ObjectType):
    get = graphene.List(CertificateAndLicenseType)

    @login_required
    def resolve_get(self, info):
        return CertificateAndLicenseType.get_queryset(CertificateAndLicenseType._meta.model.objects, info)



class Query(MeQuery, graphene.ObjectType):
    me = graphene.Field(UserNode)
    education = graphene.Field(EducationQuery)
    language_certificate = graphene.Field(LanguageCertificateQuery)
    certificate_and_license = graphene.Field(CertificateAndLicenseQuery)

    def resolve_education(self, info):
        return EducationQuery()
    
    def resolve_language_certificate(self, info):
        return LanguageCertificateQuery()
    
    def resolve_certificate_and_license(self, info):
        return CertificateAndLicenseQuery()
