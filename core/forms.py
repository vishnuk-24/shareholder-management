from django import forms

from .models import Country


COUNTRIES = (
    ('IND', 'India'),
    ('USA', 'United States'),
    # Add other countries...
)

class ShareholderForm(forms.ModelForm):
    country = forms.ChoiceField(choices=COUNTRIES)

    class Meta:
        model = Country
        fields = '__all__'
