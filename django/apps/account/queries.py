import graphene
from graphql_auth.queries import MeQuery
from graphql_jwt.decorators import login_required
from graphene_django_cud.util.model import disambiguate_id


from .types import (
    CertificateAndLicenseNode,
    EducationNode,
    LanguageCertificateNode,
    UserNode,
    WorkExperienceNode,
)


class EducationQuery(graphene.ObjectType):
    get = graphene.Field(EducationNode, id=graphene.ID())

    @login_required
    def resolve_get(self, info, id):
        return EducationNode.get_node(info, disambiguate_id(id))


class WorkExperienceQuery(graphene.ObjectType):
    get = graphene.Field(WorkExperienceNode, id=graphene.ID())

    @login_required
    def resolve_get(self, info, id):
        return WorkExperienceNode.get_node(info, disambiguate_id(id))


class LanguageCertificateQuery(graphene.ObjectType):
    get = graphene.Field(LanguageCertificateNode, id=graphene.ID())

    @login_required
    def resolve_get(self, info, id):
        return LanguageCertificateNode.get_node(info, disambiguate_id(id))


class CertificateAndLicenseQuery(graphene.ObjectType):
    get = graphene.Field(CertificateAndLicenseNode, id=graphene.ID())

    @login_required
    def resolve_get(self, info, id):
        return CertificateAndLicenseNode.get_node(info, disambiguate_id(id))


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
