from django import forms


class CantoSettingsForm(forms.Form):
    code = forms.CharField(widget=forms.HiddenInput)
    state = forms.CharField(widget=forms.HiddenInput)
