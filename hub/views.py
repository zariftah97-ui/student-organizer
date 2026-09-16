import json
import os
from decimal import Decimal
from urllib import request as urlrequest
from urllib.error import HTTPError, URLError

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    RegisterForm, CourseForm, TopicForm, TaskForm, GradeForm,
    NoteForm, EventForm, FileForm, ProfileForm, SemesterForm,
)
from .models import Course, Topic, Task, GradeComponent, Note, Event, StudyFile, UserPreference, Semester, StudentProfile


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        UserPreference.objects.create(user=user)
        StudentProfile.objects.create(user=user)
        login(request, user)
        return redirect('dashboard')
    return render(request, 'registration/register.html', {'form': form})


def owned(model, request, pk):
    return get_object_or_404(model, pk=pk, user=request.user)


def crud(request, model, form_class, back, pk=None, title='Item'):
    obj = owned(model, request, pk) if pk else None
    form = form_class(request.POST or None, request.FILES or None, instance=obj)

    for key in ('course', 'note', 'semester'):
        if key in form.fields:
            form.fields[key].queryset = form.fields[key].queryset.filter(user=request.user)

    # Allows links such as /tasks/new/?course=12 to open with that course selected.
    if not obj and request.method == 'GET' and 'course' in form.fields:
        course_id = request.GET.get('course')
        if course_id and form.fields['course'].queryset.filter(pk=course_id).exists():
            form.fields['course'].initial = course_id

    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.user = request.user
        item.full_clean()
        item.save()
        messages.success(request, f'{title} saved.')
        return redirect(back)

    return render(request, 'form.html', {'form': form, 'object': obj, 'title': title})


def remove(request, model, pk, back):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    owned(model, request, pk).delete()
    messages.success(request, 'Item deleted.')
    return redirect(back)


def grade_point(percent):
    p = float(percent)
    return (
        4 if p >= 80 else 3.75 if p >= 75 else 3.5 if p >= 70 else
        3.25 if p >= 65 else 3 if p >= 60 else 2.75 if p >= 55 else
        2.5 if p >= 50 else 2.25 if p >= 45 else 2 if p >= 40 else 0
    )


def letter(percent):
    p = float(percent)
    return (
        'A+' if p >= 80 else 'A' if p >= 75 else 'A-' if p >= 70 else
        'B+' if p >= 65 else 'B' if p >= 60 else 'B-' if p >= 55 else
        'C+' if p >= 50 else 'C' if p >= 45 else 'D' if p >= 40 else 'F'
    )


def course_result(course):
    """Return percentage, letter, grade point using only scored components."""
    components = [c for c in course.components.all() if c.score is not None]
    maximum = sum((c.maximum for c in components), Decimal('0'))
    score = sum((c.score for c in components), Decimal('0'))
    if not maximum:
        return Decimal('0'), '—', None, score, maximum
    percent = (score / maximum) * Decimal('100')
    return percent, letter(percent), grade_point(percent), score, maximum


@login_required
def dashboard(request):
    courses = Course.objects.filter(user=request.user).select_related('semester').prefetch_related('components', 'topics')
    tasks = Task.objects.filter(user=request.user)
    total = sum(c.topics.count() for c in courses)
    done = sum(c.topics.filter(completed=True).count() for c in courses)

    weighted_points = Decimal('0')
    credits = Decimal('0')
    for course in courses:
        _, _, point, _, _ = course_result(course)
        if point is not None:
            weighted_points += Decimal(str(point)) * course.credit
            credits += course.credit
    cgpa = round(float(weighted_points / credits), 2) if credits else 0
    upcoming = Event.objects.filter(user=request.user, starts_at__gte=timezone.now()).select_related('course')[:5]
    priorities = tasks.filter(completed=False).order_by('due_date', '-created_at')[:4]

    return render(request, 'dashboard.html', {
        'courses': courses[:4],
        'course_count': courses.count(),
        'pending': tasks.filter(completed=False).count(),
        'completed': tasks.filter(completed=True).count(),
        'syllabus': round(done / total * 100) if total else 0,
        'cgpa': cgpa,
        'upcoming': upcoming,
        'priorities': priorities,
        'current_semester': Semester.objects.filter(user=request.user, is_current=True).first(),
    })


@login_required
def academic_setup(request):
    semesters = Semester.objects.filter(user=request.user)
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    return render(request, 'academic.html', {'semesters': semesters, 'profile': profile})


@login_required
def semester_form(request, pk=None):
    obj = owned(Semester, request, pk) if pk else None
    form = SemesterForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        semester = form.save(commit=False)
        semester.user = request.user
        semester.full_clean()
        if semester.is_current:
            Semester.objects.filter(user=request.user).exclude(pk=semester.pk).update(is_current=False)
        semester.save()
        messages.success(request, 'Semester saved.')
        return redirect('academic')
    return render(request, 'form.html', {'form': form, 'object': obj, 'title': 'Semester'})


@login_required
def semester_delete(request, pk):
    return remove(request, Semester, pk, 'academic')


