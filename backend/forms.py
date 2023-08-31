from captcha.fields import CaptchaField
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from tinymce.widgets import TinyMCE

from .constants import TINY_MCE_ATTRS
from .models import (
    Publisher,
    Pitch,
    Platform,
    Service,
    ExternalLink,
)


class UserSignUpForm(UserCreationForm):
    terms_agreed = forms.BooleanField(required=True)
    captcha = CaptchaField()

    def clean_terms_agreed(self):
        terms_agreed = self.cleaned_data["terms_agreed"]
        if not terms_agreed:
            raise ValidationError(
                "You can't proceed futher without accepting out terms!"
            )
        return terms_agreed

    def save(self, commit: bool = True):
        user = super().save(commit=False)
        email = self.cleaned_data["email"]
        user.username = email
        user.is_active = False
        if commit:
            user.save()
        return user

    class Meta:
        model = get_user_model()
        fields = ["email", "first_name", "last_name"]


class UserPasswordResetForm(PasswordResetForm):
    captcha = CaptchaField()


class ExternalLinkForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["url"].required = False

    class Meta:
        model = ExternalLink
        fields = ["name", "url"]


class PitchUpdateForm(forms.ModelForm):
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.all(),
        widget=forms.CheckboxSelectMultiple,
    )
    platforms = forms.ModelMultipleChoiceField(
        queryset=Platform.objects.all(),
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        rich_placeholder = render_to_string("pitches/placeholder.html", {}).strip()
        self.fields["description"].widget = TinyMCE(
            attrs={
                **dict(TINY_MCE_ATTRS),
                "rich_placeholder": rich_placeholder,
                "init_instance_callback": "initEditorInstance",
            }
        )

    class Meta:
        model = Pitch
        fields = ["name", "description", "services", "platforms"]


class PitchCreateForm(PitchUpdateForm):
    captcha = CaptchaField()
    publisher = forms.ModelChoiceField(
        queryset=Publisher.objects.all(),
        required=True,
        empty_label=None,
    )

    def __init__(self, *args, **kwargs):
        self._user = kwargs.pop("user")
        super().__init__(*args, **kwargs)
        publisher = self.initial.get("publisher")
        if publisher:
            self.fields["publisher"].queryset = Publisher.objects.filter(
                pk=publisher.id
            )
            self.fields["services"].queryset = publisher.services.all()
            self.fields["platforms"].queryset = publisher.platforms.all()

    def save(self, commit: bool = True):
        pitch = super().save(commit=False)
        pitch.created_by = self._user
        if commit:
            pitch.save()
            self.save_m2m()
        return pitch
