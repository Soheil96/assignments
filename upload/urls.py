from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('students/add/<int:course_id>/', views.add_students, name='add_students'),
    path('cleanup/<str:checksum>/', views.cleanup, name='cleanup'),
    path('', views.index, name='index'),
    path('<int:course_id>/', views.course, name='course'),
    path('accounts/login/', views.login_page, name='login'),
    path('manager/', views.manager_index, name='manager_index'),
    path('manager/<int:course_id>/bystudent/', views.manager_by_student, name='manager_by_student'),
    path('manager/<int:course_id>/bystudent/<int:student_id>/', views.manager_student, name='manager_student'),
    path('manager/<int:course_id>/bystudent/<int:student_id>/download/<int:assignment_id>/', views.download, name='download'),
    path('manager/<int:course_id>/bystudent/<int:student_id>/score/<int:assignment_id>/', views.score_by_student, name='score_by_student'),
    path('manager/<int:course_id>/byassignment/', views.manager_by_assignment, name='manager_by_assignment'),
    path('manager/<int:course_id>/byassignment/<int:ca_id>/', views.manager_assignment, name='manager_assignment'),
    path('manager/<int:course_id>/byassignment/<int:ca_id>/score/<int:assignment_id>/', views.score_by_assignment, name='score_by_assignment'),
    path('manager/<int:course_id>/byassignment/<int:student_id>/download/<int:assignment_id>/', views.download, name='download'),
    path('manager/<int:course_id>/byassignment/add/', views.add_assignment, name='add_assignment'),
    path('manager/<int:course_id>/byassignment/<int:ca_id>/change/', views.change_assignment_status, name='change_assignment_status'),
    path('manager/<int:course_id>/byassignment/<int:ca_id>/delete/', views.delete_assignment, name='delete_assignment'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
