from django.contrib import admin
from .models import *
admin.site.register([Course,Topic,Task,GradeComponent,Note,Event,StudyFile,UserPreference])
