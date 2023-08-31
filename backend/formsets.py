from django.core.exceptions import ValidationError
from django.forms import BaseModelFormSet, modelformset_factory

from .constants import PITCH_EXTERNAL_LINKS_INITIAL
from .forms import ExternalLinkForm
from .models import ExternalLink


class ExternalLinkBaseFormset(BaseModelFormSet):
    def clean(self, *args, **kwargs):
        super().clean(*args, **kwargs)
        for form in self.forms:
            name = form.cleaned_data.get("name", "").strip()
            url = form.cleaned_data.get("url", "").strip()
            if name and url:
                return
        raise ValidationError("You need to have at least one url specified")


ExternalLinkCreateFormSet = modelformset_factory(
    ExternalLink,
    form=ExternalLinkForm,
    extra=len(PITCH_EXTERNAL_LINKS_INITIAL),
    formset=ExternalLinkBaseFormset,
)

ExternalLinkUpdateFormSet = modelformset_factory(
    ExternalLink,
    form=ExternalLinkForm,
    extra=1,
    formset=ExternalLinkBaseFormset,
)
