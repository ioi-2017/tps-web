from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Problem)
admin.site.register(ProblemRevision)
admin.site.register(ProblemData)
admin.site.register(Discussion)
#admin.site.register(Solution)
admin.site.register(SolutionRun)
#admin.site.register(Grader)
admin.site.register(ProblemBranch)
admin.site.register(TestCase)


@admin.register(ProblemRole)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name']


# FIXME: Temporal action for granting access to all.
# Should be removed when access UI is implemented
def grant_default_access_to_all(modeladmin, request, queryset):
    from accounts.models import User
    for user in User.objects.all():
        for problem in Problem.objects.all():
            ProblemUserRole.objects.get_or_create(
                user=user,
                problem=problem,
                defaults={'role': ProblemRole.objects.all().first()}
            )


@admin.register(ProblemUserRole)
class ProblemUserRoleAdmin(admin.ModelAdmin):
    actions = [grant_default_access_to_all]
