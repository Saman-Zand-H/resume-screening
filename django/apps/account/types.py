import graphene
from query_optimizer import DjangoObjectType

from .models import CommunicationMethod, Contact, Education, IEEMethod, Profile, LanguageCertificate


class ProfileType(DjangoObjectType):
    class Meta:
        model = Profile
        fields = (
            Profile.height.field.name,
            Profile.weight.field.name,
            Profile.skin_color.field.name,
            Profile.hair_color.field.name,
            Profile.eye_color.field.name,
            Profile.full_body_image.field.name,
            Profile.employment_status.field.name,
            Profile.interested_jobs.field.name,
            Profile.city.field.name,
        )


class ContactType(DjangoObjectType):
    class Meta:
        model = Contact
        fields = (
            Contact.id.field.name,
            Contact.type.field.name,
            Contact.value.field.name,
        )


class EducationMethodFieldTypes(graphene.ObjectType):
    method = graphene.String()
    field = graphene.String()


class EducationType(DjangoObjectType):
    method_fields = graphene.List(EducationMethodFieldTypes)

    class Meta:
        model = Education
        fields = (
            Education.id.field.name,
            Education.field.field.name,
            Education.degree.field.name,
            Education.university.field.name,
            Education.start.field.name,
            Education.end.field.name,
            Education.status.field.name,
            Education.created_at.field.name,
            Education.updated_at.field.name,
            IEEMethod.get_related_name(),
            CommunicationMethod.get_related_name(),
        )

    def resolve_method_fields(self, info):
        return [
            EducationMethodFieldTypes(method=method, field=model.get_related_name() if model else None)
            for method, model in self.get_method_choices().items()
        ]


class IEEMethodType(DjangoObjectType):
    class Meta:
        model = IEEMethod
        fields = (
            IEEMethod.id.field.name,
            IEEMethod.ices_document.field.name,
            IEEMethod.citizen_document.field.name,
            IEEMethod.evaluator.field.name,
        )


class CommunicationMethodType(DjangoObjectType):
    class Meta:
        model = CommunicationMethod
        fields = (
            CommunicationMethod.id.field.name,
            CommunicationMethod.email.field.name,
            CommunicationMethod.department.field.name,
            CommunicationMethod.person.field.name,
            CommunicationMethod.degree_file.field.name,
        )


class LanguageCertificateType(DjangoObjectType):
    class Meta:
        model = LanguageCertificate
        fields = (
            LanguageCertificate.id.field.name,
            LanguageCertificate.language.field.name,
            LanguageCertificate.test.field.name,
            LanguageCertificate.issued_at.field.name,
            LanguageCertificate.expired_at.field.name,
            LanguageCertificate.listening_score.field.name,
            LanguageCertificate.reading_score.field.name,
            LanguageCertificate.writing_score.field.name,
            LanguageCertificate.speaking_score.field.name,
            LanguageCertificate.band_score.field.name,
        )
