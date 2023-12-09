import graphene
from graphql_auth.queries import MeQuery
from graphql_jwt.decorators import login_required
from graphene_django_cud.util.model import disambiguate_id


from .types import (
    CertificateAndLicenseType,
    EducationType,
    LanguageCertificateType,
    UserNode,
    WorkExperienceType,
)


class EducationQuery(graphene.ObjectType):
    get = graphene.Field(EducationType, id=graphene.ID())

    @login_required
    def resolve_get(self, info, id):
        return EducationType.get_node(info, disambiguate_id(id))


class WorkExperienceQuery(graphene.ObjectType):
    get = graphene.Field(WorkExperienceType, id=graphene.ID())

    @login_required
    def resolve_get(self, info, id):
        return WorkExperienceType.get_node(info, disambiguate_id(id))


class LanguageCertificateQuery(graphene.ObjectType):
    get = graphene.Field(LanguageCertificateType, id=graphene.ID())

    @login_required
    def resolve_get(self, info, id):
        return LanguageCertificateType.get_node(info, disambiguate_id(id))


class CertificateAndLicenseQuery(graphene.ObjectType):
    get = graphene.Field(CertificateAndLicenseType, id=graphene.ID())

    @login_required
    def resolve_get(self, info, id):
        return CertificateAndLicenseType.get_node(info, disambiguate_id(id))


class Query(MeQuery, graphene.ObjectType):
    me = graphene.Field(UserNode)
    education = graphene.Field(EducationQuery)
    work_experience = graphene.Field(WorkExperienceQuery)
    language_certificate = graphene.Field(LanguageCertificateQuery)
    certificate_and_license = graphene.Field(CertificateAndLicenseQuery)

    def resolve_education(self, info):
        return EducationQuery()

    def resolve_work_experience(self, info):
        return WorkExperienceQuery()

    def resolve_language_certificate(self, info):
        return LanguageCertificateQuery()

    def resolve_certificate_and_license(self, info):
        return CertificateAndLicenseQuery()
