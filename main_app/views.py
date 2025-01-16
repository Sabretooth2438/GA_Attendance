from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from .forms import UserRegistrationForm, ProfileForm, ClassForm, StudentSearchForm, AttendanceForm
from .models import Profile, Class, Attendance
from django.urls import reverse_lazy

def signup(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = ProfileForm(request.POST, request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.email = user.email
            profile.save()
            login(request, user)
            return redirect('profile') 
    else:
        user_form = UserRegistrationForm()
        profile_form = ProfileForm()
    return render(request, 'registration/signup.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    def get_success_url(self): 
        return reverse_lazy('home')