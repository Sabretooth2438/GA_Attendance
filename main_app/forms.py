from django import forms
from django.contrib.auth.models import User
from .models import Profile, Class, Attendance

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email']

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_img']

class ClassForm(forms.ModelForm): 
    class Meta: 
        model = Class
        fields = ['name', 'description']

class StudentSearchForm(forms.Form):
    username = forms.CharField(label='Student Username', max_length=150)

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['date', 'status']