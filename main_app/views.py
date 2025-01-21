from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone
from django.forms import modelformset_factory
from datetime import timedelta, date
from .models import Profile, Class, Attendance, JoinRequest
from .forms import (
    UserRegistrationForm, ProfileForm, ClassForm,
    StudentSearchForm, AttendanceForm)
import logging

logger = logging.getLogger(__name__)

# Handles user sign-up and auto-login
def signup(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            user.email = user_form.cleaned_data['email']
            user.set_password(user_form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('edit_profile')
    else:
        user_form = UserRegistrationForm()
    return render(request, 'registration/signup.html', {'user_form': user_form})

# Custom login view to redirect users after login
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    def get_success_url(self):
        return reverse_lazy('home')

# Custom logout view to redirect users to home
class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')

# Displays the profile of the logged-in user
@login_required
def profile(request):
    return render(request, 'profile.html', {'user': request.user})

# Allows the user to edit their profile details
@login_required
def edit_profile(request):
    profile = get_object_or_404(Profile, user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated!")
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

    completion_percentage = profile.completion_percentage()
    return render(request, 'edit_profile.html', {
        'form': form,
        'completion_percentage': completion_percentage
    })

# Renders the home page
def home(request):
    return render(request, 'home.html')

# Allows a teacher to create a new class
@login_required
def create_class(request):
    if request.user.profile.role != 'Teacher':
        return redirect('home')

    if request.method == 'POST':
        form = ClassForm(request.POST)
        if form.is_valid():
            class_instance = form.save(commit=False)
            class_instance.teacher = request.user
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

    if request.user.profile.role == 'Student' and request.user not in students:
        messages.error(request, "You do not have access to this class.")
        return redirect('view_classes')

    if request.user.profile.role == 'Teacher' and request.user == class_instance.teacher:
        AttendanceFormSet = modelformset_factory(
            Attendance,
            fields=['student', 'status', 'reason'],
            extra=0
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
            attendance_qs = Attendance.objects.filter(classid=class_instance, date=today)
            if not attendance_qs.exists():
                initial_data = [{'student': student.pk} for student in students]
                print(f"Initial Data: {initial_data}")
                formset = AttendanceFormSet(
                    queryset=Attendance.objects.none(),
                    initial=initial_data
                )
                formset.extra = len(initial_data)
            else:
                formset = AttendanceFormSet(queryset=attendance_qs)

        zipped_data = list(zip(formset.forms, students))
        print(f"Zipped Data: {zipped_data}")

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

# Lists all classes managed by the teacher
@login_required
def manage_classes(request):
    if request.user.profile.role != 'Teacher':
        return redirect('home')
    classes = Class.objects.filter(teacher=request.user)
    return render(request, 'manage_classes.html', {'classes': classes})

# Allows a teacher to edit class details
@login_required
def edit_class(request, class_id):
    class_instance = get_object_or_404(Class, pk=class_id)
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

# Allows a teacher to delete a class
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

@login_required
def add_student(request, pk):
    class_instance = get_object_or_404(Class, pk=pk)

    if request.user.profile.role != 'Teacher' or request.user != class_instance.teacher:
        return redirect('home')

    query = request.POST.get('query', '') if request.method == 'POST' else ''
    found_students = User.objects.filter(
        username__icontains=query, 
        profile__role='Student'
    ) if query else None

    if request.method == 'POST' and 'username' in request.POST:
        username = request.POST.get('username')
        if username:
            try:
                student_user = User.objects.get(username=username)
                if student_user.profile.role == 'Student':
                    if student_user in class_instance.students.all():
                        messages.info(request, f"{username} is already enrolled in the class.")
                    else:
                        class_instance.students.add(student_user)
                        messages.success(request, f"Added {username} to the class.")
                    return redirect('class_detail', pk=pk)
                else:
                    messages.error(request, "This user is not a Student.")
            except User.DoesNotExist:
                messages.error(request, "User not found.")

    return render(request, 'add_student.html', {
        'class': class_instance,
        'found_students': found_students,
        'query': query,
    })

# Allows a teacher to remove a student from their class
@login_required
def remove_student(request, class_pk, student_pk):
    class_instance = get_object_or_404(Class, pk=class_pk)
    if request.user.profile.role != 'Teacher' or request.user != class_instance.teacher:
        return redirect('home')

    student_user = get_object_or_404(User, pk=student_pk)
    class_instance.students.remove(student_user)
    messages.info(request, f"Removed {student_user.username} from {class_instance.name}.")
    return redirect('class_detail', pk=class_pk)

# Lists all classes a student is enrolled in
@login_required
def view_classes(request):
    if request.user.profile.role == 'Student':
        enrolled = request.user.enrolled_classes.all()
        return render(request, 'view_classes.html', {'classes': enrolled})
    else:
        messages.error(request, "Unauthorized access.")
        return redirect('home')

# Allows a student to leave a class
@login_required
def leave_class(request, pk):
    class_instance = get_object_or_404(Class, pk=pk)
    if request.user.profile.role != 'Student':
        return redirect('home')
    class_instance.students.remove(request.user)
    messages.info(request, f"You left {class_instance.name}.")
    return redirect('view_classes')

# Allows a student to request to join a class
@login_required
def send_join_request(request, pk):
    class_instance = get_object_or_404(Class, pk=pk)
    if request.user.profile.role != 'Student':
        messages.error(request, "Only students can send join requests.")
        return redirect('home')

    # Check for existing requests
    existing_request = JoinRequest.objects.filter(student=request.user, classid=class_instance).first()

    if existing_request:
        if existing_request.status == 'Pending':
            messages.info(request, "You already have a pending join request.")
            return redirect('class_detail', pk=pk)
        elif existing_request.status in ['Approved', 'Rejected']:
            # Allow rejoin request by creating a new one
            existing_request.delete()

    # Create a new join request
    JoinRequest.objects.create(student=request.user, classid=class_instance, status='Pending')
    messages.success(request, "Join request sent.")
    return redirect('class_detail', pk=pk)

# Allows a teacher to manage join requests
@login_required
def manage_join_requests(request, pk):
    class_instance = get_object_or_404(Class, pk=pk)
    if request.user.profile.role != 'Teacher' or request.user != class_instance.teacher:
        messages.error(request, "Unauthorized access.")
        return redirect('home')

    join_requests = JoinRequest.objects.filter(classid=class_instance, status='Pending')
    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        action = request.POST.get('action')
        jr = get_object_or_404(JoinRequest, pk=req_id)
        if action == 'approve':
            jr.status = 'Approved'
            jr.save()
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

# Allows a teacher to mark attendance for a single student
@login_required
def mark_attendance_inline(request, class_pk, student_pk):
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

# Lists attendance records for a teacher or admin
@login_required
def attendance_records(request):
    records = Attendance.objects.all().order_by('-date')
    return render(request, 'attendance_records.html', {'records': records})

# Allows a student to view their own attendance records
@login_required
def student_attendance_records(request):
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

# Generates a range of dates between start_date and end_date
def generate_date_range(start_date, end_date):
    return [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

# Allows a teacher to edit attendance records for a student
@login_required
def edit_attendance(request, class_pk, student_pk):
    class_instance = get_object_or_404(Class, pk=class_pk)
    student = get_object_or_404(User, pk=student_pk)

    if request.method == 'POST':
        selected_date = request.POST.get('selected_date')
        status = request.POST.get('status')
        reason = request.POST.get('reason', '')

        if selected_date and status:
            try:
                Attendance.objects.update_or_create(
                    classid=class_instance,
                    student=student,
                    date=selected_date,
                    defaults={'status': status, 'reason': reason}
                )
            except Exception as e:
                print(f"Error saving attendance: {e}")
        return redirect('class_detail', pk=class_pk)

    today = date.today()
    start_date = class_instance.start_date
    end_date = min(class_instance.end_date, today)
    all_dates = generate_date_range(start_date, end_date)

    attendance_qs = Attendance.objects.filter(classid=class_instance, student=student).order_by('date')
    marked_dates = {record.date for record in attendance_qs}
    unmarked_dates = [d for d in all_dates if d not in marked_dates]

    context = {
        'class_instance': class_instance,
        'student_profile': student.profile,
        'unmarked_dates': unmarked_dates,
    }
    return render(request, 'edit_attendance.html', context)

# Displays detailed profile information for a user
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

# Searches for classes by keyword or shows all classes
@login_required
def search_classes(request):
    query = request.POST.get('query', '') if request.method == 'POST' else ''
    found_classes = Class.objects.filter(name__icontains=query) if query else Class.objects.all()
    return render(request, 'search_classes.html', {
        'classes': found_classes,
        'query': query
    })
