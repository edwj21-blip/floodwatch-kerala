from django import forms
from .models import FloodReport

DISTRICT_CHOICES = [
    ('', 'Select District'),
    ('Thiruvananthapuram', 'Thiruvananthapuram'),
    ('Kollam', 'Kollam'),
    ('Pathanamthitta', 'Pathanamthitta'),
    ('Alappuzha', 'Alappuzha'),
    ('Kottayam', 'Kottayam'),
    ('Idukki', 'Idukki'),
    ('Ernakulam', 'Ernakulam'),
    ('Thrissur', 'Thrissur'),
    ('Palakkad', 'Palakkad'),
    ('Malappuram', 'Malappuram'),
    ('Kozhikode', 'Kozhikode'),
    ('Wayanad', 'Wayanad'),
    ('Kannur', 'Kannur'),
    ('Kasaragod', 'Kasaragod'),
]


class FloodReportForm(forms.ModelForm):
    district = forms.ChoiceField(choices=DISTRICT_CHOICES)

    class Meta:
        model = FloodReport
        fields = [
            'reporter_name', 'reporter_phone', 'reporter_email',
            'location', 'district', 'description',
            'water_level_estimate', 'severity',
            'people_affected', 'evacuation_needed',
            'photo', 'latitude', 'longitude',
        ]
        widgets = {
            'reporter_name': forms.TextInput(attrs={'placeholder': 'Your full name', 'class': 'form-input'}),
            'reporter_phone': forms.TextInput(attrs={'placeholder': '+91 XXXXX XXXXX', 'class': 'form-input'}),
            'reporter_email': forms.EmailInput(attrs={'placeholder': 'your@email.com (optional)', 'class': 'form-input'}),
            'location': forms.TextInput(attrs={'placeholder': 'Street, landmark, area name', 'class': 'form-input'}),
            'district': forms.Select(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe the flood situation in detail...', 'class': 'form-input'}),
            'water_level_estimate': forms.TextInput(attrs={'placeholder': 'e.g. knee-deep, 2 feet, waist-high', 'class': 'form-input'}),
            'severity': forms.Select(attrs={'class': 'form-input'}),
            'people_affected': forms.NumberInput(attrs={'placeholder': '0', 'class': 'form-input', 'min': 0}),
            'evacuation_needed': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'photo': forms.FileInput(attrs={'class': 'form-file', 'accept': 'image/*'}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

    def clean_reporter_phone(self):
        phone = self.cleaned_data.get('reporter_phone', '')
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) < 10:
            raise forms.ValidationError('Please enter a valid phone number.')
        return phone


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-input'}))