@login_required
def set_current_semester(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    semester = owned(Semester, request, pk)
    Semester.objects.filter(user=request.user).update(is_current=False)
    semester.is_current = True
    semester.save(update_fields=['is_current'])
    messages.success(request, f'{semester.name} is now your current semester.')
    return redirect('academic')


@login_required
def courses(request):
    semesters = Semester.objects.filter(user=request.user)
    semester_id = request.GET.get('semester')
    data = Course.objects.filter(user=request.user).select_related('semester')
    if semester_id and semesters.filter(pk=semester_id).exists():
        data = data.filter(semester_id=semester_id)
    return render(request, 'courses.html', {'courses': data, 'semesters': semesters, 'selected_semester': semester_id})


@login_required
def course_form(request, pk=None):
    return crud(request, Course, CourseForm, 'courses', pk, 'Course')


@login_required
def course_detail(request, pk):
    course = owned(Course, request, pk)
    return render(request, 'course_detail.html', {
        'course': course,
        'topics': course.topics.all(),
        'tasks': course.tasks.all(),
        'notes': course.notes.all(),
        'events': course.events.filter(starts_at__gte=timezone.now())[:5],
    })


@login_required
def topics(request):
    return render(request, 'topics.html', {
        'topics': Topic.objects.filter(user=request.user).select_related('course')
    })


@login_required
def topic_form(request, pk=None):
    return crud(request, Topic, TopicForm, 'topics', pk, 'Syllabus topic')


@login_required
def toggle_topic(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    topic = owned(Topic, request, pk)
    topic.completed = not topic.completed
    topic.save(update_fields=['completed'])
    return JsonResponse({'completed': topic.completed, 'progress': topic.course.progress})


@login_required
def tasks(request):
    return render(request, 'tasks.html', {
        'tasks': Task.objects.filter(user=request.user).select_related('course')
    })


@login_required
def task_form(request, pk=None):
    return crud(request, Task, TaskForm, 'tasks', pk, 'Task')


@login_required
def toggle_task(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    task = owned(Task, request, pk)
    task.completed = not task.completed
    task.save(update_fields=['completed'])
    return JsonResponse({'completed': task.completed})


@login_required
def grades(request):
    rows = []
    courses = Course.objects.filter(user=request.user).select_related('semester').prefetch_related('components')
    semester_totals = {}
    for course in courses:
        percent, grade, point, score, maximum = course_result(course)
        rows.append((course, score, maximum, percent, grade, point))
        if point is not None and course.semester_id:
            item = semester_totals.setdefault(course.semester_id, {'semester': course.semester, 'points': Decimal('0'), 'credits': Decimal('0')})
            item['points'] += Decimal(str(point)) * course.credit
            item['credits'] += course.credit
    semester_rows = []
    for item in semester_totals.values():
        gpa = item['points'] / item['credits'] if item['credits'] else Decimal('0')
        semester_rows.append((item['semester'], round(float(gpa), 2), item['credits']))
    semester_rows.sort(key=lambda x: (not x[0].is_current, x[0].created_at), reverse=False)
    weighted = sum((Decimal(str(point)) * course.credit for course, _, _, _, _, point in rows if point is not None), Decimal('0'))
    credits = sum((course.credit for course, _, _, _, _, point in rows if point is not None), Decimal('0'))
    cgpa = round(float(weighted / credits), 2) if credits else 0
    return render(request, 'grades.html', {'rows': rows, 'semester_rows': semester_rows, 'cgpa': cgpa})


@login_required
def grade_form(request, pk=None):
    return crud(request, GradeComponent, GradeForm, 'grades', pk, 'Grade component')


@login_required
def notes(request):
    q = request.GET.get('q', '').strip()
    data = Note.objects.filter(user=request.user).select_related('course')
    if q:
        data = data.filter(Q(title__icontains=q) | Q(content__icontains=q))
    return render(request, 'notes.html', {'notes': data, 'q': q})


@login_required
def note_form(request, pk=None):
    return crud(request, Note, NoteForm, 'notes', pk, 'Note')


@login_required
def calendar(request):
    return render(request, 'calendar.html', {
        'events': Event.objects.filter(user=request.user).select_related('course')
    })


@login_required
def event_form(request, pk=None):
    return crud(request, Event, EventForm, 'calendar', pk, 'Event')


@login_required
def files(request):
    return render(request, 'files.html', {
        'files': StudyFile.objects.filter(user=request.user).select_related('course', 'note')
    })


@login_required
def file_form(request):
    return crud(request, StudyFile, FileForm, 'files', None, 'Upload file')


@login_required
def search(request):
    q = request.GET.get('q', '').strip()
    context = {'q': q}
    if q:
        context.update({
            'courses': Course.objects.filter(user=request.user).filter(
                Q(name__icontains=q) | Q(code__icontains=q)
            ),
            'topics': Topic.objects.filter(user=request.user).filter(
                Q(title__icontains=q) | Q(details__icontains=q)
            ).select_related('course'),
            'tasks': Task.objects.filter(user=request.user).filter(
                Q(title__icontains=q)
            ).select_related('course'),
            'notes': Note.objects.filter(user=request.user).filter(
                Q(title__icontains=q) | Q(content__icontains=q)
            ).select_related('course'),
            'events': Event.objects.filter(user=request.user).filter(
                Q(title__icontains=q) | Q(details__icontains=q)
            ).select_related('course'),
            'files': StudyFile.objects.filter(user=request.user).filter(
                file__icontains=q
            ).select_related('course'),
        })
    return render(request, 'search.html', context)


@login_required
def export_data(request):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    payload = {
        'profile': {
            'name': request.user.first_name,
            'email': request.user.email,
            'university': profile.university,
            'department': profile.department,
            'batch': profile.batch,
            'student_id': profile.student_id,
            'year': profile.year,
        },
        'semesters': [], 'courses': [], 'topics': [], 'tasks': [], 'grades': [], 'notes': [], 'events': [],
    }
    for x in Semester.objects.filter(user=request.user):
        payload['semesters'].append({'id': x.id, 'name': x.name, 'academic_year': x.academic_year, 'term': x.term, 'is_current': x.is_current})
    for x in Course.objects.filter(user=request.user):
        payload['courses'].append({'id': x.id, 'semester_id': x.semester_id, 'name': x.name, 'code': x.code, 'teacher': x.teacher, 'credit': str(x.credit), 'color': x.color})
    for x in Topic.objects.filter(user=request.user):
        payload['topics'].append({'course_id': x.course_id, 'title': x.title, 'details': x.details, 'completed': x.completed, 'position': x.position})
    for x in Task.objects.filter(user=request.user):
        payload['tasks'].append({'course_id': x.course_id, 'title': x.title, 'due_date': x.due_date.isoformat() if x.due_date else None, 'period': x.period, 'priority': x.priority, 'completed': x.completed})
    for x in GradeComponent.objects.filter(user=request.user):
        payload['grades'].append({'course_id': x.course_id, 'label': x.label, 'maximum': str(x.maximum), 'score': str(x.score) if x.score is not None else None})
    for x in Note.objects.filter(user=request.user):
        payload['notes'].append({'course_id': x.course_id, 'title': x.title, 'content': x.content, 'note_date': x.note_date.isoformat()})
    for x in Event.objects.filter(user=request.user):
        payload['events'].append({'course_id': x.course_id, 'title': x.title, 'starts_at': x.starts_at.isoformat(), 'event_type': x.event_type, 'details': x.details})
    response = JsonResponse(payload, json_dumps_params={'indent': 2})
    response['Content-Disposition'] = 'attachment; filename="studyos-data.json"'
    return response


@login_required
def assistant_page(request):
    return render(request, 'ai.html', {'configured': bool(os.getenv('OPENAI_API_KEY'))})


@login_required
def ai_query(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    key = os.getenv('OPENAI_API_KEY')
    if not key:
        return JsonResponse({'error': 'AI is not configured. Add OPENAI_API_KEY to the project .env file.'}, status=503)

    try:
        question = json.loads(request.body).get('question', '').strip()
    except (json.JSONDecodeError, AttributeError):
        question = ''

    if not question:
        return JsonResponse({'error': 'Please enter a question.'}, status=400)
    if len(question) > 4000:
        return JsonResponse({'error': 'Question is too long (maximum 4000 characters).'}, status=400)

    payload = json.dumps({
        'model': os.getenv('OPENAI_MODEL', 'gpt-4.1-mini'),
        'input': [
            {'role': 'system', 'content': 'You are StudyOS AI, a concise and supportive study assistant.'},
            {'role': 'user', 'content': question},
        ],
    }).encode()

    req = urlrequest.Request(
        'https://api.openai.com/v1/responses',
        data=payload,
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
    )
    try:
        with urlrequest.urlopen(req, timeout=30) as response:
            data = json.loads(response.read())
        answer = ''.join(
            item.get('text', '')
            for output in data.get('output', [])
            for item in output.get('content', [])
            if item.get('type') == 'output_text'
        )
        return JsonResponse({'answer': answer or 'No text response was returned.'})
    except (HTTPError, URLError, TimeoutError, ValueError):
        return JsonResponse({'error': 'StudyOS AI is temporarily unavailable. Please try again.'}, status=502)


@login_required
def settings_page(request):
    pref, _ = UserPreference.objects.get_or_create(user=request.user)
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, instance=request.user)

    if request.method == 'POST' and form.is_valid():
        form.save()
        profile.university = request.POST.get('university', '').strip()
        profile.department = request.POST.get('department', '').strip()
        profile.batch = request.POST.get('batch', '').strip()
        profile.student_id = request.POST.get('student_id', '').strip()
        year = request.POST.get('year', '').strip()
        profile.year = int(year) if year.isdigit() else None
        profile.save()
        pref.theme = request.POST.get('theme', 'light')
        pref.save(update_fields=['theme'])
        messages.success(request, 'Profile and settings saved.')
        return redirect('settings')

    return render(request, 'settings.html', {'form': form, 'pref': pref, 'profile': profile})
