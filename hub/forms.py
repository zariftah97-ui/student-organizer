from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Course, Topic, Task, GradeComponent, Note, Event, StudyFile, Semester, StudentProfile


class RegisterForm(UserCreationForm):
    name = forms.CharField(max_length=150, label='Full name')
    email = forms.EmailField(label='Email')

    class Meta:
        model = User
        fields = ('name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('username', None)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists. Please sign in instead.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.first_name = self.cleaned_data['name'].strip()
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('semester', 'name', 'code', 'teacher', 'credit', 'color')
        widgets = {'color': forms.TextInput(attrs={'type': 'color'})}


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ('course', 'title', 'details', 'completed')
        widgets = {'details': forms.Textarea(attrs={'rows': 5})}


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ('course', 'title', 'due_date', 'period', 'priority', 'completed')
        widgets = {'due_date': forms.DateInput(attrs={'type': 'date'})}


class GradeForm(forms.ModelForm):
    class Meta:
        model = GradeComponent
        fields = ('course', 'label', 'maximum', 'score')
        widgets = {
            'maximum': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'score': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ('course', 'title', 'content', 'note_date')
        widgets = {
            'note_date': forms.DateInput(attrs={'type': 'date'}),
            'content': forms.Textarea(attrs={'rows': 10}),
        }


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ('course', 'title', 'starts_at', 'event_type', 'details')
        widgets = {
            'starts_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'details': forms.Textarea(attrs={'rows': 4}),
        }


class FileForm(forms.ModelForm):
    class Meta:
        model = StudyFile
        fields = ('course', 'note', 'file')


class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = ('name', 'academic_year', 'term', 'start_date', 'end_date', 'is_current')
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class ProfileForm(forms.ModelForm):
    name = forms.CharField(max_length=150, label='Full name')

    class Meta:
        model = User
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].initial = self.instance.first_name

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(username__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('That email is already used by another account.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.first_name = self.cleaned_data['name'].strip()
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
