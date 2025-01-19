from django.urls import path
from . import views

urlpatterns = [
    # Home page.
    path('', views.home, name='home'),
    
    # User authentication routes.
    path('signup/', views.signup, name='signup'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    
    # User profile routes.
    path('profile/', views.profile, name='profile'),
    path('profile/<int:pk>/', views.profile_detail, name='profile_detail'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Class management routes.
    path('class/create/', views.create_class, name='create_class'),
    path('class/<int:pk>/', views.class_detail, name='class_detail'),
    path('classes/manage/', views.manage_classes, name='manage_classes'),
    path('class/<int:pk>/add_student/', views.add_student, name='add_student'),
    path('classes/search/', views.search_classes, name='search_classes'),
    path('class/<int:pk>/join/', views.send_join_request, name='send_join_request'),
    path('classes/', views.view_classes, name='view_classes'),
    path('class/<int:pk>/leave/', views.leave_class, name='leave_class'),
    path('class/<int:class_pk>/remove_student/<int:student_pk>/', views.remove_student, name='remove_student'),
    path('class/<int:class_id>/delete/', views.delete_class, name='delete_class'),
    
    # Attendance management routes.
    path('class/<int:class_pk>/mark_attendance/<int:student_pk>/', views.mark_attendance_inline, name='mark_attendance_inline'),
    path('class/<int:class_id>/attendance_records/', views.attendance_records, name='attendance_records'),
    path('class/<int:class_id>/edit/', views.edit_class, name='edit_class'),
    path('attendance/', views.student_attendance_records, name='student_attendance_records'),
]
