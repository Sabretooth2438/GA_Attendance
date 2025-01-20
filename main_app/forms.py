from django import forms
from django.contrib.auth.models import User
from .models import Profile, Class, Attendance

# Handles user registration with password confirmation
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_password2(self):
        data = self.cleaned_data
        if data['password'] != data['password2']:
            raise forms.ValidationError("Passwords don't match.")
        return data['password2']

# Allows users to edit their profile details
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_img']

# Used for creating or editing a class
class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name', 'description', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

# Manages attendance records for students
class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'status', 'reason']

# Allows searching for a student by username
class StudentSearchForm(forms.Form):
    username = forms.CharField(max_length=150, label='Student username')

# Allows teachers to edit class details
class EditClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name', 'description']
