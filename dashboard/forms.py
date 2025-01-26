from django import forms
from .models import Patient

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['user', 'name', 'UID', 'email', 'address', 'picture', 'phone']
