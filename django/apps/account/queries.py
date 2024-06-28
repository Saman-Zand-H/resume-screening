import graphene
from graphql_auth.queries import MeQuery
from graphql_jwt.decorators import login_required

from .types import (
    CertificateAndLicenseNode,
    EducationNode,
    LanguageCertificateNode,
    OrganizationInvitationType,
    UserNode,
    WorkExperienceNode,
)


class OrganizationQuery(graphene.ObjectType):
    invitation = graphene.Field(OrganizationInvitationType, token=graphene.String(required=True))

    @login_required
    def resolve_invitation(self, info, token):
        return OrganizationInvitationType.get_node_by_token(info, token)


class EducationQuery(graphene.ObjectType):
    get = graphene.Field(EducationNode, id=graphene.ID())

    @login_required
    def resolve_get(self, info, id):
        return EducationNode.get_node(info, id)


class WorkExperienceQuery(graphene.ObjectType):
    get = graphene.Field(WorkExperienceNode, id=graphene.ID())

    @login_required
    def resolve_get(self, info, id):
        return WorkExperienceNode.get_node(info, id)


class LanguageCertificateQuery(graphene.ObjectType):
    get = graphene.Field(LanguageCertificateNode, id=graphene.ID())

    @login_required
    def resolve_get(self, info, id):
        return LanguageCertificateNode.get_node(info, id)


class CertificateAndLicenseQuery(graphene.ObjectType):
    get = graphene.Field(CertificateAndLicenseNode, id=graphene.ID())

    @login_required
    def resolve_get(self, info, id):
        return CertificateAndLicenseNode.get_node(info, id)


class Query(MeQuery, graphene.ObjectType):
    me = graphene.Field(UserNode)
    education = graphene.Field(EducationQuery)
    work_experience = graphene.Field(WorkExperienceQuery)
    language_certificate = graphene.Field(LanguageCertificateQuery)
    certificate_and_license = graphene.Field(CertificateAndLicenseQuery)
    organization = graphene.Field(OrganizationQuery)

    def resolve_education(self, info):
        return EducationQuery()

    def resolve_work_experience(self, info):
        return WorkExperienceQuery()

    def resolve_language_certificate(self, info):
        return LanguageCertificateQuery()

    def resolve_certificate_and_license(self, info):
        return CertificateAndLicenseQuery()

    def resolve_organization(self, info):
        return OrganizationQuery()
