from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
import re
from core.models import CustomUser

class ClientProfileForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email','profile_image']

class ClientPasswordChangeForm(PasswordChangeForm):
    new_password1 = forms.CharField(
        label="New password",
        widget=forms.PasswordInput,
        strip=False,
    )
    new_password2 = forms.CharField(
        label="Confirm new password",
        widget=forms.PasswordInput,
        strip=False,
    )

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at least one number.")
        if not re.search(r'[\W_]', password):
            raise ValidationError("Password must contain at least one special character.")
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("new_password1")
        password2 = cleaned_data.get("new_password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("The two password fields didn't match.")

class NotificationPreferencesForm(forms.Form):
    email_notifications = forms.BooleanField(required=False)
    sms_notifications = forms.BooleanField(required=False)
