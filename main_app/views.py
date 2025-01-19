from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from .forms import UserRegistrationForm, ProfileForm, ClassForm, StudentSearchForm, AttendanceForm, EditClassForm, AttendanceFormSet
from .models import Profile, Class, Attendance, JoinRequest
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages 
import logging
from django.forms import modelformset_factory


logger = logging.getLogger(__name__)

# Handle user registration.
def signup(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            user.email = user_form.cleaned_data['email']
            user.set_password(user_form.cleaned_data['password'])
            user.save()
            login(request, user)
            Profile.objects.create(user=user)  # Create an empty profile
            return redirect('edit_profile')  # Redirect to profile editing
            # return redirect('profile') 
    else:
        user_form = UserRegistrationForm()
    return render(request, 'registration/signup.html', {'user_form': user_form})

# Custom login view.
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    def get_success_url(self): 
        return reverse_lazy('home')

# Custom logout view.
class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')

# Display user profile.
@login_required
def profile(request):
    return render(request, 'profile.html', {'user': request.user})

# Edit user profile.
@login_required 
def edit_profile(request): 
    profile = get_object_or_404(Profile, user=request.user) 
    if request.method == 'POST': 
        form = ProfileForm(request.POST, request.FILES, instance=profile) 
        if form.is_valid(): 
            form.save() 
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('profile') 
    else: 
        form = ProfileForm(instance=profile) 

    completion_percentage = profile.completion_percentage()
    return render(request, 'edit_profile.html', {'form': form, 'completion_percentage': completion_percentage})

# Render homepage.
def home(request):
    return render(request, 'home.html')

# Create a new class (teacher only).
@login_required
def create_class(request):
    if request.user.profile.role != 'Teacher':
        return redirect('home')

    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            class_instance = form.save(commit=False)
            class_instance.teacher = request.user.profile
            class_instance.save()
            return redirect('class_detail', pk=class_instance.pk)
    else:
        form = ClassForm()

    return render(request, 'create_class.html', {'form': form})


# Display class details.
@login_required
def class_detail(request, pk):
    class_instance = get_object_or_404(Class, pk=pk)
    students = class_instance.students.all()
    date = timezone.now().date()

    if request.user.profile.role == 'Teacher':
        AttendanceFormSet = modelformset_factory(
            Attendance,
            fields=['student', 'status', 'reason'],
            extra=len(students)
        )

        if request.method == 'POST':
            formset = AttendanceFormSet(request.POST)
            if formset.is_valid():
                instances = formset.save(commit=False)
                for instance, student in zip(instances, students):
                    instance.student = student
                    instance.classid = class_instance
                    instance.date = date
                    instance.save()
                messages.success(request, "Attendance has been marked for all students.")
                return redirect('class_detail', pk=pk)
        else:
            formset = AttendanceFormSet(queryset=Attendance.objects.none())
            # Pre-fill student field
            for form, student in zip(formset.forms, students):
                form.initial['student'] = student.pk

        # **Zip the formset and students here**:
        zipped_data = zip(formset.forms, students)

        return render(request, 'class_detail.html', {
            'class': class_instance,
            'formset': formset,       # If you still need formset in template
            'students': students,     # If needed for other logic
            'zipped_data': zipped_data,  # Pass zipped data to the template
            'date': date
        })

    # Otherwise, student or non-teacher logic
    return render(request, 'class_detail.html', {
        'class': class_instance,
        'students': students,
        'date': date
    })

# Manage classes (teacher only).
@login_required
def manage_classes(request):
    if request.user.profile.role != 'Teacher':
        return redirect('home')
    classes = Class.objects.filter(teacher=request.user.profile)
    return render(request, 'manage_classes.html', {'classes': classes})

# Add a student to a class (teacher only).
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

# Search for classes.
@login_required
def search_classes(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        classes = Class.objects.filter(name__icontains=query)
        return render(request, 'search_classes.html', {'classes': classes, 'query': query})
    return render(request, 'search_classes.html')

# Send a join request to a class (student only).
@login_required
def send_join_request(request, pk):
    class_ = get_object_or_404(Class, pk=pk)
    if request.user.profile.role != 'Student':
        return redirect('home')
    class_.students.add(request.user.profile)
    return redirect('class_detail', pk=pk)

# View all classes a user is enrolled in.
@login_required
def view_classes(request):
    classes = request.user.profile.classes.all()
    return render(request, 'view_classes.html', {'classes': classes})

# Leave a class (student only).
@login_required
def leave_class(request, pk):
    class_ = get_object_or_404(Class, pk=pk)
    if request.user.profile.role != 'Student':
        return redirect('home')
    class_.students.remove(request.user.profile)
    return redirect('view_classes')

# Remove a student from a class (teacher only).
@login_required
def remove_student(request, class_pk, student_pk):
    class_ = get_object_or_404(Class, pk=class_pk)
    student_profile = get_object_or_404(Profile, pk=student_pk)
    if request.user.profile.role != 'Teacher' or request.user.profile != class_.teacher:
        return redirect('home')
    class_.students.remove(student_profile)
    return redirect('class_detail', pk=class_pk)


@login_required
def mark_attendance_inline(request, class_pk, student_pk):
    class_instance = get_object_or_404(Class, pk=class_pk)
    student_profile = get_object_or_404(Profile, pk=student_pk)

    if request.user.profile.role != 'Teacher' or request.user.profile != class_instance.teacher:
        return redirect('home')

    current_date = timezone.now().date()

    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.classid = class_instance
            attendance.student = student_profile
            attendance.date = current_date
            attendance.save()
            return redirect('class_detail', pk=class_pk)
    else:
        form = AttendanceForm()

    return render(request, 'class_detail.html', {'class': class_instance, 'form': form, 'student_profile': student_profile})

# Display all attendance records.
@login_required
def attendance_records(request):
    records = Attendance.objects.all()
    return render(request, 'attendance_records.html', {'records': records})

# Display profile details and attendance summary.
@login_required
def profile_detail(request, pk, class_pk=None):
    profile = get_object_or_404(Profile, pk=pk)
    classes = profile.classes.all()
    attendance_summary = {}
    attendance_records = None
    absence_percentage = None

    # If a class_pk is provided, filter attendance records for that class
    if class_pk:
        class_instance = get_object_or_404(Class, pk=class_pk)
        # Ensure the requesting user is the teacher of the class
        if request.user.profile.role != 'Teacher' or request.user.profile != class_instance.teacher:
            return redirect('home')
        
        attendance_records = Attendance.objects.filter(student=profile, classid=class_instance).order_by('date')
        total_classes = attendance_records.count()
        absences = attendance_records.filter(status='A').count()
        absence_percentage = (absences / total_classes) * 100 if total_classes > 0 else 0
    else:
        # Calculate attendance summary for all classes (existing functionality)
        for class_ in classes:
            records = Attendance.objects.filter(student=profile, classid=class_)
            total = records.count()
            present = records.filter(status='P').count()
            percentage = (present / total) * 100 if total > 0 else 0
            attendance_summary[class_] = percentage

    return render(request, 'profile_detail.html', {
        'profile': profile,
        'classes': classes,
        'attendance_summary': attendance_summary,
        'attendance_records': attendance_records,
        'absence_percentage': absence_percentage,
    })


# Delete a class (teacher only).
@login_required
def delete_class(request, class_id):
    class_instance = get_object_or_404(Class, pk=class_id)
    if request.user.profile == class_instance.teacher:
        if request.method == 'POST':
            class_instance.delete()
            return redirect('manage_classes')
    else:
        return redirect('home')
    return render(request, 'delete_class.html', {'class': class_instance})

@login_required
def edit_class(request, class_id):
    class_instance = get_object_or_404(Class, pk=class_id)

    if request.user.profile != class_instance.teacher:
        return redirect('home')

    if request.method == 'POST':
        form = ClassForm(request.POST, instance=class_instance)
        if form.is_valid():
            form.save()
            return redirect('class_detail', pk=class_id)
    else:
        form = ClassForm(instance=class_instance)

    return render(request, 'edit_class.html', {'form': form, 'class': class_instance})


@login_required
def student_attendance_records(request):
    if request.user.profile.role != 'Student':
        return redirect('home')

    attendance_records = Attendance.objects.filter(student=request.user.profile).order_by('date')
    total_classes = attendance_records.count()
    absences = attendance_records.filter(status='A').count()

    # Calculate absence percentage
    absence_percentage = (absences / total_classes) * 100 if total_classes > 0 else 0
    warning = absence_percentage > 25  # Warn if absence exceeds 25%

    return render(request, 'attendance_records.html', {
        'records': attendance_records,
        'absence_percentage': absence_percentage,
        'warning': warning,
    })

@login_required
def send_join_request(request, pk):
    class_instance = get_object_or_404(Class, pk=pk)
    if request.user.profile.role != 'Student':
        return redirect('home')

    existing_request = JoinRequest.objects.filter(student=request.user.profile, classid=class_instance).first()
    if not existing_request:
        JoinRequest.objects.create(student=request.user.profile, classid=class_instance)
        messages.success(request, "Your join request has been sent.")
    else:
        messages.info(request, "You have already sent a join request for this class.")

    return redirect('class_detail', pk=pk)

@login_required
def manage_join_requests(request, pk):
    class_instance = get_object_or_404(Class, pk=pk)
    if request.user.profile != class_instance.teacher:
        return redirect('home')

    join_requests = JoinRequest.objects.filter(classid=class_instance, status='Pending')

    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')
        join_request = get_object_or_404(JoinRequest, id=request_id)

        if action == 'approve':
            join_request.status = 'Approved'
            join_request.save()
            class_instance.students.add(join_request.student)
            messages.success(request, f"{join_request.student.user.username} has been approved.")
        elif action == 'reject':
            join_request.status = 'Rejected'
            join_request.save()
            messages.info(request, f"{join_request.student.user.username}'s request has been rejected.")

    return render(request, 'manage_join_requests.html', {'class': class_instance, 'join_requests': join_requests})

@login_required
def edit_attendance(request, class_pk, student_pk):
    class_instance = get_object_or_404(Class, pk=class_pk)
    student_profile = get_object_or_404(Profile, pk=student_pk)

    # Ensure the requesting user is the teacher of the class
    if request.user.profile.role != 'Teacher' or request.user.profile != class_instance.teacher:
        return redirect('home')

    # Fetch all attendance records for the student in the class
    attendance_records = Attendance.objects.filter(student=student_profile, classid=class_instance).order_by('date')

    # Use a modelformset for inline editing
    AttendanceFormSet = modelformset_factory(
        Attendance,
        fields=['date', 'status', 'reason'],
        extra=0
    )

    if request.method == 'POST':
        formset = AttendanceFormSet(request.POST, queryset=attendance_records)
        if formset.is_valid():
            formset.save()  # Save all changes
            messages.success(request, "Attendance records have been updated.")
            return redirect('student_profile', class_pk=class_pk, pk=student_pk)
    else:
        formset = AttendanceFormSet(queryset=attendance_records)

    return render(request, 'edit_attendance.html', {
        'class_instance': class_instance,
        'student_profile': student_profile,
        'formset': formset,
    })
