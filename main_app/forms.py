from django import forms
from django.contrib.auth.models import User
from .models import Profile, Class, Attendance
from django.forms import modelformset_factory

# Form for user registration.
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email is already in use.")
        return email

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']

# Form for profile editing.
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_img']

# Form for class creation and editing.
class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name', 'description', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'date-selector'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'date-selector'}),
        }

# Form for student search by username.
class StudentSearchForm(forms.Form):
    username = forms.CharField(label='Student Username', max_length=150)

# Form for attendance management.
class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'status', 'reason']

AttendanceFormSet = modelformset_factory(
    Attendance, 
    form=AttendanceForm, 
    extra=0
)

class EditClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name', 'description']
