from django import forms
from django.forms import ModelForm

from .models import User, Profile, Contact, Education, WorkExperience, LanguageCertificate, CertificateAndLicense


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = [User.gender.field.name, User.birth_date.field.name, User.skills.field.name]


class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = [
            Profile.user.field.name,
            Profile.height.field.name,
            Profile.weight.field.name,
            Profile.skin_color.field.name,
            Profile.hair_color.field.name,
            Profile.eye_color.field.name,
            Profile.full_body_image.field.name,
            Profile.employment_status.field.name,
            Profile.interested_jobs.field.name,
            Profile.city.field.name,
        ]


class ContactForm(ModelForm):
    class Meta:
        model = Contact
        fields = [
            Contact.type.field.name,
            Contact.value.field.name,
        ]


class BaseDocumentForm(ModelForm):
    # TODO: Make status not required in Meta class
    status = forms.CharField(required=False)

    class Meta:
        abstract = True

    @classmethod
    def get_field_names(cls, model):
        return [field.name for field in model._meta.fields if field.editable]


class EducationForm(BaseDocumentForm):
    class Meta:
        model = Education
        # TODO:add fields base on model in Meta class of super calss
        fields = BaseDocumentForm.get_field_names(Education)


class WorkExperienceForm(BaseDocumentForm):
    class Meta:
        model = WorkExperience
        fields = BaseDocumentForm.get_field_names(WorkExperience)


class LanguageCertificateForm(BaseDocumentForm):
    class Meta:
        model = LanguageCertificate
        fields = BaseDocumentForm.get_field_names(LanguageCertificate)


class CertificateAndLicenseForm(BaseDocumentForm):
    class Meta:
        model = CertificateAndLicense
        fields = BaseDocumentForm.get_field_names(CertificateAndLicense)


class ResumeForm:
    def __init__(self, data=None):
        self.data = data or {}
        self.errors = {}

    def validate(self):
        form_classes = {
            "user": UserForm,
            "profile": ProfileForm,
            "contact": ContactForm,
            "education": EducationForm,
            "work_experience": WorkExperienceForm,
            "language_certificate": LanguageCertificateForm,
            "certificate_and_license": CertificateAndLicenseForm,
        }

        for form_name, form_class in form_classes.items():
            form_data = self.data.get(form_name, [] if form_name == "contact" else {})
            if form_name == "contact":
                for data in form_data:
                    f = form_class(data=data)
                    if not f.is_valid():
                        self.errors[form_name] = f.errors.get_json_data(escape_html=True)
            else:
                f = form_class(data=form_data)
                if not f.is_valid():
                    self.errors[form_name] = f.errors.get_json_data(escape_html=True)

    def get_errors(self):
        return self.errors