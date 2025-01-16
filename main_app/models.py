from django.contrib.auth.models import User
from django.db import models

STATUS_CHOICES = [
    ('P', 'Present'),
    ('A', 'Absent'),
    ('L', 'Late'),
]

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)
    profile_img = models.ImageField(upload_to='profile_images/', blank=True, default="")
    role = models.CharField(
        max_length=10,
        choices=[('Teacher', 'Teacher'), ('Student', 'Student')],
        default='Student'
    )

    def __str__(self):
        return self.user.username

class Class(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    students = models.ManyToManyField(Profile, related_name='classes')
    teacher = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='taught_classes')

    def __str__(self):
        return self.name
    
class Attendance(models.Model):
    student = models.ForeignKey(Profile, on_delete=models.CASCADE)
    classid = models.ForeignKey(Class, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)

    def __str__(self):
        return f"{self.student.user.username} - {self.classid.name} on {self.date} - {self.get_status_display()}"