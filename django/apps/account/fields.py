from django.contrib.auth.forms import UsernameField as UsernameFieldBase


class UsernameField(UsernameFieldBase):
    def to_python(self, value):
        return super(UsernameFieldBase, self).to_python(value or "")
