from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

ROLE_CHOICES = [
    ('Teacher', 'Teacher'),
    ('Student', 'Student'),
]

STATUS_CHOICES = [
    ('P', 'Present'),
    ('A', 'Absent'),
    ('L', 'Late'),
    ('E', 'Excused'),
]

# Profile model extending User with additional details
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Student')
    bio = models.TextField(blank=True)
    profile_img = models.ImageField(upload_to='profile_images/', blank=True, default='some_default.jpg')

    def __str__(self):
        return self.user.username
    
    # Calculate profile completion percentage
    def completion_percentage(self):
        fields = [self.bio, self.profile_img]
        filled = sum(1 for field in fields if field)
        total = len(fields)
        return int(filled / total * 100) if total else 0

# Automatically create or update Profile when a User is saved
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()

# Class model for courses with teacher and student associations
class Class(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='taught_classes')
    students = models.ManyToManyField(User, related_name='enrolled_classes', blank=True)

    def __str__(self):
        return self.name

# Attendance model to track student attendance in classes
class Attendance(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    classid = models.ForeignKey(Class, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)
    reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.username} - {self.classid.name} on {self.date} ({self.get_status_display()})"

# Model to handle join requests for classes
class JoinRequest(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    classid = models.ForeignKey(Class, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10,
        choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')],
        default='Pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} -> {self.classid.name} ({self.status})"
