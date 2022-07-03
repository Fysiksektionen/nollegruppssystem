import django.contrib.auth.forms as auth_forms
import django.forms as forms

from .models import AuthUser


class FakeCASLoginForm(forms.Form):
    username = auth_forms.UsernameField()

class UserCreationForm(auth_forms.UserCreationForm):
    class Meta(auth_forms.UserCreationForm.Meta):
        model = AuthUser
        fields = ('username', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            user.profile.save()

        return user

