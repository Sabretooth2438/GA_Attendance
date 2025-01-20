from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.forms import modelformset_factory
import logging

from .models import Profile, Class, Attendance, JoinRequest
from .forms import (
    UserRegistrationForm, ProfileForm, ClassForm,
    StudentSearchForm, AttendanceForm, EditClassForm
)

logger = logging.getLogger(__name__)

#################
#   AUTH VIEWS  #
#################

def signup(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            user.email = user_form.cleaned_data['email']
            user.set_password(user_form.cleaned_data['password'])
            user.save()
            login(request, user)
            # Profile auto-created by signal if not existing
            return redirect('edit_profile')
    else:
        user_form = UserRegistrationForm()
    return render(request, 'registration/signup.html', {'user_form': user_form})


class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    def get_success_url(self):
        return reverse_lazy('home')


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')

########################
#   PROFILE / HOME     #
########################

@login_required
def profile(request):
    # Just show the logged-in user's data
    return render(request, 'profile.html', {'user': request.user})

@login_required
def edit_profile(request):
    # Access Profile via request.user.profile
    profile = get_object_or_404(Profile, user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated!")
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

    completion_percentage = profile.completion_percentage()  # If you have that method
    return render(request, 'edit_profile.html', {
        'form': form,
        'completion_percentage': completion_percentage
    })

def home(request):
    return render(request, 'home.html')

#####################
#   CLASS VIEWS     #
#####################

@login_required
def create_class(request):
    # Ensure they're a teacher
    if request.user.profile.role != 'Teacher':
        return redirect('home')

    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            class_instance = form.save(commit=False)
            class_instance.teacher = request.user  # store the User as the teacher
            class_instance.save()
            return redirect('class_detail', pk=class_instance.pk)
    else:
        form = ClassForm()
    return render(request, 'create_class.html', {'form': form})


@login_required
def class_detail(request, pk):
    class_instance = get_object_or_404(Class, pk=pk)
    students = class_instance.students.all()
    today = timezone.now().date()

    if request.user.profile.role == 'Teacher' and request.user == class_instance.teacher:
        # Define a formset for Attendance
        AttendanceFormSet = modelformset_factory(
            Attendance,
            fields=['student', 'status', 'reason'],
            extra=0  # No extra empty forms
        )

        if request.method == 'POST':
            formset = AttendanceFormSet(request.POST)
            if formset.is_valid():
                attendance_objects = formset.save(commit=False)
                for attendance_obj in attendance_objects:
                    attendance_obj.classid = class_instance
                    attendance_obj.date = today
                    attendance_obj.save()
                messages.success(request, "Attendance marked for all students!")
                return redirect('class_detail', pk=pk)
        else:
            # Pre-fill the formset with today's attendance records or create new ones
            attendance_qs = Attendance.objects.filter(classid=class_instance, date=today)
            if not attendance_qs.exists():
                # Create initial attendance objects for the formset
                initial_data = [{'student': student.pk} for student in students]
                formset = AttendanceFormSet(queryset=Attendance.objects.none(), initial=initial_data)
            else:
                formset = AttendanceFormSet(queryset=attendance_qs)

        zipped_data = zip(formset.forms, students)

        return render(request, 'class_detail.html', {
            'class': class_instance,
            'formset': formset,
            'zipped_data': zipped_data,
            'students': students,
            'date': today
        })

    return render(request, 'class_detail.html', {
        'class': class_instance,
        'students': students,
        'date': today
    })

@login_required
def manage_classes(request):
    # Only teachers can see "manage classes"
    if request.user.profile.role != 'Teacher':
        return redirect('home')
    # Show all classes this teacher owns
    classes = Class.objects.filter(teacher=request.user)
    return render(request, 'manage_classes.html', {'classes': classes})


@login_required
def edit_class(request, class_id):
    class_instance = get_object_or_404(Class, pk=class_id)

    # Confirm user is that class's teacher
    if request.user.profile.role != 'Teacher' or request.user != class_instance.teacher:
        return redirect('home')

    if request.method == 'POST':
        form = ClassForm(request.POST, instance=class_instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Class updated!")
            return redirect('class_detail', pk=class_id)
    else:
        form = ClassForm(instance=class_instance)
    return render(request, 'edit_class.html', {'form': form, 'class': class_instance})


@login_required
def delete_class(request, class_id):
    class_instance = get_object_or_404(Class, pk=class_id)
    if request.user.profile.role != 'Teacher' or request.user != class_instance.teacher:
        return redirect('home')

    if request.method == 'POST':
        class_instance.delete()
        messages.success(request, "Class deleted.")
        return redirect('manage_classes')

    return render(request, 'delete_class.html', {'class': class_instance})

###############################
#   ADD / REMOVE STUDENTS     #
###############################

@login_required
def add_student(request, pk):
    """Teacher can enroll a student into their class by username."""
    class_instance = get_object_or_404(Class, pk=pk)

    # Check teacher
    if request.user.profile.role != 'Teacher' or request.user != class_instance.teacher:
        return redirect('home')

    if request.method == 'POST':
        search_form = StudentSearchForm(request.POST)
        if search_form.is_valid():
            username = search_form.cleaned_data['username']
            try:
                # We want a User whose profile.role == 'Student'
                student_user = User.objects.get(username=username)
                if student_user.profile.role == 'Student':
                    # Enroll them
                    class_instance.students.add(student_user)
                    messages.success(request, f"Added {username} to the class.")
                    return redirect('class_detail', pk=pk)
                else:
                    search_form.add_error('username', 'This user is not a Student.')
            except User.DoesNotExist:
                search_form.add_error('username', 'User not found.')
    else:
        search_form = StudentSearchForm()

    return render(request, 'add_student.html', {
        'class': class_instance,
        'search_form': search_form
    })


@login_required
def remove_student(request, class_pk, student_pk):
    class_instance = get_object_or_404(Class, pk=class_pk)
    if request.user.profile.role != 'Teacher' or request.user != class_instance.teacher:
        return redirect('home')

    # We assume student_pk is actually the ID of the *User*
    student_user = get_object_or_404(User, pk=student_pk)
    class_instance.students.remove(student_user)
    messages.info(request, f"Removed {student_user.username} from {class_instance.name}.")
    return redirect('class_detail', pk=class_pk)

#################################
#   JOIN / LEAVE CLASS (STUDENT) #
#################################

@login_required
def view_classes(request):
    """Show all classes the current user is enrolled in."""
    # Because 'students' is M2M to User
    enrolled = request.user.enrolled_classes.all()
    return render(request, 'view_classes.html', {'classes': enrolled})


@login_required
def leave_class(request, pk):
    class_instance = get_object_or_404(Class, pk=pk)
    # Only a student can leave
    if request.user.profile.role != 'Student':
        return redirect('home')
    # Remove this user from class
    class_instance.students.remove(request.user)
    messages.info(request, f"You left {class_instance.name}.")
    return redirect('view_classes')


@login_required
def send_join_request(request, pk):
    """Student requests to join a class, leading to teacher approval."""
    class_instance = get_object_or_404(Class, pk=pk)
    if request.user.profile.role != 'Student':
        return redirect('home')

    existing = JoinRequest.objects.filter(student=request.user, classid=class_instance).first()
    if not existing:
        JoinRequest.objects.create(student=request.user, classid=class_instance)
        messages.success(request, "Join request sent.")
    else:
        messages.info(request, "You already have a pending or decided request.")
    return redirect('class_detail', pk=pk)

@login_required
def manage_join_requests(request, pk):
    """Teacher can see pending join requests and approve or reject them."""
    class_instance = get_object_or_404(Class, pk=pk)
    if request.user.profile.role != 'Teacher' or request.user != class_instance.teacher:
        return redirect('home')

    join_requests = JoinRequest.objects.filter(classid=class_instance, status='Pending')
    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        action = request.POST.get('action')
        jr = get_object_or_404(JoinRequest, pk=req_id)
        if action == 'approve':
            jr.status = 'Approved'
            jr.save()
            # Add the user to the class
            class_instance.students.add(jr.student)
            messages.success(request, f"Approved {jr.student.username}.")
        elif action == 'reject':
            jr.status = 'Rejected'
            jr.save()
            messages.info(request, f"Rejected {jr.student.username}.")
    return render(request, 'manage_join_requests.html', {
        'class': class_instance,
        'join_requests': join_requests
    })

######################
#   ATTENDANCE       #
######################

@login_required
def mark_attendance_inline(request, class_pk, student_pk):
    """One-off attendance marking for a single student (teacher only)."""
    class_instance = get_object_or_404(Class, pk=class_pk)
    if request.user.profile.role != 'Teacher' or request.user != class_instance.teacher:
        return redirect('home')

    student_user = get_object_or_404(User, pk=student_pk)

    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.classid = class_instance
            attendance.student = student_user
            attendance.date = timezone.now().date()
            attendance.save()
            messages.success(request, "Attendance marked.")
            return redirect('class_detail', pk=class_pk)
    else:
        form = AttendanceForm()
    return render(request, 'class_detail.html', {
        'class': class_instance,
        'form': form,
        'student_user': student_user
    })


@login_required
def attendance_records(request):
    """Teacher or admin might see all attendance records?"""
    # Or filter by class, etc.
    records = Attendance.objects.all().order_by('-date')
    return render(request, 'attendance_records.html', {'records': records})


@login_required
def student_attendance_records(request):
    """A student sees his/her own attendance."""
    if request.user.profile.role != 'Student':
        return redirect('home')
    records = Attendance.objects.filter(student=request.user).order_by('-date')
    total = records.count()
    absences = records.filter(status='A').count()
    absence_pct = (absences / total * 100) if total > 0 else 0
    warning = (absence_pct > 25)
    return render(request, 'attendance_records.html', {
        'records': records,
        'absence_percentage': absence_pct,
        'warning': warning
    })


@login_required
def edit_attendance(request, class_pk, student_pk):
    class_instance = get_object_or_404(Class, pk=class_pk)

    # Ensure the current user is the teacher of the class
    if request.user.profile.role != 'Teacher' or request.user != class_instance.teacher:
        return redirect('home')

    # Fetch the student user and their attendance records for this class
    student_user = get_object_or_404(User, pk=student_pk)
    attendance_qs = Attendance.objects.filter(student=student_user, classid=class_instance).order_by('date')

    # Create a modelformset for attendance editing
    AttendanceFormSet = modelformset_factory(
        Attendance,
        fields=['date', 'status', 'reason'],
        extra=0
    )

    if request.method == 'POST':
        formset = AttendanceFormSet(request.POST, queryset=attendance_qs)
        if formset.is_valid():
            formset.save()
            messages.success(request, f"Attendance for {student_user.username} updated.")
            return redirect('profile_detail', pk=student_user.profile.pk)
    else:
        formset = AttendanceFormSet(queryset=attendance_qs)

    return render(request, 'edit_attendance.html', {
        'class_instance': class_instance,
        'student_user': student_user,
        'formset': formset,
    })

@login_required
def profile_detail(request, user_id):
    user_profile = get_object_or_404(Profile, user_id=user_id)
    
    attendance_records = Attendance.objects.filter(student=user_profile.user).order_by('-date')
    
    total_classes = attendance_records.count()
    total_absences = attendance_records.filter(status='A').count()
    
    absence_percentage = (total_absences / total_classes * 100) if total_classes > 0 else 0

    class_instance = user_profile.user.enrolled_classes.first() if hasattr(user_profile.user, 'enrolled_classes') else None

    return render(request, 'profile_detail.html', {
        'profile': user_profile,
        'attendance_records': attendance_records,
        'total_classes': total_classes,
        'total_absences': total_absences,
        'absence_percentage': round(absence_percentage, 2),
        'class_instance': class_instance,
    })



@login_required
def search_classes(request):
    if request.method == 'POST':
        query = request.POST.get('query', '')
        # Filter classes by name
        found_classes = Class.objects.filter(name__icontains=query)
        return render(request, 'search_classes.html', {
            'classes': found_classes,
            'query': query
        })
    # If GET request or no query yet
    return render(request, 'search_classes.html')