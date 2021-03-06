from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('students/add/<int:course_id>/', views.add_students, name='add_students'),
    path('data/cleanup/<str:checksum>/', views.cleanup, name='cleanup'),
    path('data/download/<str:checksum>/', views.download_data, name='download_data'),
    path('data/update/<str:checksum>/', views.update, name='update'),
    path('', views.index, name='index'),
    path('<int:course_id>/', views.course, name='course'),
    path('accounts/login/', views.login_page, name='login'),
    path('manager/', views.manager_index, name='manager_index'),
    path('manager/<int:course_id>/scores/', views.manager_scores, name='manager_scores'),
    path('manager/<int:course_id>/scores/excel/', views.course_scores_excel, name='course_scores_excel'),
    path('manager/<int:course_id>/bystudent/', views.manager_by_student, name='manager_by_student'),
    path('manager/<int:course_id>/bystudent/add/', views.add_student, name='add_student'),
    path('manager/<int:course_id>/bystudent/grouping/', views.grouping, name='grouping'),
    path('manager/<int:course_id>/bystudent/<int:student_id>/', views.manager_student, name='manager_student'),
    path('manager/<int:course_id>/bystudent/<int:student_id>/download/<int:assignment_id>/<str:checksum>/', views.download, name='download'),
    path('manager/<int:course_id>/bystudent/<int:student_id>/score/<int:assignment_id>/', views.score_by_student, name='score_by_student'),
    path('manager/<int:course_id>/byassignment/', views.manager_by_assignment, name='manager_by_assignment'),
    path('manager/<int:course_id>/byassignment/<int:ca_id>/', views.manager_assignment, name='manager_assignment'),
    path('manager/<int:course_id>/byassignment/<int:ca_id>/extend/', views.extend_assignment, name='extend_assignment'),
    path('manager/<int:course_id>/byassignment/<int:ca_id>/score/assignment/', views.assignment_score, name='assignment_score'),
    path('manager/<int:course_id>/byassignment/<int:ca_id>/score/all/', views.assignment_all_scores, name='assignment_all_scores'),
    path('manager/<int:course_id>/byassignment/<int:ca_id>/score/<int:assignment_id>/', views.score_by_assignment, name='score_by_assignment'),
    path('manager/<int:course_id>/byassignment/<int:student_id>/download/<int:assignment_id>/<str:checksum>/', views.download, name='download'),
    path('manager/<int:course_id>/byassignment/add/', views.add_assignment, name='add_assignment'),
    path('manager/<int:course_id>/byassignment/<int:ca_id>/delete/', views.delete_assignment, name='delete_assignment'),
    path('manager/poll/', views.manager_polls, name='manager_polls'),
    path('manager/poll/add/', views.manager_add_poll, name='manager_add_poll'),
    path('manager/poll/<int:poll_id>/', views.manager_poll, name='manager_poll'),
    path('manager/poll/<int:poll_id>/delete/', views.manager_poll_delete, name='manager_poll_delete'),
    path('manager/poll/<int:poll_id>/add/', views.manager_poll_add_option, name='manager_poll_add_option'),
    path('manager/poll/<int:poll_id>/state/', views.manager_poll_change_state, name='manager_poll_change_state'),
    path('poll/<int:poll_id>/', views.vote_poll, name='vote_poll'),
] #+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
