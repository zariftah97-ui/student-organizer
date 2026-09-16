from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Owned(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class Semester(Owned):
    name = models.CharField(max_length=80)
    academic_year = models.CharField(max_length=20, blank=True)
    term = models.CharField(max_length=30, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_current', '-created_at', 'id']
        constraints = [
            models.UniqueConstraint(fields=['user', 'name'], name='unique_semester_name_per_user')
        ]

    def __str__(self):
        label = self.name
        if self.academic_year:
            label += f' · {self.academic_year}'
        return label


class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    university = models.CharField(max_length=180, blank=True)
    department = models.CharField(max_length=180, blank=True)
    batch = models.CharField(max_length=50, blank=True)
    student_id = models.CharField(max_length=60, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(10)])
    avatar = models.FileField(upload_to='avatars/', blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class Course(Owned):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=30, blank=True)
    semester = models.ForeignKey(Semester, null=True, blank=True, on_delete=models.SET_NULL, related_name='courses')
    credit = models.DecimalField(max_digits=4, decimal_places=1, default=3,
                                 validators=[MinValueValidator(0.5)])
    teacher = models.CharField(max_length=160, blank=True)
    color = models.CharField(max_length=7, default='#6f9d70')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name', 'id']

    def __str__(self):
        return self.name

    @property
    def progress(self):
        total = self.topics.count()
        if not total:
            return 0
        return round(self.topics.filter(completed=True).count() / total * 100)


class Topic(Owned):
    course = models.ForeignKey(Course, related_name='topics', on_delete=models.CASCADE)
    title = models.CharField(max_length=180)
    details = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['position', 'id']


class Task(Owned):
    PERIODS = [('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')]
    PRIORITIES = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]

    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.SET_NULL, related_name='tasks')
    title = models.CharField(max_length=180)
    due_date = models.DateField(null=True, blank=True)
    period = models.CharField(max_length=10, choices=PERIODS, default='weekly')
    priority = models.CharField(max_length=10, choices=PRIORITIES, default='medium')
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['completed', 'due_date', '-created_at']


class GradeComponent(Owned):
    course = models.ForeignKey(Course, related_name='components', on_delete=models.CASCADE)
    label = models.CharField(max_length=80)
    maximum = models.DecimalField(max_digits=6, decimal_places=2,
                                  validators=[MinValueValidator(0.01)])
    score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                validators=[MinValueValidator(0)])

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['course', 'label'], name='unique_grade_component_per_course')
        ]

    def clean(self):
        if self.score is not None and self.score > self.maximum:
            raise ValidationError({'score': 'Score cannot exceed maximum.'})


class Note(Owned):
    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.SET_NULL, related_name='notes')
    title = models.CharField(max_length=180)
    content = models.TextField()
    note_date = models.DateField(default=timezone.localdate)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-id']


class Event(Owned):
    TYPES = [
        ('exam', 'Exam'), ('assignment', 'Assignment'), ('presentation', 'Presentation'),
        ('study', 'Study session'), ('personal', 'Personal')
    ]

    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.SET_NULL, related_name='events')
    title = models.CharField(max_length=180)
    starts_at = models.DateTimeField()
    event_type = models.CharField(max_length=15, choices=TYPES, default='study')
    details = models.TextField(blank=True)

    class Meta:
        ordering = ['starts_at']


def validate_upload_size(value):
    max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 15 * 1024 * 1024)
    if value.size > max_size:
        raise ValidationError('File is too large. Maximum size is 15 MB.')


class StudyFile(Owned):
    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.SET_NULL, related_name='files')
    note = models.ForeignKey(Note, null=True, blank=True, on_delete=models.SET_NULL, related_name='files')
    file = models.FileField(upload_to='study_files/%Y/%m/', validators=[validate_upload_size])
    uploaded_at = models.DateTimeField(auto_now_add=True)

    @property
    def filename(self):
        return self.file.name.rsplit('/', 1)[-1]


class UserPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='preference')
    theme = models.CharField(max_length=10, choices=[('light','Sage Garden'),('dark','Deep Garden')], default='light')
