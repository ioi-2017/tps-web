from django.views.generic import View
from .decorators import authenticate_problem_access
from problems.views.utils import render_for_problem

__all__ = ["FilesListView"]

class FilesListView(View):
    pass