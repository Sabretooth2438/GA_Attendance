from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
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
    
class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')

@login_required
def profile(request):
    return render(request, 'profile.html', {'user': request.user})

@login_required 
def edit_profile(request): 
    profile = get_object_or_404(Profile, user=request.user) 
    if request.method == 'POST': 
        form = ProfileForm(request.POST, request.FILES, instance=profile) 
        if form.is_valid(): 
            form.save() 
            return redirect('profile') 
    else: 
        form = ProfileForm(instance=profile) 
    return render(request, 'edit_profile.html', {'form': form})

def home(request):
    return render(request, 'home.html')

@login_required
def create_class(request):
    if request.user.profile.role != 'Teacher':
        return redirect('home')  # Only teachers can create classes
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            class_ = form.save(commit=False)
            class_.teacher = request.user.profile
            class_.save()
            return redirect('class_detail', pk=class_.pk)
    else:
        form = ClassForm()
    return render(request, 'create_class.html', {'form': form})

@login_required
def class_detail(request, pk):
    class_ = get_object_or_404(Class, pk=pk)
    return render(request, 'class_detail.html', {'class': class_})

@login_required
def manage_classes(request):
    if request.user.profile.role != 'Teacher':
        return redirect('home')
    classes = Class.objects.filter(teacher=request.user.profile)
    return render(request, 'manage_classes.html', {'classes': classes})

@login_required
def add_student(request, pk):
    class_ = get_object_or_404(Class, pk=pk)
    if request.user.profile.role != 'Teacher' or request.user.profile != class_.teacher:
        return redirect('home')  
        
    if request.method == 'POST':
        search_form = StudentSearchForm(request.POST)
        if search_form.is_valid():
            username = search_form.cleaned_data['username']
            try:
                student_profile = Profile.objects.get(user__username=username, role='Student')
                class_.students.add(student_profile)
                return redirect('class_detail', pk=pk)
            except Profile.DoesNotExist:
                search_form.add_error('username', 'Student not found.')
    else:
        search_form = StudentSearchForm()
    
    return render(request, 'add_student.html', {'class': class_, 'search_form': search_form})

@login_required
def search_classes(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        classes = Class.objects.filter(name__icontains=query)
        return render(request, 'search_classes.html', {'classes': classes, 'query': query})
    return render(request, 'search_classes.html')

@login_required
def send_join_request(request, pk):
    class_ = get_object_or_404(Class, pk=pk)
    if request.user.profile.role != 'Student':
        return redirect('home')
    class_.students.add(request.user.profile)
    return redirect('class_detail', pk=pk)
