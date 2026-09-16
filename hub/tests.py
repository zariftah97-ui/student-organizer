from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Course, Task, Event, Semester, GradeComponent
from .views import grade_point

class StudyOSTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('student@example.com','student@example.com','StrongPass123!')
        self.other=User.objects.create_user('other@example.com','other@example.com','StrongPass123!')
    def test_protected_dashboard(self):
        self.assertRedirects(self.client.get(reverse('dashboard')), '/login/?next=/')
    def test_course_is_owned(self):
        course=Course.objects.create(user=self.user,name='Algorithms',credit=3)
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(reverse('course_detail',args=[course.id])).status_code,404)
    def test_task_creation_and_toggle(self):
        self.client.force_login(self.user); course=Course.objects.create(user=self.user,name='Math',credit=3)
        self.client.post(reverse('task_new'),{'course':course.id,'title':'Revise','period':'daily','priority':'high'})
        task=Task.objects.get(); self.client.post(reverse('task_toggle',args=[task.id])); task.refresh_from_db()
        self.assertTrue(task.completed)
    def test_grade_point(self):
        self.assertEqual(grade_point(81),4); self.assertEqual(grade_point(39),0)
    def test_event_is_created(self):
        self.client.force_login(self.user)
        self.client.post(reverse('event_new'),{'title':'Exam','starts_at':'2026-12-01T10:00','event_type':'exam'})
        self.assertEqual(Event.objects.filter(user=self.user).count(),1)

    def test_semester_current_is_unique_per_user(self):
        self.client.force_login(self.user)
        s1=Semester.objects.create(user=self.user,name='Spring')
        s2=Semester.objects.create(user=self.user,name='Fall',is_current=True)
        self.client.post(reverse('semester_edit',args=[s1.id]), {'name':'Spring','academic_year':'2026','term':'Spring','start_date':'2026-01-01','end_date':'2026-05-01','is_current':'on'})
        s2.refresh_from_db()
        self.assertFalse(s2.is_current)

    def test_grade_score_cannot_exceed_maximum(self):
        course=Course.objects.create(user=self.user,name='Math',credit=3)
        self.client.force_login(self.user)
        response=self.client.post(reverse('grade_new'), {'course':course.id,'label':'Quiz','maximum':'10','score':'12'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(GradeComponent.objects.count(), 0)

    def test_export_requires_login(self):
        self.assertEqual(self.client.get(reverse('export_data')).status_code, 302)
