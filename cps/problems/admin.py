from django.contrib import admin
from .models import Problem, ProblemRevision, ProblemData, Discussion

# Register your models here.
admin.site.register(Problem)
admin.site.register(ProblemRevision)
admin.site.register(ProblemData)
admin.site.register(Discussion)