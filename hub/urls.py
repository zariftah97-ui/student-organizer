from django.contrib.auth import views as auth
from django.urls import path

from . import views
from .models import Course, Topic, Task, GradeComponent, Note, Event, StudyFile

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', auth.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth.LogoutView.as_view(), name='logout'),

    path('academic/', views.academic_setup, name='academic'),
    path('academic/semesters/new/', views.semester_form, name='semester_new'),
    path('academic/semesters/<int:pk>/edit/', views.semester_form, name='semester_edit'),
    path('academic/semesters/<int:pk>/delete/', views.semester_delete, name='semester_delete'),
    path('academic/semesters/<int:pk>/current/', views.set_current_semester, name='semester_current'),

    path('courses/', views.courses, name='courses'),
    path('courses/new/', views.course_form, name='course_new'),
    path('courses/<int:pk>/', views.course_detail, name='course_detail'),
    path('courses/<int:pk>/edit/', views.course_form, name='course_edit'),
    path('courses/<int:pk>/delete/', lambda request, pk: views.remove(request, Course, pk, 'courses'), name='course_delete'),

    path('syllabus/', views.topics, name='topics'),
    path('syllabus/new/', views.topic_form, name='topic_new'),
    path('syllabus/<int:pk>/edit/', views.topic_form, name='topic_edit'),
    path('syllabus/<int:pk>/toggle/', views.toggle_topic, name='topic_toggle'),
    path('syllabus/<int:pk>/delete/', lambda request, pk: views.remove(request, Topic, pk, 'topics'), name='topic_delete'),

    path('tasks/', views.tasks, name='tasks'),
    path('tasks/new/', views.task_form, name='task_new'),
    path('tasks/<int:pk>/edit/', views.task_form, name='task_edit'),
    path('tasks/<int:pk>/toggle/', views.toggle_task, name='task_toggle'),
    path('tasks/<int:pk>/delete/', lambda request, pk: views.remove(request, Task, pk, 'tasks'), name='task_delete'),

    path('grades/', views.grades, name='grades'),
    path('grades/new/', views.grade_form, name='grade_new'),
    path('grades/<int:pk>/edit/', views.grade_form, name='grade_edit'),
    path('grades/<int:pk>/delete/', lambda request, pk: views.remove(request, GradeComponent, pk, 'grades'), name='grade_delete'),

    path('notes/', views.notes, name='notes'),
    path('notes/new/', views.note_form, name='note_new'),
    path('notes/<int:pk>/edit/', views.note_form, name='note_edit'),
    path('notes/<int:pk>/delete/', lambda request, pk: views.remove(request, Note, pk, 'notes'), name='note_delete'),

    path('calendar/', views.calendar, name='calendar'),
    path('calendar/new/', views.event_form, name='event_new'),
    path('calendar/<int:pk>/edit/', views.event_form, name='event_edit'),
    path('calendar/<int:pk>/delete/', lambda request, pk: views.remove(request, Event, pk, 'calendar'), name='event_delete'),

    path('files/', views.files, name='files'),
    path('files/new/', views.file_form, name='file_new'),
    path('files/<int:pk>/delete/', lambda request, pk: views.remove(request, StudyFile, pk, 'files'), name='file_delete'),

    path('search/', views.search, name='search'),
    path('ai/', views.assistant_page, name='ai'),
    path('api/ai/', views.ai_query, name='ai_query'),
    path('settings/', views.settings_page, name='settings'),
    path('settings/export/', views.export_data, name='export_data'),
]
