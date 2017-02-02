from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Problem)
admin.site.register(ProblemRevision)
admin.site.register(ProblemData)
admin.site.register(Discussion)
admin.site.register(Solution)
admin.site.register(SolutionRun)
admin.site.register(Grader)
# admin.site.register(SourceFile)
admin.site.register(ProblemFork)
admin.site.register(TestCase)
